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
        self.__chain = _TimeHeterogenousMarkovChain(activity_markov_chains, number_generator)
        if not isinstance(initial_activity, Activity):
            raise ValueError('Initial activity must be an people.Activity.')
        self.activity = initial_activity
        self.__time = initial_time
        self.__time_step_size = time_step_size

    def step(self):
        self.activity = self.__chain.move(current_state=self.activity, current_time=self.__time)
        self.__time += self.__time_step_size


class _TimeHeterogenousMarkovChain():

    def __init__(self, activity_markov_chains, number_generator):
        self.__number_generator = number_generator
        if 'weekday' not in activity_markov_chains.keys():
            raise ValueError('Activity markov chains have wrong format.')
        if 'weekend' not in activity_markov_chains.keys():
            raise ValueError('Activity markov chains have wrong format.')
        if any(hour not in activity_markov_chains['weekday'] for hour in range(24)):
            raise ValueError('Activity markov chains have wrong format.')
        if any(hour not in activity_markov_chains['weekend'] for hour in range(24)):
            raise ValueError('Activity markov chains have wrong format.')
        self.__chains = {day: activity_markov_chains['weekday'] if day < 5
                         else activity_markov_chains['weekend']
                         for day in range(7)}
        for day in range(7):
            for hour in range(24):
                activities = self.__chains[day][hour].states()
                if not all(isinstance(activity, Activity) for activity in activities):
                    msg = 'At least one activity in {} is not a people.Activity.'.format(activities)
                    raise ValueError(msg)

    def move(self, current_state, current_time):
        return self._select_chain(current_time).move(
            state=current_state,
            random_func=self.__number_generator
        )

    def _select_chain(self, current_time):
        return self.__chains[current_time.weekday()][current_time.hour]
