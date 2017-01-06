from datetime import time, timedelta
import math

import pandas as pd
import pytest

from people import Activity, week_markov_chain


@pytest.fixture
def weekday_time_series():
    index = [time(0, 0), time(12, 0)]
    values1 = [Activity.HOME, Activity.NOT_AT_HOME]
    values2 = [Activity.HOME, Activity.HOME]
    values3 = [Activity.HOME, Activity.NOT_AT_HOME]
    return pd.DataFrame(
        index=index,
        data={'person1': values1, 'person2': values2, 'person3': values3}
    )


@pytest.fixture
def weekend_day_time_series():
    index = [time(0, 0), time(12, 0)]
    values1 = [Activity.HOME, Activity.HOME]
    values2 = [Activity.HOME, Activity.HOME]
    values3 = [Activity.HOME, Activity.NOT_AT_HOME]
    return pd.DataFrame(
        index=index,
        data={'person1': values1, 'person2': values2, 'person3': values3}
    )


@pytest.fixture
def markov_chain(weekday_time_series, weekend_day_time_series):
    return week_markov_chain(
        weekday_time_series=weekday_time_series,
        weekend_time_series=weekend_day_time_series,
        time_step_size=timedelta(hours=12)
    )


def test_length_of_markov_chain(markov_chain):
    assert len(markov_chain['weekday']) == 2
    assert len(markov_chain['weekend']) == 2


@pytest.mark.parametrize('day, from_activity,to_activity,probability', [
    ('weekday', Activity.HOME, Activity.HOME, 0.333),
    ('weekday', Activity.HOME, Activity.NOT_AT_HOME, 0.666),
    ('weekend', Activity.HOME, Activity.HOME, 0.666),
    ('weekend', Activity.HOME, Activity.NOT_AT_HOME, 0.333)
])
def test_probabilities(markov_chain, day, from_activity, to_activity, probability):
    assert math.isclose(
        markov_chain[day][time(0, 0)][(from_activity, to_activity)],
        probability,
        abs_tol=0.001
    )
