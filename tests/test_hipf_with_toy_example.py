"""Testing the HIPF algorithm with the toy example from its original paper.

The paper defining the algorithm and the toy example is:
Müller and Axhausen 2011: "Hierarchical IPF: Generating a synthetic population for Switzerland"

"""
import sys
import itertools
from collections import namedtuple

import pandas as pd
import numpy as np
from pandas.util.testing import assert_series_equal
import pytest

sys.path.append('.')
from ktp.synthpop import fit_hipf


HouseholdType = namedtuple('HouseholdType', ['household_ids', 'a', 'alpha', 'weights'])


@pytest.fixture
def household_types():
    household_types = []
    household_types.append(HouseholdType(
        household_ids=range(1, 23),
        a=True,
        alpha=[True, False, False],
        weights=[1.33, 1.28, 1.18]
    ))
    household_types.append(HouseholdType(
        household_ids=range(23, 44),
        a=True,
        alpha=[True, False],
        weights=[1.61, 1.61, 1.50]
    ))
    household_types.append(HouseholdType(
        household_ids=range(44, 65),
        a=True,
        alpha=[False, False, False],
        weights=[0.92, 0.75, 0.54]
    ))
    household_types.append(HouseholdType(
        household_ids=range(65, 81),
        a=False,
        alpha=[False, False],
        weights=[0.45, 0.38, 0.28]
    ))
    household_types.append(HouseholdType(
        household_ids=range(81, 97),
        a=False,
        alpha=[True, False, False],
        weights=[0.62, 0.66, 0.68]
    ))
    household_types.append(HouseholdType(
        household_ids=range(97, 109),
        a=False,
        alpha=[False],
        weights=[0.48, 0.38, 0.26]
    ))
    household_types.append(HouseholdType(
        household_ids=range(109, 120),
        a=True,
        alpha=[False, False],
        weights=[0.97, 0.75, 0.49]
    ))
    household_types.append(HouseholdType(
        household_ids=range(120, 129),
        a=True,
        alpha=[False],
        weights=[1.01, 0.75, 0.45]
    ))
    household_types.append(HouseholdType(
        household_ids=range(129, 137),
        a=False,
        alpha=[True, True, False],
        weights=[0.82, 1.00, 1.30]
    ))
    household_types.append(HouseholdType(
        household_ids=range(137, 145),
        a=True,
        alpha=[True, True, False],
        weights=[1.73, 1.95, 2.24]
    ))
    household_types.append(HouseholdType(
        household_ids=range(145, 152),
        a=False,
        alpha=[True, False],
        weights=[0.75, 0.82, 0.87]
    ))
    household_types.append(HouseholdType(
        household_ids=range(152, 159),
        a=False,
        alpha=[False, False, False],
        weights=[0.43, 0.38, 0.31]
    ))
    household_types.append(HouseholdType(
        household_ids=range(159, 165),
        a=True,
        alpha=[True],
        weights=[2.35, 2.76, 3.27]
    ))
    household_types.append(HouseholdType(
        household_ids=range(165, 171),
        a=True,
        alpha=[True, True],
        weights=[2.25, 2.75, 3.58]
    ))
    household_types.append(HouseholdType(
        household_ids=range(171, 174),
        a=False,
        alpha=[True],
        weights=[1.11, 1.41, 1.89]
    ))
    household_types.append(HouseholdType(
        household_ids=range(174, 176),
        a=True,
        alpha=[True, True, True],
        weights=[2.14, 2.74, 3.92]
    ))
    household_types.append(HouseholdType(
        household_ids=range(176, 177),
        a=False,
        alpha=[True, True],
        weights=[1.06, 1.40, 2.07]
    ))
    return household_types


@pytest.fixture
def reference_sample(household_types):
    id_tuples = itertools.chain(*(itertools.product(ht.household_ids, range(1, len(ht.alpha) + 1))
                                  for ht in household_types))
    index = pd.MultiIndex.from_tuples(list(id_tuples), names=['household_id', 'person_id'])
    ref_sample = pd.DataFrame(index=index, columns=['a', 'alpha'])
    for ht in household_types:
        ref_sample.ix[ht.household_ids[0]: ht.household_ids[-1], 'a'] = ht.a
        for p, alpha in enumerate(ht.alpha):
            ref_sample.loc[
                (slice(ht.household_ids[0], ht.household_ids[-1]), p + 1),
                'alpha'
            ] = alpha
    return ref_sample


@pytest.fixture
def expected_weights(household_types, reference_sample):
    expected_weights = pd.DataFrame(
        index=reference_sample.groupby(reference_sample.index.get_level_values(0))
                              .count().index.get_level_values(0),
        columns=[0, 5, 10, 'infinity'],
        dtype=np.float64
    )
    expected_weights[0] = 1.
    for ht in household_types:
        for household_id in ht.household_ids:
            expected_weights.ix[household_id, 5] = ht.weights[0]
            expected_weights.ix[household_id, 10] = ht.weights[1]
            expected_weights.ix[household_id, 'infinity'] = ht.weights[2]
    return expected_weights


def assert_weights_equal(expected_weights, weights, precision=1):
    weights.name = expected_weights.name # don't want to check the name
    assert_series_equal(expected_weights, weights, check_less_precise=precision)


def test_first_iteration(reference_sample, expected_weights):
    weights = fit_hipf(
        reference_sample=reference_sample,
        controls_individuals={'alpha': {True: 227, False: 207}},
        controls_households={'a': {True: 145, False: 45}},
        maxiter=1
    )
    assert_weights_equal(expected_weights[5], weights) # 5 iterations in paper represent 1 iteration


def test_second_iteration(reference_sample, expected_weights):
    weights = fit_hipf(
        reference_sample=reference_sample,
        controls_individuals={'alpha': {True: 227, False: 207}},
        controls_households={'a': {True: 145, False: 45}},
        maxiter=2
    )
    assert_weights_equal(expected_weights[10], weights) # 5 iteration in paper represent 1 iteration


def test_convergence(reference_sample, expected_weights):
    weights = fit_hipf(
        reference_sample=reference_sample,
        controls_individuals={'alpha': {True: 227, False: 207}},
        controls_households={'a': {True: 145, False: 45}},
        maxiter=10
    )
    assert_weights_equal(expected_weights['infinity'], weights)


@pytest.mark.parametrize("tol", [(10), (1), (0.1)]) # assertion below uses tolerance 0.01
def test_residuals_tolerance_criteria_stops_early(reference_sample, expected_weights, tol):
    weights = fit_hipf(
        reference_sample=reference_sample,
        controls_individuals={'alpha': {True: 227, False: 207}},
        controls_households={'a': {True: 145, False: 45}},
        residuals_tol=tol,
        weights_tol=1e-16,
        maxiter=10
    )
    with pytest.raises(AssertionError):
        assert_weights_equal(expected_weights['infinity'], weights)


@pytest.mark.parametrize("tol", [(0.01), (0.001)]) # assertion below uses tolerance 0.01
def test_residuals_tolerance_criteria_does_not_stop_early(reference_sample, expected_weights, tol):
    weights = fit_hipf(
        reference_sample=reference_sample,
        controls_individuals={'alpha': {True: 227, False: 207}},
        controls_households={'a': {True: 145, False: 45}},
        residuals_tol=tol,
        weights_tol=1e-16,
        maxiter=10
    )
    assert_weights_equal(expected_weights['infinity'], weights)


@pytest.mark.parametrize("tol", [(10), (1), (0.1)]) # assertion below uses tolerance 0.01
def test_weights_tolerance_criteria_stops_early(reference_sample, expected_weights, tol):
    weights = fit_hipf(
        reference_sample=reference_sample,
        controls_individuals={'alpha': {True: 227, False: 207}},
        controls_households={'a': {True: 145, False: 45}},
        residuals_tol=1e-16,
        weights_tol=tol,
        maxiter=10
    )
    with pytest.raises(AssertionError):
        assert_weights_equal(expected_weights['infinity'], weights)


@pytest.mark.parametrize("tol", [(0.01), (0.001)]) # assertion below uses tolerance 0.01
def test_weights_tolerance_criteria_does_not_stop_early(reference_sample, expected_weights, tol):
    weights = fit_hipf(
        reference_sample=reference_sample,
        controls_individuals={'alpha': {True: 227, False: 207}},
        controls_households={'a': {True: 145, False: 45}},
        residuals_tol=1e-16,
        weights_tol=tol,
        maxiter=10
    )
    assert_weights_equal(expected_weights['infinity'], weights)
