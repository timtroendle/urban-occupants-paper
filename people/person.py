from collections import OrderedDict
import datetime
from enum import Enum
import math

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
    """A time heterogeneous markov chain of people activities for one week.

    Parameters:
        * weekday_time_series: 24h time series of Activities with given time step size of a
                               weekday. The index should be instances of time, and there can
                               be arbitrary many columns, each column representing the weekday
                               of one person.
        * weekend_time_series: As weekday_time_series, but for a weekend day.
        * time_step_size:      A timedelta representing the time step size of above time series.
    """

    def __init__(self, weekday_time_series, weekend_time_series, time_step_size):
        self.__time_step_size = time_step_size
        if weekday_time_series.isnull().any().any():
            raise ValueError('Weekday time series contains missing values.')
        if weekend_time_series.isnull().any().any():
            raise ValueError('Weekend time series contains missing values.')
        self.__chain = {
            'weekday': WeekMarkovChain._day_markov_chain(weekday_time_series, time_step_size),
            'weekend': WeekMarkovChain._day_markov_chain(weekend_time_series, time_step_size)
        }
        self._add_missing_transitions()
        # there is a chance that after the first round of adding transitions, the markov chain is
        # still not valid (the first element could have a new element now that the second doesn't
        # have). This is ignored for the moment, as the chain is validated anyway again.
        self._validate()

    @property
    def time_step_size(self):
        return self.__time_step_size

    def move(self, current_state, current_time, random_func):
        return self.__chain[WeekMarkovChain._weekday(current_time)][current_time.time()].move(
            state=current_state,
            random_func=random_func
        )

    def to_dataframe(self):
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
        for day, day_chain in self.__chain.items():
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
        df.set_index(
            [MARKOV_CHAIN_DAY_COLUMN_NAME, MARKOV_CHAIN_TIME_OF_DAY_COLUMN_NAME],
            inplace=True
        )
        return df

    def _validate(self):
        assert 'weekday' in self.__chain.keys()
        assert 'weekend' in self.__chain.keys()
        assert all(isinstance(time_step, datetime.time)
                   for time_step in self.__chain['weekday'].keys())
        assert all(isinstance(time_step, datetime.time)
                   for time_step in self.__chain['weekend'].keys())
        assert all(isinstance(activity, Activity)
                   for chain in self.__chain['weekday'].values()
                   for activity in chain.states())
        assert all(isinstance(activity, Activity)
                   for chain in self.__chain['weekend'].values()
                   for activity in chain.states())
        assert self._valid_transitions()
        assert self._valid_probabilities()

    def _valid_probabilities(self):
        return all(WeekMarkovChain._probabilities_add_to_one(self.__chain[day][time])
                   for day in ['weekday', 'weekend']
                   for time in WeekMarkovChain._day_time_step_generator(self.__time_step_size))

    @staticmethod
    def _probabilities_add_to_one(markov_chain):
        start_states = [item[0][0] for item in markov_chain.items()]
        return all(math.isclose(
                   sum(item[1] for item in markov_chain.items() if item[0][0] == start_state),
                   1.0,
                   abs_tol=0.001
                   ) for start_state in start_states)

    def _valid_transitions(self):
        flags = [WeekMarkovChain._valid_transition(self.__chain[day][time],
                                                   self.__chain[next_day][next_time])
                 for day, time, next_day, next_time
                 in WeekMarkovChain._all_possible_time_combinations(self.__time_step_size)]
        return all(flags)

    @staticmethod
    def _valid_transition(single_markov_chain, next_single_markov_chain):
        end_states_first = [x[0][1] for x in single_markov_chain.items()]
        start_states_second = [x[0][0] for x in next_single_markov_chain.items()]
        return all([state in start_states_second for state in end_states_first])

    def _add_missing_transitions(self):
        for day, time in WeekMarkovChain._week_time_steps_generator(self.__time_step_size):
            next_day, next_time = WeekMarkovChain._add_delta_to_day_and_time(day, time,
                                                                             self.__time_step_size)
            current_chain = self.__chain[day][time].items()
            next_chain = self.__chain[next_day][next_time].items()
            end_states_current_chain = [x[0][1] for x in current_chain]
            start_states_next_chain = [x[0][0] for x in next_chain]
            missing_start_states = [state for state in end_states_current_chain
                                    if state not in start_states_next_chain]
            for missing_state in missing_start_states:
                self._add_transition(
                    day=next_day,
                    time=next_time,
                    from_activity=missing_state,
                    to_activity=missing_state,
                    probability=1.0
                )

    def _add_transition(self, day, time, from_activity, to_activity, probability):
        chain = self.__chain[day][time]
        elements = OrderedDict(chain)
        elements[(from_activity, to_activity)] = probability
        self.__chain[day][time] = pykov.Chain(elements)

    @staticmethod
    def _weekday(time_stamp):
        day_number = time_stamp.weekday()
        assert day_number in list(range(7))
        if day_number in list(range(5)):
            return 'weekday'
        else:
            return 'weekend'

    @staticmethod
    def _day_markov_chain(day_time_series, time_step_size):
        return {
            time_step: WeekMarkovChain._markov_chain(time_step, day_time_series, time_step_size)
            for time_step in WeekMarkovChain._day_time_step_generator(time_step_size)
        }

    @staticmethod
    def _day_time_step_generator(time_step_size):
        assert time_step_size % datetime.timedelta(minutes=1) == datetime.timedelta(minutes=0)
        start_time = datetime.time(0, 0)
        for minutes in range(0, 24 * 60, int(time_step_size.total_seconds() / 60)):
            yield WeekMarkovChain._add_delta_to_time(start_time,
                                                     datetime.timedelta(minutes=minutes))

    @staticmethod
    def _week_time_steps_generator(time_step_size):
        # starts Tuesday so that there are all possible combinations between work and weekend days
        for day in ['weekday', 'weekday', 'weekday', 'weekday', 'weekend', 'weekend', 'weekday']:
            for time_step in WeekMarkovChain._day_time_step_generator(time_step_size):
                yield day, time_step

    @staticmethod
    def _all_possible_time_combinations(time_step_size):
        # starts Tuesday so that there are all possible combinations between work and weekend days
        for day in ['weekday', 'weekday', 'weekday', 'weekday', 'weekend', 'weekend', 'weekday']:
            for time_step in WeekMarkovChain._day_time_step_generator(time_step_size):
                next_day, next_time = WeekMarkovChain._add_delta_to_day_and_time(
                    day, time_step, time_step_size
                )
                yield day, time_step, next_day, next_time

    @staticmethod
    def _markov_chain(time_step, day_time_series, time_step_size):
        next_time_step = WeekMarkovChain._add_delta_to_time(time_step, time_step_size)
        current_vector = day_time_series.ix[time_step]
        next_vector = day_time_series.ix[next_time_step]
        chain_elements = [((current_state, next_state), WeekMarkovChain._probability(current_state,
                                                                                     next_state,
                                                                                     current_vector,
                                                                                     next_vector))
                          for current_state in Activity
                          for next_state in Activity]
        return pykov.Chain(OrderedDict(chain_elements))

    @staticmethod
    def _probability(current_state, next_state, current_vector, next_vector):
        if current_state in current_vector.unique():
            current_mask = current_vector == current_state
            next_mask = next_vector == next_state
            next_instances = len(next_vector[current_mask & next_mask])
            current_instances = len(current_vector[current_mask])
            return next_instances / current_instances
        else:
            return 0

    @staticmethod
    def _add_delta_to_time(time_step, delta):
        fulldate = datetime.datetime.combine(datetime.datetime(100, 1, 1), time_step)
        fulldate = fulldate + delta
        return fulldate.time()

    @staticmethod
    def _add_delta_to_day_and_time(day, time_step, delta):
        random_date = datetime.datetime.combine(datetime.datetime(100, 1, 1), time_step)
        updated_date = random_date + delta
        if (random_date.date() == updated_date.date()):
            return day, updated_date.time()
        else:
            next_day = 'weekend' if day == 'weekday' else 'weekday'
            return next_day, updated_date.time()
