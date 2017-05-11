import sys

import pandas as pd

sys.path.append('./scripts/tus/')
import association


def test_linear_function():
    vector1a = pd.Series([1, 2, 3, 4, 5])
    vector1b = pd.Series([2, 4, 6, 8, 10])
    vector2 = pd.Series([4, 4, 5, 5, 9])
    result1a = association.cramers_corrected_stat(pd.crosstab(vector1a, vector2))
    result1b = association.cramers_corrected_stat(pd.crosstab(vector1b, vector2))
    assert result1a == result1b


def test_purely_nominal():
    vector1a = pd.Series([1, 2, 1, 2, 4])
    vector1b = pd.Series([10, 28, 10, 28, 78])
    vector2 = pd.Series([4, 5, 4, 5, 4])
    result1a = association.cramers_corrected_stat(pd.crosstab(vector1a, vector2))
    result1b = association.cramers_corrected_stat(pd.crosstab(vector1b, vector2))
    assert result1a == result1b
