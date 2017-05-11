from enum import Enum

import pandas as pd

from urbanoccupants.synthpop import feature_id, _pairing_function


class Feature(Enum):
    A = 1
    B = 2
    C = 3


def test_1d_feature():
    assert feature_id(Feature.A) == 1


def test_2d_feature_tuple():
    assert feature_id((Feature.A, Feature.B)) == _pairing_function(1, 2)


def test_2d_feature_series():
    assert feature_id(pd.Series([Feature.A, Feature.B])) == _pairing_function(1, 2)


def test_3d_feature_tuple():
    assert (feature_id((Feature.A, Feature.B, Feature.C)) ==
            _pairing_function(_pairing_function(1, 2), 3))


def test_3d_tuple_series():
    assert (feature_id(pd.Series([Feature.A, Feature.B, Feature.C])) ==
            _pairing_function(_pairing_function(1, 2), 3))
