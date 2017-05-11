import click
import pandas as pd
import numpy as np

import urbanoccupants as uo


FEATURE_TO_KEEP = (str(uo.PeopleFeature.ECONOMIC_ACTIVITY),
                   str(uo.PeopleFeature.AGE),
                   str(uo.HouseholdFeature.HOUSEHOLD_TYPE)) # this is the 'best' feature


@click.command()
@click.argument('path_to_seed')
@click.argument('path_to_ts_association')
@click.argument('path_to_full_result')
@click.argument('path_to_filtered_result')
def analyse_association(path_to_seed, path_to_ts_association, path_to_full_result,
                        path_to_filtered_result):
    seed = pd.read_pickle(path_to_seed)
    ts_association = pd.read_pickle(path_to_ts_association)
    stats = pd.DataFrame({
        'mean_association': ts_association.mean(),
        'std_association': ts_association.std(),
        'min_cluster_size': [seed.groupby(features).size().min()
                             for features in ts_association.columns],
        'mean_cluster_size': [seed.groupby(features).size().mean()
                              for features in ts_association.columns],
        'std_cluster_size': [seed.groupby(features).size().std()
                             for features in ts_association.columns]
    })
    stats.sort_values(by='mean_association', ascending=False, inplace=True)
    stats.to_csv(path_to_full_result)
    _filter(stats).to_csv(
        path_to_filtered_result,
        float_format=''
    )


def _filter(stats):
    fstats = stats[[not isinstance(idx, tuple) or len(set(idx)) < 3 or idx == FEATURE_TO_KEEP
                    for idx in stats.index]] # filter 3d
    fstats = fstats.reset_index()

    def _rename_index(index_name):
        if isinstance(index_name, tuple):
            index_name = ','.join(index_name)
        for key, value in feature_name_map.items():
            index_name = index_name.replace(key, value)
        return index_name
    fstats.index = fstats['index'].apply(_rename_index)
    fstats.drop(['index'], axis=1, inplace=True)
    fstats['mean_association'] = fstats['mean_association'].apply(np.round, decimals=5)
    fstats['mean_cluster_size'] = fstats['mean_cluster_size'].apply(np.round, decimals=0)
    fstats.rename(columns={
        'mean_association': '$\overline{\Phi_C}$',
        'mean_cluster_size': 'avg cluster size'
    }, inplace=True)
    fstats.drop(['min_cluster_size', 'std_association', 'std_cluster_size'], axis=1, inplace=True)
    return fstats[:6]


feature_name_map = {
    'HouseholdFeature.HOUSEHOLD_TYPE': 'hhtype',
    'HouseholdFeature.POPULATION_DENSITY': 'popden',
    'HouseholdFeature.REGION': 'region',
    'PeopleFeature.CARER': 'carer',
    'PeopleFeature.PERSONAL_INCOME': 'income',
    'PeopleFeature.AGE': 'age',
    'PeopleFeature.ECONOMIC_ACTIVITY': 'ecact',
    'PeopleFeature.QUALIFICATION': 'qual'
}

if __name__ == '__main__':
    analyse_association()
