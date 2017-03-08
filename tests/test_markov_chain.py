from collections import OrderedDict
from datetime import time, timedelta, datetime
import math
from io import StringIO
import random

import pandas as pd
from pandas.util.testing import assert_frame_equal
import pytest
import pykov

from people import Activity, WeekMarkovChain
from people import person


MIDNIGHT_WEEKDAY = datetime(2017, 3, 8, 0, 0)
MIDNIGHT_WEEKEND = datetime(2017, 3, 5, 0, 0)


@pytest.fixture
def random_func():
    random.seed('markov chain tests')
    return random.uniform


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
def not_matching_weekend_day_time_series():
    index = [time(0, 0), time(12, 0)]
    values1 = [Activity.NOT_AT_HOME, Activity.HOME]
    values2 = [Activity.HOME, Activity.HOME]
    values3 = [Activity.HOME, Activity.NOT_AT_HOME]
    return pd.DataFrame(
        index=index,
        data={'person1': values1, 'person2': values2, 'person3': values3}
    )


@pytest.fixture
def markov_chain(weekday_time_series, weekend_day_time_series):
    return WeekMarkovChain(
        weekday_time_series=weekday_time_series,
        weekend_time_series=weekend_day_time_series,
        time_step_size=timedelta(hours=12)
    )


@pytest.fixture
def dead_locked_markov_chain(weekday_time_series, not_matching_weekend_day_time_series):
    return WeekMarkovChain(
        weekday_time_series=weekday_time_series,
        weekend_time_series=not_matching_weekend_day_time_series,
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


def test_time_step_size(markov_chain):
    assert markov_chain.time_step_size == timedelta(hours=12)


@pytest.mark.parametrize('time_stamp,from_activity,to_activity,probability', [
    (MIDNIGHT_WEEKDAY, Activity.HOME, Activity.HOME, 0.333),
    (MIDNIGHT_WEEKDAY, Activity.HOME, Activity.NOT_AT_HOME, 0.666),
    (MIDNIGHT_WEEKEND, Activity.HOME, Activity.HOME, 0.666),
    (MIDNIGHT_WEEKEND, Activity.HOME, Activity.NOT_AT_HOME, 0.333)
])
def test_probabilities(markov_chain, random_func, time_stamp, from_activity, to_activity,
                       probability):
    next_states = [markov_chain.move(current_state=from_activity,
                                     current_time=time_stamp,
                                     random_func=random_func)
                   for unused in range(500)]
    actual_probability = (len([state for state in next_states if state == to_activity]) /
                          len(next_states))
    assert math.isclose(
        actual_probability,
        probability,
        abs_tol=0.05
    )


def test_dead_locks_are_handled(dead_locked_markov_chain, random_func):
    # Time series can always contain states for which no transition exists.
    # In the test data above such a state exist for the transitioning from
    # weekend 12:00 to weekday 00:00. The markov chain generation should
    # make sure that in these cases the next markov chain will contain the
    # end state of the previous chain as a start state. As we don't know
    # any likelihood of state transition we assume the state remains the
    # same.
    next_state = dead_locked_markov_chain.move(
        current_time=MIDNIGHT_WEEKDAY,
        current_state=Activity.NOT_AT_HOME,
        random_func=random_func
    )
    assert next_state == Activity.NOT_AT_HOME


def test_dataframe_representation(markov_chain, markov_chain_as_dataframe):
    cols = [ # sort, as we are not interested in column order
        person.MARKOV_CHAIN_FROM_ACTIVITY_COLUMN_NAME,
        person.MARKOV_CHAIN_TO_ACTIVITY_COLUMN_NAME,
        person.MARKOV_CHAIN_PROBABILITY_COLUMN_NAME
    ]
    assert_frame_equal(
        markov_chain.to_dataframe()[cols],
        markov_chain_as_dataframe[cols],
        check_exact=False,
        check_less_precise=2
    )
