import os
from pathlib import Path

import click
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
import pandas as pd
import sqlalchemy
import requests_cache

import urbanoccupants as uo
import geopandasplotting as gpdplt
ROOT_FOLDER = Path(os.path.abspath(__file__)).parent.parent.parent
CACHE_PATH = ROOT_FOLDER / 'build' / 'web-cache'
requests_cache.install_cache((CACHE_PATH).as_posix())


@click.command()
@click.argument('path_to_simulation_results')
@click.argument('path_to_config')
@click.argument('path_to_thermal_power_plot')
@click.argument('path_to_choropleth_plot')
def plot_simulation_results(path_to_simulation_results, path_to_config,
                            path_to_thermal_power_plot, path_to_choropleth_plot):
    disk_engine = sqlalchemy.create_engine('sqlite:///{}'.format(path_to_simulation_results))
    dwellings = _read_dwellings(disk_engine)
    thermal_power = _read_thermal_power(disk_engine, dwellings)
    geo_data = _read_geo_data(uo.read_simulation_config(path_to_config), thermal_power)
    _plot_choropleth(geo_data, path_to_choropleth_plot)
    _plot_thermal_power(thermal_power, path_to_thermal_power_plot)


def _read_dwellings(disk_engine):
    dwellings = pd.read_sql_query(
        'SELECT * FROM {}'.format(uo.DWELLINGS_TABLE_NAME),
        disk_engine,
        index_col='index'
    )
    people = pd.read_sql_query(
        'SELECT * FROM {}'.format(uo.PEOPLE_TABLE_NAME),
        disk_engine,
        index_col='index'
    )
    dwellings['householdSize'] = people.groupby('dwellingId').size()
    return dwellings


def _read_thermal_power(disk_engine, dwellings):
    dwellingId_to_region = {dwellingId: dwellings.loc[dwellingId, 'region']
                            for dwellingId in dwellings.index}
    thermal_power = pd.read_sql_query(
        'SELECT * FROM thermalPower',
        disk_engine,
        index_col='timestamp',
        parse_dates=True
    )
    thermal_power.index = pd.to_datetime(thermal_power.index * 1000 * 1000)
    thermal_power.index.name = 'datetime'
    thermal_power.rename(columns={'id': 'dwelling_id'}, inplace=True)
    thermal_power['region'] = thermal_power.dwelling_id.map(dwellingId_to_region)
    return thermal_power.reset_index()


def _read_geo_data(config, thermal_power):
    geo_data = uo.census.read_haringey_shape_file(config['spatial-resolution'])
    geo_data['average_power'] = thermal_power.groupby('region').value.mean()
    return geo_data


def _plot_thermal_power(thermal_power, path_to_plot):
    def _xTickFormatter(x, pos):
        return pd.to_datetime(x).time()
    fig = plt.figure(figsize=(14, 7))
    ax1 = fig.add_subplot(2, 1, 1)
    sns.tsplot(
        data=thermal_power.groupby(['datetime', 'region']).value.mean().reset_index(),
        time='datetime',
        unit='region',
        value='value',
        err_style='unit_traces',
        ax=ax1
    )
    _ = plt.ylabel('average [W]')
    _ = plt.xlabel('')

    ax2 = fig.add_subplot(2, 1, 2, sharex=ax1)
    sns.tsplot(
        data=thermal_power.groupby(['datetime', 'region']).value.std().reset_index(),
        time='datetime',
        unit='region',
        value='value',
        err_style='unit_traces',
        ax=ax2
    )
    _ = plt.ylabel('standard deviation [W]')
    _ = plt.xlabel('time of the day')
    ax1.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(_xTickFormatter))
    fig.savefig(path_to_plot)


def _plot_choropleth(geo_data, path_to_choropleth):
    ax = gpdplt.plot_dataframe(
        geo_data,
        column='average_power',
        categorical=False,
        linewidth=0.2,
        legend=True,
        figsize=(14, 7),
        cmap='viridis'
    )
    _ = plt.xticks([])
    _ = plt.yticks([])
    fig = ax.get_figure()
    fig.savefig(path_to_choropleth)


if __name__ == '__main__':
    plot_simulation_results()
