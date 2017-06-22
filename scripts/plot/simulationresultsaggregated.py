import os
from pathlib import Path
from datetime import timedelta

import click
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
import pandas as pd
import numpy as np
import sqlalchemy
import requests_cache

import urbanoccupants as uo
import geopandasplotting as gpdplt
ROOT_FOLDER = Path(os.path.abspath(__file__)).parent.parent.parent
CACHE_PATH = ROOT_FOLDER / 'build' / 'web-cache'
requests_cache.install_cache((CACHE_PATH).as_posix())

ENERGY_TIME_SPAN = timedelta(days=7) # energy will be reported as kWh per timespan, e.g kWh per week


@click.command()
@click.argument('path_to_simulation_results')
@click.argument('path_to_config')
@click.argument('path_to_choropleth_plot')
def plot_simulation_results(path_to_simulation_results, path_to_config,
                            path_to_choropleth_plot):
    sns.set_context('paper')
    disk_engine = sqlalchemy.create_engine('sqlite:///{}'.format(path_to_simulation_results))
    thermal_power = _read_average_thermal_power(disk_engine)
    geo_data = _read_geo_data(uo.read_simulation_config(path_to_config), thermal_power)
    _plot_choropleth(geo_data, path_to_choropleth_plot)


def _read_average_thermal_power(disk_engine):
    thermal_power = pd.read_sql_query(
        'SELECT * FROM averageThermalPower',
        disk_engine,
        index_col='timestamp',
        parse_dates=True
    )
    thermal_power.index = pd.to_datetime(thermal_power.index * 1000 * 1000)
    thermal_power.index.name = 'datetime'
    thermal_power['region'] = thermal_power.id.map(_district_id_int_to_str)
    return thermal_power.reset_index()


def _district_id_int_to_str(district_id_int):
    as_string = list(str(district_id_int))
    as_string[0] = 'E'
    return "".join(as_string)


def _read_geo_data(config, thermal_power):
    geo_data = uo.census.read_shape_file(config['study-area'], config['spatial-resolution'])

    energy = thermal_power.copy()
    energy.value = energy.value * config['time-step-size'].total_seconds() / 1000 / 3600 # kWh
    duration = thermal_power.datetime.max() - thermal_power.datetime.min()
    if config['reweight-to-full-week']:
        print('Reweighting energy to full week. Make sure that is what you want.')
        energy = _reweight_energy(energy)
        duration = duration * 7 / 2
    geo_data['average energy'] = (energy.groupby('region').value.sum() /
                                  duration.total_seconds() * ENERGY_TIME_SPAN.total_seconds())
    return geo_data


def _reweight_energy(energy):
    weekend_mask = ((energy.set_index('datetime', drop=True).index.weekday == 5) |
                    (energy.set_index('datetime', drop=True).index.weekday == 6))
    weekday_mask = np.invert(weekend_mask)
    energy_re = energy.copy()
    energy_re.loc[weekend_mask, 'value'] = energy.loc[weekend_mask, 'value'] * 2
    energy_re.loc[weekday_mask, 'value'] = energy.loc[weekday_mask, 'value'] * 5
    return energy_re


def _plot_choropleth(geo_data, path_to_choropleth):
    # The plot must be scaled, otherwise the legend will look weird. To bring
    # test sizes to a readable level, the seaborn context is set to poster.
    sns.set_context('poster')
    fig = plt.figure(figsize=(18, 8))
    ax = fig.add_subplot(111)
    gpdplt.plot_dataframe(
        geo_data,
        column='average energy',
        categorical=False,
        linewidth=0.2,
        legend=True,
        cmap='viridis',
        ax=ax
    )
    ax.set_aspect(1)
    _ = plt.xticks([])
    _ = plt.yticks([])

    fig.savefig(path_to_choropleth, dpi=300)
    sns.set_context('paper')


if __name__ == '__main__':
    plot_simulation_results()
