from itertools import filterfalse, chain

import pandas as pd
import numpy as np
from numpy.polynomial import Polynomial


def fit_hipf(reference_sample, controls_individuals, controls_households, maxiter,
             weights_tol=None, residuals_tol=None):
    """Hierarchical Iterative Proportional Fitting.

    Algorithm taken from
    Müller and Axhausen 2011: "Hierarchical IPF: Generating a synthetic population for Switzerland"

    Can be used to fit a reference sample of households and individuals to control variables
    simultaneously. The algorithm supports only one dimensional control variables, and hence
    multi-dimensional control variables must be transformed to one dimensional ones first.

    By default the algorithm runs exactly `maxiter` iterations. Convergence can be checked on
    residuals and changes in the weights by giving the corresponding tolerances.

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
        weights_tol:          Convergence tolerance on the weights. Whenever the weights change
                              between two iterations is smaller than the given tolerance, stop.
                              (optional)
        residuals_tol:        Convergence tolerance on the residuals (difference to control
                              totals). Whenever the residuals are smaller than the given tolerance,
                              stop. (optional)
        maxiter:              Maximum number of iterations.
    """

    weights = pd.Series(
        index=_household_groups(reference_sample).count().index.get_level_values(0),
        data=1.0,
        dtype=np.float64
    )
    for i in range(1, maxiter + 1):
        next_weights = _fit(_household_groups(reference_sample).first(), weights,
                            controls_households)
        weights_person = _expand_weights_to_person(next_weights, reference_sample.index)
        weights_person = _fit(reference_sample, weights_person, controls_individuals)
        next_weights = _aggregate_person_weights_to_household(weights_person)
        next_weights = _rescale_weights(reference_sample, next_weights,
                                        controls_individuals, controls_households)
        previous_weights = weights.copy()
        weights = next_weights.copy()
        if (residuals_tol is not None and
            _residuals_tolerance_reached(reference_sample, weights, controls_households,
                                         controls_individuals, residuals_tol)):
            print('Residuals tolerance reached in iteration {}.'.format(i))
            break
        if (weights_tol is not None and
                _weights_tolerance_reached(next_weights, previous_weights, weights_tol)):
            print("Weights haven't changed anymore in iteration {}.".format(i))
            break
    return weights


def _household_groups(reference_sample):
    return reference_sample.groupby(reference_sample.index.get_level_values(0))


def _residuals_tolerance_reached(reference_sample, weights, controls_households,
                                 controls_individuals, tol):
    residuals = _all_residuals(reference_sample, weights, controls_households, controls_individuals)
    return residuals.abs().max() < tol


def _all_residuals(reference_sample, weights, controls_households, controls_individuals):
    household_ref_sample = _household_groups(reference_sample).first()
    residuals_household = _residuals(
        reference_sample=_household_groups(reference_sample).first(),
        weights=weights,
        controls=controls_households
    )
    residuals_individual = _residuals(
        reference_sample=reference_sample,
        weights=_expand_weights_to_person(weights, reference_sample.index),
        controls=controls_individuals
    )
    return pd.Series(list(chain(residuals_household, residuals_individual)))


def _residuals(reference_sample, weights, controls):
    residuals = []
    residuals.append(weights.sum() / _grand_total(controls) - 1)
    for control_name, control_values in controls.items():
        actual_values = {key: weights[reference_sample[control_name] == key].sum()
                         for key, value in control_values.items()}
        for key in control_values.keys():
            residuals.append(actual_values[key] / control_values[key] - 1)
    return residuals


def _weights_tolerance_reached(weights, previous_weights, tol):
    return (weights / previous_weights - 1).abs().max() < tol


def _grand_total(controls):
    grand_totals = [sum([value for key, value in category.items()])
                    for category in controls.values()]
    return grand_totals[0]


def _fit(reference_sample, weights, controls):
    new_weights = weights.copy()
    for control_name, control_values in controls.items():
        summed_weights = {key: new_weights[reference_sample[control_name] == key].sum()
                          for key, value in control_values.items()}
        control_values = reference_sample[control_name].map(control_values)
        summed_weights = reference_sample[control_name].map(summed_weights)
        new_weights = new_weights * control_values / summed_weights
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


def _rescale_weights(reference_sample, weights, controls_individuals, controls_households):
    grand_total_hh = _grand_total(controls_households)
    grand_total_ind = _grand_total(controls_individuals)
    household_sizes = _household_groups(reference_sample)[reference_sample.columns[0]].count()
    largest_household_size = household_sizes.max()
    Fp = [weights[household_sizes == p].sum()
          for p in range(0, largest_household_size + 1)]
    polynom = [(grand_total_hh / grand_total_ind * p - 1) * Fp[p]
               for p in range(0, largest_household_size + 1)]
    roots = Polynomial(polynom).roots()
    dx = list(filter(lambda x: np.real(x) > 0, filterfalse(lambda x: np.iscomplex(x), roots)))
    assert len(dx) == 1
    d = np.real(dx[0])
    c = grand_total_hh / sum(Fp[p] * d ** p for p in range(1, largest_household_size + 1))
    fhprime_by_fh = {p: c * d ** p for p in range(1, largest_household_size + 1)}

    fhprime_by_fh = household_sizes.map(fhprime_by_fh)
    new_weights = fhprime_by_fh * weights
    return new_weights
