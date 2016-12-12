from collections import OrderedDict

import pykov
import pytest

from people import Person


@pytest.fixture
def pseudo_random_number_generator(scope="module"):
    class Generator:

        number = 0.5

        def __call__(self, min, max):
            return self.number

    return Generator()


@pytest.fixture
def activity_markov_chain():
    return pykov.Chain(OrderedDict([
        (('sleep', 'work'), 0.3),
        (('sleep', 'sleep'), 0.7),
        (('work', 'sleep'), 0.2),
        (('work', 'work'), 0.8)
    ]))


@pytest.fixture
def sleeping_person(activity_markov_chain, pseudo_random_number_generator):
    return Person(
        activity_markov_chain=activity_markov_chain,
        number_generator=pseudo_random_number_generator,
        initial_activity='sleep'
    )


def test_sleeping_person_starts_working(sleeping_person, pseudo_random_number_generator):
    pseudo_random_number_generator.number = 0.1
    sleeping_person.step()
    assert sleeping_person.activity == 'work'


def test_sleeping_person_remains_sleeping(sleeping_person, pseudo_random_number_generator):
    pseudo_random_number_generator.number = 0.31
    sleeping_person.step()
    assert sleeping_person.activity == 'sleep'
