from datetime import time, timedelta, datetime
import math
from io import StringIO

import pandas as pd
from pandas.util.testing import assert_frame_equal
import pytest

from people import Activity, week_markov_chain, week_markov_chain_to_dataframe
from people import person


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


@pytest.fixture
def markov_chain_as_dataframe():
    day_column = ['weekday'] * 4 + ['weekend'] * 4
    time_column = ([time(0, 0)] * 2 + [time(12, 00)] * 2) * 2
    from_column = [
        Activity.HOME, Activity.HOME, Activity.HOME, Activity.NOT_AT_HOME,
        Activity.HOME, Activity.HOME, Activity.HOME, Activity.NOT_AT_HOME
    ]
    to_column = [
        Activity.HOME, Activity.NOT_AT_HOME, Activity.HOME, Activity.HOME,
        Activity.HOME, Activity.NOT_AT_HOME, Activity.HOME, Activity.HOME
    ]
    prob_column = [
        0.333, 0.666, 1.0, 1.0,
        0.666, 0.333, 1.0, 1.0
    ]
    df = pd.DataFrame({
        person.MARKOV_CHAIN_DAY_COLUMN_NAME: day_column,
        person.MARKOV_CHAIN_TIME_OF_DAY_COLUMN_NAME: time_column,
        person.MARKOV_CHAIN_FROM_ACTIVITY_COLUMN_NAME: from_column,
        person.MARKOV_CHAIN_TO_ACTIVITY_COLUMN_NAME: to_column,
        person.MARKOV_CHAIN_PROBABILITY_COLUMN_NAME: prob_column
    })
    df.set_index(
        [person.MARKOV_CHAIN_DAY_COLUMN_NAME, person.MARKOV_CHAIN_TIME_OF_DAY_COLUMN_NAME],
        inplace=True
    )
    return df


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


def test_dataframe_representation(markov_chain, markov_chain_as_dataframe):
    cols = [ # sort, as we are not interested in column order
        person.MARKOV_CHAIN_FROM_ACTIVITY_COLUMN_NAME,
        person.MARKOV_CHAIN_TO_ACTIVITY_COLUMN_NAME,
        person.MARKOV_CHAIN_PROBABILITY_COLUMN_NAME
    ]
    assert_frame_equal(
        week_markov_chain_to_dataframe(markov_chain)[cols],
        markov_chain_as_dataframe[cols],
        check_exact=False,
        check_less_precise=2
    )
