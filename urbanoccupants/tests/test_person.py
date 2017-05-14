from collections import OrderedDict
from datetime import datetime, timedelta, time
from unittest.mock import Mock
import random

import pykov
import pytest

from urbanoccupants import Person, Activity, WeekMarkovChain


TIME_STEP_SIZE = timedelta(hours=1)


@pytest.fixture
def week_markov_chain():
    chain = Mock(spec_set=WeekMarkovChain)
    chain.time_step_size = TIME_STEP_SIZE
    return chain


@pytest.fixture
def person(week_markov_chain):
    return Person(
        week_markov_chain=week_markov_chain,
        number_generator=random.uniform,
        initial_activity=Activity.NOT_AT_HOME,
        initial_time=datetime(2016, 12, 18, 16, 00),
        time_step_size=timedelta(hours=1)
    )


@pytest.mark.parametrize('time_step_size', [timedelta(minutes=30), timedelta(hours=2)])
def test_inconsistent_time_step_size_fails(week_markov_chain, time_step_size):
    with pytest.raises(AssertionError):
        Person(
            week_markov_chain=week_markov_chain,
            number_generator=random.uniform,
            initial_activity=Activity.SLEEP_AT_HOME,
            initial_time=datetime(2016, 12, 13, 16, 00), # Tuesday
            time_step_size=time_step_size
        )


@pytest.mark.parametrize('next_activity', [ac for ac in Activity])
def test_chooses_next_activity(person, week_markov_chain, next_activity):
    week_markov_chain.move.return_value = next_activity
    person.step()
    assert person.activity == next_activity
