"""These tests test the HIPF algorithm with two control totals.

The problem is the `Separate` problem among the toy example taken from
https://github.com/krlmlr/MultiLevelIPF/commit/408d23d9db6536b47d78ab0c65aff40111a829fc.

Results were created from the given repository with default parameters, i.e. running
`ml_fit_hipf(toy_example('Separate'))`. Hence `tol` was 1e-6, `diff_tol` was set to
2.220446e-16, and `maxiter` was 200.
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.util.testing import assert_series_equal
import pytest

from urbanoccupants.hipf import fit_hipf, _all_residuals


RESOURCES_PATH = Path(__file__).parent / 'resources'
PATH_TO_REFERENCE_SAMPLE = RESOURCES_PATH / 'two_controls_reference_sample.csv'
PATH_TO_RESULTS = RESOURCES_PATH / 'two_controls_results.csv'


@pytest.fixture
def reference_sample():
    sample = pd.read_csv(PATH_TO_REFERENCE_SAMPLE)
    return sample.set_index(['HHNR', 'PNR'])


@pytest.fixture
def controls_individuals():
    return {'WKSTAT': {0: 395, 1: 459}, 'GENDER': {'X': 434, 'Y': 420}}


@pytest.fixture
def controls_households():
    return {'CAR': {0: 99, 1: 273}}


@pytest.fixture(params=[
    {'UNKNOWN_NAME': {0: 395, 1: 459}, 'GENDER': {'X': 434, 'Y': 420}},
    {'WKSTAT': {0: 10, 1: 20}, 'GENDER': {'X': 434, 'Y': 420}},
    {}
])
def invalid_controls_individuals(request):
    return request.param


@pytest.fixture(params=[
    {'UNKNOWN_NAME': {0: 99, 1: 273}},
    {}
])
def invalid_controls_households(request):
    return request.param


@pytest.fixture
def invalid_index_reference_sample(reference_sample):
    return reference_sample.reset_index() # this mlipf, no multi-index style is invalid


@pytest.fixture
def expected_weights():
    weights = pd.read_csv(PATH_TO_RESULTS)
    return weights.reset_index(drop=True).iloc[:, 0] # weights are indexed from 1, ref sample from 0


def assert_weights_equal(expected_weights, weights, precision=1):
    weights.name = expected_weights.name # don't want to check the name
    weights.index.name = expected_weights.index.name # don't want to check the name
    assert_series_equal(expected_weights, weights, check_less_precise=precision)


@pytest.mark.xfail(reason="Currently the algorithms do not seem to be equal.")
def test_same_result_like_mlipf(reference_sample, expected_weights, controls_individuals,
                                controls_households):
    weights = fit_hipf(
        reference_sample=reference_sample,
        controls_individuals=controls_individuals,
        controls_households=controls_households,
        weights_tol=2.220446e-16,
        residuals_tol=1e-6,
        maxiter=200
    )
    assert_weights_equal(expected_weights, weights)


@pytest.mark.parametrize("tol", [(1), pytest.mark.xfail(0.1)])
def test_converges(reference_sample, controls_households, controls_individuals, tol):
    weights = fit_hipf(
        reference_sample=reference_sample,
        controls_individuals=controls_individuals,
        controls_households=controls_households,
        weights_tol=2.220446e-16,
        residuals_tol=1e-6,
        maxiter=200
    )
    residuals = _all_residuals(reference_sample, weights, controls_households, controls_individuals)
    assert residuals.abs().max() < tol


def test_fails_with_invalid_controls_individuals(reference_sample, controls_households,
                                                 invalid_controls_individuals):
    with pytest.raises(AssertionError):
        weights = fit_hipf(
            reference_sample=reference_sample,
            controls_individuals=invalid_controls_individuals,
            controls_households=controls_households,
            maxiter=2
        )


def test_fails_with_invalid_controls_household(reference_sample, invalid_controls_households,
                                               controls_individuals):
    with pytest.raises(AssertionError):
        weights = fit_hipf(
            reference_sample=reference_sample,
            controls_individuals=controls_individuals,
            controls_households=invalid_controls_households,
            maxiter=2
        )


def test_fails_with_invalid_index_reference_sample(invalid_index_reference_sample,
                                                   controls_households, controls_individuals):
    with pytest.raises(AssertionError):
        weights = fit_hipf(
            reference_sample=invalid_index_reference_sample,
            controls_individuals=controls_individuals,
            controls_households=controls_households,
            maxiter=2
        )


def test_fails_with_invalid_type_reference_sample(reference_sample,
                                                  controls_households, controls_individuals):
    with pytest.raises(AssertionError):
        weights = fit_hipf(
            reference_sample=np.array(reference_sample),
            controls_individuals=controls_individuals,
            controls_households=controls_households,
            maxiter=2
        )
