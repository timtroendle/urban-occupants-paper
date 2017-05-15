import click
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from scipy.ndimage.filters import gaussian_filter
import pandas as pd
import numpy as np
import string
from itertools import cycle

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
    sns.set_context('paper')
    fig = plt.figure(figsize=(8, 4), dpi=300)
    ax = fig.add_subplot(len(ALL_FEATURES) + 1, 1, 1)
    _plot_heatmap(markov_ts.unstack(['SN1', 'SN2', 'SN3']), ax)
    for i, feature in enumerate(ALL_FEATURES):
        ax = fig.add_subplot(len(ALL_FEATURES) + 1, 1, i + 2)
        _plot_clustered_by_feature(markov_ts, seed, feature, ax)
    _ = plt.xlabel('people')
    _label_axes(
        fig,
        ha='left',
        loc=(-0.075, 0.5), labels=['({})'.format(letter) for letter in string.ascii_lowercase]
    )
    fig.savefig(path_to_plot, dpi=300)


def _convert_to_numerical_values(markov_ts):
    color_markov_ts = markov_ts.copy()
    color_markov_ts.replace(to_replace=uo.Activity.NOT_AT_HOME, value=0, inplace=True)
    color_markov_ts.replace(to_replace=uo.Activity.SLEEP_AT_HOME, value=0.5, inplace=True)
    color_markov_ts.replace(to_replace=uo.Activity.HOME, value=1.0, inplace=True)
    return color_markov_ts


def _plot_heatmap(markov_ts, ax):
    sns.heatmap(
        gaussian_filter(markov_ts, sigma=GAUSSIAN_SIGMA),
        cmap=GREY_COLORMAP,
        cbar=False,
        ax=ax
    )
    _ = plt.xticks([])
    _ = plt.yticks([])
    _ = plt.ylabel('time of the day')


def _plot_clustered_by_feature(markov_ts, seed, feature, ax):
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
    _plot_heatmap(sorted_markov_ts, ax)
    ax.vlines(
        cluster_boundaries,
        ymin=0, ymax=288,
        color='black',
        linewidth=1.0
    )


def _label_axes(fig, labels=None, loc=None, **kwargs):
    """
    Walks through axes and labels each.

    kwargs are collected and passed to `annotate`

    Parameters
    ----------
    fig : Figure
         Figure object to work on

    labels : iterable or None
        iterable of strings to use to label the axes.
        If None, lower case letters are used.

    loc : len=2 tuple of floats
        Where to put the label in axes-fraction units
    """
    # from http://stackoverflow.com/a/22509497/1856079
    if labels is None:
        labels = string.ascii_lowercase

    # re-use labels rather than stop labeling
    labels = cycle(labels)
    if loc is None:
        loc = (.9, .9)
    for ax, lab in zip(fig.axes, labels):
        ax.annotate(lab, xy=loc,
                    xycoords='axes fraction',
                    **kwargs)


if __name__ == '__main__':
    population_cluster()
