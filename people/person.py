from collections import OrderedDict
import datetime
from enum import Enum

import pykov
import pandas as pd


MARKOV_CHAIN_DAY_COLUMN_NAME = 'day'
MARKOV_CHAIN_TIME_OF_DAY_COLUMN_NAME = 'time'
MARKOV_CHAIN_FROM_ACTIVITY_COLUMN_NAME = 'fromActivity'
MARKOV_CHAIN_TO_ACTIVITY_COLUMN_NAME = 'toActivity'
MARKOV_CHAIN_PROBABILITY_COLUMN_NAME = 'probability'


class Activity(Enum):
    """Activities of citizens."""
    HOME = 1
    SLEEP_AT_HOME = 2
    OTHER_HOME = 3
    SLEEP_AT_OTHER_HOME = 4
    NOT_AT_HOME = 5

    def __str__(self):
        return self.name


class Person():
    """The model of a citizen making choices on activities and locations.

    Parameters:
        * week_markov_chain:      a heterogeneous markov chain for a week of type
                                  people.WeekMarkovChain
        * number_generator:       a callable returning a random number between min and max
                                  parameters
        * initial_activity:       the activity at initial time
        * initial_time:           the initial time
        * time_step_size:         the time step size of the simulation, must be consistent with
                                  time step size of markov chains

    For example:

    Person(
        week_markov_chain=week_markov_chain
        number_generator=random.uniform,
        initial_activity=HOME,
        initial_time=datetime(2016, 12, 15, 12, 06),
        time_step_size=timedelta(hours=1)
    )
    """

    def __init__(self, week_markov_chain, initial_activity, number_generator,
                 initial_time, time_step_size):
        assert week_markov_chain.time_step_size == time_step_size
        self.__chain = week_markov_chain
        assert isinstance(initial_activity, Activity)
        self.activity = initial_activity
        self.__number_generator = number_generator
        self.__time = initial_time
        self.__time_step_size = time_step_size

    def step(self):
        """Run simulation for one time step.

        Chooses new activity.
        Updates internal time by time step.
        """
        self.activity = self._choose_next_activity()
        self.__time += self.__time_step_size

    def _choose_next_activity(self):
        return self.__chain.move(
            current_state=self.activity,
            current_time=self.__time,
            random_func=self.__number_generator
        )


class WeekMarkovChain():

    @property
    def time_step_size(self):
        pass

    def move(current_state, current_time, random_func):
        pass

    def _weekday(self):
        day_number = self.__time.weekday()
        assert day_number in list(range(7))
        if day_number in list(range(5)):
            return 'weekday'
        else:
            return 'weekend'


def week_markov_chain(weekday_time_series, weekend_time_series, time_step_size):
    """Creates a time heterogeneous markov chain for one week from time series of activities.

    Parameters:
        * weekday_time_series: 24h time series of Activities with given time step size of a
                               weekday. The index should be instances of time, and there can
                               be arbitrary many columns, each column representing the weekday
                               of one person.
        * weekend_time_series: As weekday_time_series, but for a weekend day.
        * time_step_size:      A timedelta representing the time step size of above time series.
    """
    return {
        'weekday': _day_markov_chain(weekday_time_series, time_step_size),
        'weekend': _day_markov_chain(weekend_time_series, time_step_size)
    }


def week_markov_chain_to_dataframe(markov_chain):
    """Creates a dataframe representation of a time heterogeneous markov chain.

    Can be used to serialise the markov chain into csv or sql.
    """
    df = pd.DataFrame(columns=[
        MARKOV_CHAIN_DAY_COLUMN_NAME,
        MARKOV_CHAIN_TIME_OF_DAY_COLUMN_NAME,
        MARKOV_CHAIN_FROM_ACTIVITY_COLUMN_NAME,
        MARKOV_CHAIN_TO_ACTIVITY_COLUMN_NAME,
        MARKOV_CHAIN_PROBABILITY_COLUMN_NAME
    ])
    for day, day_chain in markov_chain.items():
        assert day in ['weekday', 'weekend']
        for time_stamp, single_markov_chain in day_chain.items():
            assert isinstance(time_stamp, datetime.time)
            single_df = pd.DataFrame({
                MARKOV_CHAIN_DAY_COLUMN_NAME: day,
                MARKOV_CHAIN_TIME_OF_DAY_COLUMN_NAME: time_stamp,
                MARKOV_CHAIN_FROM_ACTIVITY_COLUMN_NAME: [element[0]
                                                         for element in single_markov_chain],
                MARKOV_CHAIN_TO_ACTIVITY_COLUMN_NAME: [element[1]
                                                       for element in single_markov_chain],
                MARKOV_CHAIN_PROBABILITY_COLUMN_NAME: [single_markov_chain[element]
                                                       for element in single_markov_chain]
            })
            df = df.append(single_df, ignore_index=True)
    assert not df.isnull().any().any()
    df.set_index([MARKOV_CHAIN_DAY_COLUMN_NAME, MARKOV_CHAIN_TIME_OF_DAY_COLUMN_NAME], inplace=True)
    return df


def _day_markov_chain(day_time_series, time_step_size):
    return {
        time_step: _markov_chain(time_step, day_time_series, time_step_size)
        for time_step in _day_time_step_generator(time_step_size)
    }


def _day_time_step_generator(time_step_size):
    assert time_step_size % datetime.timedelta(minutes=1) == datetime.timedelta(minutes=0)
    start_time = datetime.time(0, 0)
    for minutes in range(0, 24 * 60, int(time_step_size.total_seconds() / 60)):
        yield _add_delta_to_time(start_time, datetime.timedelta(minutes=minutes))


def _markov_chain(time_step, day_time_series, time_step_size):
    next_time_step = _add_delta_to_time(time_step, time_step_size)
    current_vector = day_time_series.ix[time_step]
    next_vector = day_time_series.ix[next_time_step]
    chain_elements = [((current_state, next_state), _probability(current_state, next_state,
                                                                 current_vector, next_vector))
                      for current_state in Activity
                      for next_state in Activity]
    return pykov.Chain(OrderedDict(chain_elements))


def _probability(current_state, next_state, current_vector, next_vector):
    if current_state in current_vector.unique():
        current_mask = current_vector == current_state
        next_mask = next_vector == next_state
        next_instances = len(next_vector[current_mask & next_mask])
        current_instances = len(current_vector[current_mask])
        return next_instances / current_instances
    else:
        return 0


def _add_delta_to_time(time_step, delta):
    fulldate = datetime.datetime.combine(datetime.datetime(100, 1, 1), time_step)
    fulldate = fulldate + delta
    return fulldate.time()
