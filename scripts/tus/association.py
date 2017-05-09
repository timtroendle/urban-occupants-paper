from itertools import combinations

import click
import pandas as pd
import scipy.stats
import numpy as np

import urbanoccupants as uo
from urbanoccupants.tus import filter_features_and_drop_nan

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

filter_features = filter_features_and_drop_nan


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
    _association_of_features(seed, path_to_feature_association)
    _association_of_time_series(seed, markov_ts, path_to_ts_association)


def _association_of_features(seed, path_to_result):
    feature_correlation = pd.Series(
        index=combinations(ALL_FEATURES, 2),
        data=[_cramers_corrected_stat(pd.crosstab(filter_features(seed, features)[features[0]],
                                                  filter_features(seed, features)[features[1]]))
              for features in combinations([str(feature) for feature in ALL_FEATURES], 2)]
    )
    feature_correlation.to_pickle(path_to_result)


def _association_of_time_series(seed, markov_ts, path_to_result):
    markov_ts = markov_ts.unstack([0, 1, 2])
    markov_ts.columns = markov_ts.columns.droplevel(0)
    ts_corr_1d = pd.DataFrame({
        feature: _cramers_phi_for_features(markov_ts, seed, feature)
        for feature in [str(feature) for feature in ALL_FEATURES]
    })
    ts_corr_1d.to_pickle(path_to_result)


def _cramers_phi_for_features(markov_ts, seed, features):
    filtered_seed = filter_features(seed, features)
    return markov_ts.loc[:, filtered_seed.index].apply(_cramers_phi_for_feature(filtered_seed),
                                                       axis=1)


def _cramers_phi_for_feature(feature):
    if isinstance(feature, pd.Series): # 1D
        feature_ids = feature.apply(uo.feature_id)
    elif isinstance(feature, pd.DataFrame): # 2D or more
        feature_ids = feature.apply(uo.feature_id, axis=1)
    else:
        raise ValueError('Feature must be pandas series or dataframe.')

    def cramers_phi(series):
        return _cramers_corrected_stat(pd.crosstab(series.values, feature_ids))
    return cramers_phi


def _cramers_corrected_stat(confusion_matrix):
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
