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
@click.argument('path_to_thermal_power_plot')
@click.argument('path_to_choropleth_plot')
@click.argument('path_to_scatter_plot')
def plot_simulation_results(path_to_simulation_results, path_to_config,
                            path_to_thermal_power_plot, path_to_choropleth_plot,
                            path_to_scatter_plot):
    sns.set_context('paper')
    disk_engine = sqlalchemy.create_engine('sqlite:///{}'.format(path_to_simulation_results))
    dwellings = _read_dwellings(disk_engine)
    thermal_power = _read_thermal_power(disk_engine, dwellings)
    geo_data = _read_geo_data(uo.read_simulation_config(path_to_config), thermal_power)
    _plot_scatter(geo_data, path_to_scatter_plot)
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
    household_data = uo.census.read_household_type_data(config['spatial-resolution'])
    age_structure = uo.census.read_age_structure_data(config['spatial-resolution'])
    economic_activity_data = uo.census.read_economic_activity_data(config['spatial-resolution'])

    energy = thermal_power.copy()
    energy.value = energy.value * config['time-step-size'].total_seconds() / 1000 / 3600 # kWh
    duration = thermal_power.datetime.max() - thermal_power.datetime.min()
    if config['reweight-to-full-week']:
        print('Reweighting energy to full week. Make sure that is what you want.')
        energy = _reweight_energy(energy)
        duration = duration * 7 / 2
    energy_per_building = energy.groupby('dwelling_id').agg({'value': 'sum', 'region': 'first'})
    geo_data['average energy'] = (energy_per_building.groupby('region').value.mean() /
                                  duration.total_seconds() * ENERGY_TIME_SPAN.total_seconds())
    geo_data['standard deviation energy'] = (energy_per_building.groupby('region').value.std() /
                                             duration.total_seconds() *
                                             ENERGY_TIME_SPAN.total_seconds())
    geo_data['avg household size'] = age_structure.sum(axis=1) / household_data.sum(axis=1)
    geo_data['avg age'] = _mean_age(age_structure)
    geo_data['share economic active'] = _share_economic_active(economic_activity_data)
    return geo_data


def _reweight_energy(energy):
    weekend_mask = ((energy.set_index('datetime', drop=True).index.weekday == 5) |
                    (energy.set_index('datetime', drop=True).index.weekday == 6))
    weekday_mask = np.invert(weekend_mask)
    energy_re = energy.copy()
    energy_re.loc[weekend_mask, 'value'] = energy.loc[weekend_mask, 'value'] * 2
    energy_re.loc[weekday_mask, 'value'] = energy.loc[weekday_mask, 'value'] * 5
    return energy_re


AGE_MAP = {
    uo.types.AgeStructure.AGE_0_TO_4: 2.5,
    uo.types.AgeStructure.AGE_5_TO_7: 6.5,
    uo.types.AgeStructure.AGE_8_TO_9: 9,
    uo.types.AgeStructure.AGE_10_TO_14: 12.5,
    uo.types.AgeStructure.AGE_15: 15.5,
    uo.types.AgeStructure.AGE_16_TO_17: 17,
    uo.types.AgeStructure.AGE_18_TO_19: 19,
    uo.types.AgeStructure.AGE_20_TO_24: 22.5,
    uo.types.AgeStructure.AGE_25_TO_29: 27.5,
    uo.types.AgeStructure.AGE_30_TO_44: 37.5,
    uo.types.AgeStructure.AGE_45_TO_59: 52.5,
    uo.types.AgeStructure.AGE_60_TO_64: 62.5,
    uo.types.AgeStructure.AGE_65_TO_74: 70,
    uo.types.AgeStructure.AGE_75_TO_84: 80,
    uo.types.AgeStructure.AGE_85_TO_89: 87.5,
    uo.types.AgeStructure.AGE_90_AND_OVER: 95 # this is not correct, but shouldn't be a major impact
}


def _mean_age(age_structure):
    age_structure_num = age_structure.copy()
    for col in age_structure:
        age_structure_num[col] = age_structure[col] * AGE_MAP[col]
    return age_structure_num.sum(axis=1) / age_structure.sum(axis=1)


def _share_economic_active(economic_activity_data):
    total_active = economic_activity_data[[
        uo.types.EconomicActivity.EMPLOYEE_PART_TIME,
        uo.types.EconomicActivity.EMPLOYEE_FULL_TIME,
        uo.types.EconomicActivity.SELF_EMPLOYED,
        uo.types.EconomicActivity.ACTIVE_FULL_TIME_STUDENT
    ]].sum(axis=1)
    return total_active / economic_activity_data.sum(axis=1)


def _plot_thermal_power(thermal_power, path_to_plot):
    def _xTickFormatter(x, pos):
        return pd.to_datetime(x).time()
    fig = plt.figure(figsize=(8, 4), dpi=300)
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
    ax1.set_ylim(bottom=0)

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
    ax2.set_ylim(bottom=0)

    points_in_time = thermal_power.groupby('datetime').value.mean().index
    xtick_locations = [5, 5 + 144 // 2, 149, 149 + 144 // 2] # not sure why they are shifted
    ax2.set_xticks([points_in_time[x].timestamp() * 10e8 for x in xtick_locations])
    ax2.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(_xTickFormatter))

    ax1.label_outer()
    ax2.label_outer()

    fig.savefig(path_to_plot, dpi=300)


def _plot_choropleth(geo_data, path_to_choropleth):
    # The plot must be scaled, otherwise the legend will look weird. To bring
    # test sizes to a readable level, the seaborn context is set to poster.
    sns.set_context('poster')
    fig = plt.figure(figsize=(18, 4))
    ax = fig.add_subplot(121)
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
    ax.annotate('(a)', xy=[-0.15, 0.5], xycoords='axes fraction')

    ax = fig.add_subplot(122)
    gpdplt.plot_dataframe(
        geo_data,
        column='standard deviation energy',
        categorical=False,
        linewidth=0.2,
        legend=True,
        cmap='viridis',
        ax=ax
    )
    ax.set_aspect(1)
    _ = plt.xticks([])
    _ = plt.yticks([])
    ax.annotate('(b)', xy=[-0.15, 0.5], xycoords='axes fraction')

    fig.savefig(path_to_choropleth, dpi=300)
    sns.set_context('paper')


def _plot_scatter(geo_data, path_to_plot):
    plt.rcParams['figure.figsize'] = (8, 3)
    plt.rcParams['figure.dpi'] = 300
    geo_data = geo_data.rename(columns={
        'average energy': 'average energy [kWh/week]',
    })

    sns.pairplot(
        data=geo_data,
        y_vars=['average energy [kWh/week]'],
        x_vars=['avg household size', 'avg age', 'share economic active']
    )
    plt.savefig(path_to_plot, dpi=300)


if __name__ == '__main__':
    plot_simulation_results()
