from itertools import filterfalse

import pandas as pd
import numpy as np
from numpy.polynomial import Polynomial


def fit_hipf(reference_sample, controls_individuals, controls_households, maxiter):
    """Hierarchical Iterative Proportional Fitting.

    Algorithm taken from
    Müller and Axhausen 2011: "Hierarchical IPF: Generating a synthetic population for Switzerland"

    Can be used to fit a reference sample of households and individuals to control variables
    simultaneously. The algorithm supports only one dimensional control variables, and hence
    multi-dimensional control variables must be transformed to one dimensional ones first.

    Parameters:
        reference_sample:     The reference sample to be fited to the controls. Must be a pandas
                              DataFrame where the index is a multi index of (household_id,
                              person_id), and each colum represents either a household category
                              or a category of an individual.
        controls_individuals: The control variables for individuals. Must be a dict from control
                              name to a dict of its values.
                              e.g. {'age': {'below_50': 45, '50_or_older'}: 55}
        controls_households:  The control variables for households. Must be in the same format as
                              the controls for individuals.
        maxiter:              Maximum number of iterations.
    """

    weights = pd.Series(
        index=_household_groups(reference_sample).count().index.get_level_values(0),
        data=1.0,
        dtype=np.float64
    )
    for i in range(0, maxiter):
        next_weights = _fit_households(reference_sample, weights, controls_households)
        weights_person = _expand_weights_to_person(next_weights, reference_sample.index)
        weights_person = _fit_person(reference_sample, weights_person, controls_individuals)
        next_weights = _aggregate_person_weights_to_household(weights_person)
        next_weights = _rescale_weights(reference_sample, next_weights)
        weights = next_weights
    return weights


def _household_groups(reference_sample):
    return reference_sample.groupby(reference_sample.index.get_level_values(0))


def _fit_households(reference_sample, weights, controls_households):
    new_weights = weights.copy()
    for control_name, control_values in controls_households.items():
        for household_id in new_weights.index:
            hh_value = reference_sample.loc[(household_id, 1), control_name]
            mask = _household_groups(reference_sample)[control_name].first() == hh_value
            new_weights[household_id] = (weights.loc[household_id] *
                                         control_values[hh_value] / weights[mask].sum())
    return new_weights


def _fit_person(reference_sample, weights, controls_individuals):
    new_weights = weights.copy()
    for control_name, control_values in controls_individuals.items():
        for person_id in weights.index:
            value = reference_sample.loc[person_id, control_name]
            mask = reference_sample[control_name] == value
            new_weights.loc[person_id] = (weights.loc[person_id] *
                                          control_values[value] / weights[mask].sum())
    return new_weights


def _aggregate_person_weights_to_household(person_weights):
    return person_weights.groupby(person_weights.index.get_level_values(0)).mean()


def _expand_weights_to_person(weights, person_index):
    person_weights = weights.copy()
    person_weights = pd.DataFrame(person_weights)
    person_weights['person_id'] = 1
    person_weights.set_index('person_id', append=True, inplace=True)
    person_weights = person_weights.reindex(person_index)
    person_weights.fillna(method='ffill', inplace=True)
    return person_weights.iloc[:, 0] # return series not dataframe


def _rescale_weights(reference_sample, weights):
    household_sizes = _household_groups(reference_sample)[reference_sample.columns[0]].count()
    largest_household_size = household_sizes.max()
    Fp = [weights[household_sizes == p].sum()
          for p in range(0, largest_household_size + 1)]
    polynom = [(190 / 434 * p - 1) * Fp[p] for p in range(0, largest_household_size + 1)]
    roots = Polynomial(polynom).roots()
    dx = list(filter(lambda x: np.real(x) > 0, filterfalse(lambda x: np.iscomplex(x), roots)))
    assert len(dx) == 1
    d = np.real(dx[0])
    c = 190 / sum([Fp[p] * d ** p for p in range(1, largest_household_size + 1)])
    fhprime_by_fh = {p: c * d ** p for p in range(1, largest_household_size + 1)}

    new_weights = weights.copy()
    for household_id in weights.index:
        household_size = household_sizes[household_id]
        new_weights[household_id] = fhprime_by_fh[household_size] * weights[household_id]
    return new_weights
