from itertools import combinations, chain
from multiprocessing import Pool, cpu_count

import click
import pandas as pd
import scipy.stats
import scipy.special
import numpy as np
from tqdm import tqdm

import urbanoccupants as uo
from urbanoccupants.tus import filter_features, filter_features_and_drop_nan

ALL_FEATURES = [
    uo.PeopleFeature.ECONOMIC_ACTIVITY,
    uo.PeopleFeature.QUALIFICATION,
    uo.PeopleFeature.AGE,
    uo.HouseholdFeature.HOUSEHOLD_TYPE,
    uo.HouseholdFeature.POPULATION_DENSITY,
    uo.HouseholdFeature.REGION,
    uo.PeopleFeature.CARER,
    uo.PeopleFeature.PERSONAL_INCOME
]


@click.command()
@click.argument('path_to_seed')
@click.argument('path_to_markov_ts')
@click.argument('path_to_feature_association')
@click.argument('path_to_ts_association')
def calculate_association(path_to_seed, path_to_markov_ts, path_to_feature_association,
                          path_to_ts_association):
    """Calculates the association between people and household features and markov time series.

    Association is defined by Cramer's V method.

    For the time series it is calculated per time step.
    """
    seed = pd.read_pickle(path_to_seed)
    markov_ts = pd.read_pickle(path_to_markov_ts)
    feature_association = _association_of_features(seed)
    ts_association = _association_of_time_series(seed, markov_ts)
    feature_association.to_pickle(path_to_feature_association)
    ts_association.to_pickle(path_to_ts_association)


def _association_of_features(seed):
    filter_features = filter_features_and_drop_nan
    feature_association = pd.Series(
        index=combinations(ALL_FEATURES, 2),
        data=[cramers_corrected_stat(pd.crosstab(filter_features(seed, features)[features[0]],
                                                 filter_features(seed, features)[features[1]]))
              for features in tqdm(combinations([str(feature) for feature in ALL_FEATURES], 2),
                                   total=scipy.special.binom(len(ALL_FEATURES), 2),
                                   desc='Feature-feature association')]
    )
    return feature_association


def _association_of_time_series(seed, markov_ts):
    with Pool(cpu_count()) as pool:
        feature_strings = [str(feature) for feature in ALL_FEATURES]
        features_1d = [feature for feature in feature_strings]
        features_2d = [(feature1, feature2)
                       for feature1, feature2 in combinations(feature_strings, 2)]
        features_3d = [(feature1, feature2, feature3)
                       for feature1, feature2, feature3 in combinations(feature_strings, 3)]
        feature_combinations = list(chain(features_1d, features_2d, features_3d))
        all_parameters = ( # imap_unordered allows only one parameter, hence the tuple
            (seed,
             markov_ts,
             features)
            for features in feature_combinations
        )
        ts_association = dict(pool.imap_unordered(_cramers_phi_for_features,
                              tqdm(all_parameters,
                                   total=len(feature_combinations),
                                   desc='Time series association    ')))
    return pd.DataFrame(ts_association)


def _cramers_phi_for_features(params):
    seed, markov_ts, features = params
    if isinstance(features, tuple):
        tuple_features = features
    else:
        tuple_features = (features, ) # turning 1d feature to tuple
    seed, markov_ts = filter_features(seed, markov_ts, tuple_features)
    markov_ts = markov_ts.unstack(['SN1', 'SN2', 'SN3'])
    markov_ts.columns = markov_ts.columns.droplevel(0)
    return features, markov_ts.apply(_cramers_phi_for_feature(seed), axis=1)


def _cramers_phi_for_feature(seed):
    if not isinstance(seed, pd.Series) and not isinstance(seed, pd.DataFrame):
        raise ValueError('Seed must be pandas series or dataframe, but was {}.'
                         .format(type(seed)))
    if seed.shape[1] == 1: # 1 feature
        if isinstance(seed, pd.DataFrame):
            seed = seed.iloc[:, 0] # not sure why, but apply on a single-columned df fails
        feature_ids = seed.apply(uo.feature_id)
    else: # 2 or more features
        feature_ids = seed.apply(uo.feature_id, axis=1)

    def cramers_phi(series):
        return cramers_corrected_stat(pd.crosstab(series.values, feature_ids))
    return cramers_phi


def cramers_corrected_stat(confusion_matrix):
    """ Calculate Cramers V statistic for categorial-categorial association.
        uses correction from Bergsma and Wicher,
        Journal of the Korean Statistical Society 42 (2013): 323-328
    """
    # taken from http://stackoverflow.com/a/39266194/1856079
    chi2 = scipy.stats.chi2_contingency(confusion_matrix)[0]
    n = confusion_matrix.sum().sum()
    phi2 = chi2 / n
    r, k = confusion_matrix.shape
    phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
    rcorr = r - ((r - 1)**2) / (n - 1)
    kcorr = k - ((k - 1)**2) / (n - 1)
    return np.sqrt(phi2corr / min((kcorr - 1), (rcorr - 1)))


if __name__ == '__main__':
    calculate_association()
