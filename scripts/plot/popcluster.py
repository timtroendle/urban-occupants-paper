import click
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from scipy.ndimage.filters import gaussian_filter
import pandas as pd
import numpy as np

import people as ppl
import urbanoccupants as uo

GREY_COLORMAP = ListedColormap(sns.light_palette("black", 30)[2:20])
GAUSSIAN_SIGMA = 0.7
ALL_FEATURES = [
    uo.synthpop.PeopleFeature.ECONOMIC_ACTIVITY,
    uo.synthpop.PeopleFeature.AGE
]


@click.command()
@click.argument('path_to_seed')
@click.argument('path_to_markov_ts')
@click.argument('path_to_plot')
def population_cluster(path_to_seed, path_to_markov_ts, path_to_plot):
    seed = pd.read_pickle(path_to_seed)
    markov_ts = _convert_to_numerical_values(pd.read_pickle(path_to_markov_ts))
    seed, markov_ts = uo.tus.filter_features(seed, markov_ts, ALL_FEATURES)
    fig = plt.figure(figsize=(14, 7))
    ax = fig.add_subplot(len(ALL_FEATURES) + 1, 1, 1)
    _plot_heatmap(markov_ts.unstack(['SN1', 'SN2', 'SN3']), ax, '(a)')
    for i, (feature, name) in enumerate(zip(ALL_FEATURES, 'bcdefg')):
        ax = fig.add_subplot(len(ALL_FEATURES) + 1, 1, i + 2)
        _plot_clustered_by_feature(markov_ts, seed, feature, ax, '({})'.format(name))
    _ = plt.xlabel('people')
    fig.savefig(path_to_plot)


def _convert_to_numerical_values(markov_ts):
    color_markov_ts = markov_ts.copy()
    color_markov_ts.replace(to_replace=ppl.Activity.NOT_AT_HOME, value=0, inplace=True)
    color_markov_ts.replace(to_replace=ppl.Activity.SLEEP_AT_HOME, value=0.5, inplace=True)
    color_markov_ts.replace(to_replace=ppl.Activity.HOME, value=1.0, inplace=True)
    return color_markov_ts


def _plot_heatmap(markov_ts, ax, name):
    sns.heatmap(
        gaussian_filter(markov_ts, sigma=GAUSSIAN_SIGMA),
        cmap=GREY_COLORMAP,
        cbar=False,
        ax=ax
    )
    _ = plt.xticks([])
    _ = plt.yticks([])
    _ = plt.ylabel(name)


def _plot_clustered_by_feature(markov_ts, seed, feature, ax, name):
    sorted_seed = seed.sort_values(by=str(feature))
    last_entries_in_group = sorted_seed.reset_index()\
        .groupby(str(feature)).last()[['SN1', 'SN2', 'SN3']]
    cluster_boundaries = [
        sorted_seed.reset_index()[
            (sorted_seed.reset_index().SN1 == last_entries_in_group.iloc[i, 0]) &
            (sorted_seed.reset_index().SN2 == last_entries_in_group.iloc[i, 1]) &
            (sorted_seed.reset_index().SN3 == last_entries_in_group.iloc[i, 2])].index.values[0]
        for i in range(len(last_entries_in_group))
    ]
    cluster_boundaries = pd.Series(cluster_boundaries)
    label_locations = (cluster_boundaries.shift().fillna(0) +
                       cluster_boundaries.diff().fillna(cluster_boundaries[0]) / 2)
    label_locations = label_locations.astype(np.int16)
    sorted_markov_ts = markov_ts.unstack(['SN1', 'SN2', 'SN3'])
    sorted_markov_ts.columns = sorted_markov_ts.columns.droplevel(0)
    sorted_markov_ts = sorted_markov_ts.reindex(columns=sorted_seed.index).dropna(axis=1)
    _plot_heatmap(sorted_markov_ts, ax, name)
    ax.vlines(
        cluster_boundaries,
        ymin=0, ymax=288,
        color='black',
        linewidth=2
    )


if __name__ == '__main__':
    population_cluster()
