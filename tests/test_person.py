from collections import OrderedDict
from datetime import datetime, timedelta, time

import pykov
import pytest

from people import Person, Activity


@pytest.fixture
def pseudo_random():
    class Generator:

        number = 0.5

        def __call__(self, min, max):
            return self.number

    return Generator()


@pytest.fixture
def day_markov_chain():
    return pykov.Chain(OrderedDict([
        ((Activity.SLEEP_AT_HOME, Activity.NOT_AT_HOME), 0.9),
        ((Activity.SLEEP_AT_HOME, Activity.SLEEP_AT_HOME), 0.1),
        ((Activity.NOT_AT_HOME, Activity.SLEEP_AT_HOME), 0.2),
        ((Activity.NOT_AT_HOME, Activity.NOT_AT_HOME), 0.8)
    ]))


@pytest.fixture
def night_markov_chain():
    return pykov.Chain(OrderedDict([
        ((Activity.SLEEP_AT_HOME, Activity.NOT_AT_HOME), 0.0),
        ((Activity.SLEEP_AT_HOME, Activity.SLEEP_AT_HOME), 1.0),
        ((Activity.NOT_AT_HOME, Activity.SLEEP_AT_HOME), 0.7),
        ((Activity.NOT_AT_HOME, Activity.NOT_AT_HOME), 0.3)
    ]))


@pytest.fixture
def activity_markov_chains(day_markov_chain, night_markov_chain):
    chain = {}
    chain['weekday'] = {time(hour): day_markov_chain if (hour >= 9 and hour < 17)
                        else night_markov_chain
                        for hour in range(24)}
    chain['weekend'] = {time(hour): night_markov_chain for hour in range(24)}
    return chain


@pytest.fixture
def sleeping_person(activity_markov_chains, pseudo_random):
    return Person(
        activity_markov_chains=activity_markov_chains,
        number_generator=pseudo_random,
        initial_activity=Activity.SLEEP_AT_HOME,
        initial_time=datetime(2016, 12, 13, 16, 00), # Tuesday
        time_step_size=timedelta(hours=1)
    )


@pytest.fixture
def weekend_person(activity_markov_chains, pseudo_random):
    return Person(
        activity_markov_chains=activity_markov_chains,
        number_generator=pseudo_random,
        initial_activity=Activity.NOT_AT_HOME,
        initial_time=datetime(2016, 12, 18, 16, 00), # Sunday
        time_step_size=timedelta(hours=1)
    )


@pytest.mark.parametrize('time_step_size', [timedelta(minutes=30), timedelta(hours=2)])
def test_inconsistent_time_step_size_fails(activity_markov_chains, pseudo_random, time_step_size):
    with pytest.raises(AssertionError):
        Person(
            activity_markov_chains=activity_markov_chains,
            number_generator=pseudo_random,
            initial_activity=Activity.SLEEP_AT_HOME,
            initial_time=datetime(2016, 12, 13, 16, 00), # Tuesday
            time_step_size=time_step_size
        )


def test_sleeping_person_leaves_home_during_day(sleeping_person, pseudo_random):
    pseudo_random.number = 0.8
    sleeping_person.step()
    assert sleeping_person.activity == Activity.NOT_AT_HOME


def test_sleeping_person_remains_sleeping_during_day(sleeping_person, pseudo_random):
    pseudo_random.number = 0.91
    sleeping_person.step()
    assert sleeping_person.activity == Activity.SLEEP_AT_HOME


def test_away_person_remains_away_on_weekend(weekend_person, pseudo_random):
    pseudo_random.number = 0.71
    weekend_person.step()
    assert weekend_person.activity == Activity.NOT_AT_HOME


def test_away_person_starts_sleeping_on_weekend(weekend_person, pseudo_random):
    pseudo_random.number = 0.69
    weekend_person.step()
    assert weekend_person.activity == Activity.SLEEP_AT_HOME


def test_away_person_starts_sleeping_during_night(sleeping_person, pseudo_random):
    pseudo_random.number = 0.8
    sleeping_person.step()
    pseudo_random.number = 0.69
    sleeping_person.step()
    assert sleeping_person.activity == Activity.SLEEP_AT_HOME
