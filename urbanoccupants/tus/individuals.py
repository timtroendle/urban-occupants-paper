from itertools import chain

import click
import pandas as pd
import pytus2000

from ..synthpop import PeopleFeature, HouseholdFeature
from ..types import HouseholdType


HOUSEHOLD_TYPE_FEATURE_NAME = str(HouseholdFeature.HOUSEHOLD_TYPE)


@click.command()
@click.argument('path_to_input')
@click.argument('path_to_output')
def read_seed(path_to_input, path_to_output):
    """Reads, transforms, and filters the individual data from the TUS data set.

    The raw data is mapped to people and household features of this study, all other
    features are discarded. Furthermore the data set is filtered by correct households,
    e.g. a couple with children household must have at least 3 individuals, otherwise
    it is discarded as well.

    Output is written in plain pickle format.
    """
    individual_data = _read_raw_data(path_to_input)
    print("Read {} individuals.".format(individual_data.shape[0]))
    seed = _map_to_internal_types(individual_data)
    seed = _filter_invalid_households(seed)
    print("Write {} individuals.".format(seed.shape[0]))
    seed.to_pickle(path_to_output)


def filter_features_and_drop_nan(seed, features):
    """Filters seed by chosen features and drops nans.

    If there is any nan in any chosen feature for a certain individual in the seed, that
    individual will be dropped.
    """
    if isinstance(features, tuple): # 2D
        features = list(features)
    return seed[features].dropna(axis='index', how='any')


def _read_raw_data(path_to_input):
    return pytus2000.read_individual_file(path_to_input)


def _map_to_internal_types(individual_data):
    age = individual_data.IAGE
    seed = pd.DataFrame(index=individual_data.index)
    for feature in chain(PeopleFeature, HouseholdFeature):
        seed[str(feature)] = feature.tus_value_to_uo_value(
            individual_data[feature.tus_variable_name],
            age
        )
    return seed


def _filter_invalid_households(seed):
    hh_groups = seed.groupby((seed.index.get_level_values('SN1'),
                             seed.index.get_level_values('SN2')))
    households = hh_groups[HOUSEHOLD_TYPE_FEATURE_NAME].agg(['first', 'count'])
    households.rename(columns={'first': 'type'}, inplace=True)
    invalids = (
        households[(households.type == HouseholdType.COUPLE_WITH_DEPENDENT_CHILDREN) &
                   (households.size <= 2)] |
        households[(households.type == HouseholdType.COUPLE_WITHOUT_DEPENDENT_CHILDREN) &
                   (households.size != 2)] |
        households[(households.type == HouseholdType.LONE_PARENT_WITH_DEPENDENT_CHILDREN) &
                   (households.size < 2)] |
        households[(households.type == HouseholdType.MULTI_PERSON_HOUSEHOLD) &
                   (households.size <= 2)]
    )
    print("{} households are invalid and were removed.".format(len(invalids.index)))
    return seed.drop(labels=invalids.index, level=None)
