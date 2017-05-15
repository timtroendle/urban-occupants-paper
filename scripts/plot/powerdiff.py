import click
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import sqlalchemy
import seaborn as sns


import urbanoccupants as uo


@click.command()
@click.argument('path_to_original_result')
@click.argument('name2')
@click.argument('path_to_result2')
@click.argument('name3')
@click.argument('path_to_result3')
@click.argument('name4')
@click.argument('path_to_result4')
@click.argument('path_to_plot')
def plot_diff(path_to_original_result, name2, path_to_result2, name3, path_to_result3,
              name4, path_to_result4, path_to_plot):
    """Plots the difference in thermal power of several simulation runs."""
    disk_engine = sqlalchemy.create_engine('sqlite:///{}'.format(path_to_original_result))
    dwellings = _read_dwellings(disk_engine)
    thermal_power_orig = _read_thermal_power(disk_engine, dwellings)
    disk_engine = sqlalchemy.create_engine('sqlite:///{}'.format(path_to_result2))
    dwellings = _read_dwellings(disk_engine)
    thermal_power2 = _read_thermal_power(disk_engine, dwellings)
    disk_engine = sqlalchemy.create_engine('sqlite:///{}'.format(path_to_result3))
    dwellings = _read_dwellings(disk_engine)
    thermal_power3 = _read_thermal_power(disk_engine, dwellings)
    disk_engine = sqlalchemy.create_engine('sqlite:///{}'.format(path_to_result4))
    dwellings = _read_dwellings(disk_engine)
    thermal_power4 = _read_thermal_power(disk_engine, dwellings)

    orig_groups = thermal_power_orig.groupby(['region', 'datetime'])
    orig_mean = orig_groups.value.mean()
    orig_std = orig_groups.value.std()
    diff = pd.concat([
        pd.DataFrame(index=orig_mean.index, data={
                     'mean': diff.groupby(['region', 'datetime']).value.mean() - orig_mean,
                     'std': diff.groupby(['region', 'datetime']).value.std() - orig_std,
                     'feature': name})
        for diff, name in zip([thermal_power2, thermal_power3, thermal_power4],
                              [name2, name3, name4])
    ])
    diff.reset_index(inplace=True)
    _plot_thermal_power_diff(diff, path_to_plot)


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


def _plot_thermal_power_diff(thermal_power, path_to_plot):
    def _xTickFormatter(x, pos):
        return pd.to_datetime(x).time()
    fig = plt.figure(figsize=(8, 4), dpi=300)
    ax1 = fig.add_subplot(2, 1, 1)
    sns.tsplot(
        data=thermal_power,
        time='datetime',
        unit='region',
        value='mean',
        condition='feature',
        err_style='unit_traces',
        ax=ax1
    )
    _ = plt.ylabel('average [W]')
    _ = plt.xlabel('')
    ax1.get_xaxis().set_visible(False)
    ax1.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
               ncol=2, mode="expand", borderaxespad=0.)

    ax2 = fig.add_subplot(2, 1, 2, sharex=ax1)
    sns.tsplot(
        data=thermal_power,
        time='datetime',
        unit='region',
        value='std',
        condition='feature',
        err_style='unit_traces',
        ax=ax2
    )
    _ = plt.ylabel('standard deviation [W]')
    _ = plt.xlabel('time of the day')
    ax2.legend().set_visible(False)

    points_in_time = thermal_power.groupby('datetime').feature.first().index
    xtick_locations = [5, 5 + 144 // 2, 149, 149 + 144 // 2] # not sure why they are shifted
    ax1.set_xticks([points_in_time[x].timestamp() * 10e8 for x in xtick_locations])
    ax1.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(_xTickFormatter))
    fig.savefig(path_to_plot, dpi=300)


if __name__ == '__main__':
    plot_diff()
