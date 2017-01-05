import datetime
from enum import Enum


class Activity(Enum):
    HOME = 1
    SLEEP_AT_HOME = 2
    OTHER_HOME = 3
    SLEEP_AT_OTHER_HOME = 4
    NOT_AT_HOME = 5


class Person():

    def __init__(self, activity_markov_chains, initial_activity, number_generator,
                 initial_time, time_step_size):
        self.__chain = _TimeHeterogenousMarkovChain(
            activity_markov_chains=activity_markov_chains,
            time_step_size=time_step_size,
            number_generator=number_generator
        )
        if not isinstance(initial_activity, Activity):
            raise ValueError('Initial activity must be an people.Activity.')
        self.activity = initial_activity
        self.__time = initial_time
        self.__time_step_size = time_step_size

    def step(self):
        self.activity = self.__chain.move(current_state=self.activity, current_time=self.__time)
        self.__time += self.__time_step_size


class _TimeHeterogenousMarkovChain():

    def __init__(self, activity_markov_chains, time_step_size, number_generator):
        assert 'weekday' in activity_markov_chains.keys()
        assert 'weekend' in activity_markov_chains.keys()
        assert all(isinstance(time, datetime.time)
                   for time in activity_markov_chains['weekday'].keys())
        assert all(isinstance(time, datetime.time)
                   for time in activity_markov_chains['weekend'].keys())
        assert all(isinstance(activity, Activity)
                   for chain in activity_markov_chains['weekday'].values()
                   for activity in chain.states())
        assert all(isinstance(activity, Activity)
                   for chain in activity_markov_chains['weekend'].values()
                   for activity in chain.states())
        n_time_steps_per_day = datetime.timedelta(hours=24) / time_step_size
        assert len(activity_markov_chains['weekday']) == n_time_steps_per_day
        assert len(activity_markov_chains['weekend']) == n_time_steps_per_day
        self.__number_generator = number_generator
        self.__chains = {day: activity_markov_chains['weekday'] if day < 5
                         else activity_markov_chains['weekend']
                         for day in range(7)}

    def move(self, current_state, current_time):
        return self._select_chain(current_time).move(
            state=current_state,
            random_func=self.__number_generator
        )

    def _select_chain(self, current_time):
        return self.__chains[current_time.weekday()][current_time.time()]
