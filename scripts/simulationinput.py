from datetime import datetime, timedelta
from itertools import count, chain
import math
from multiprocessing import Pool, cpu_count
import os
from pathlib import Path
import random

import click
import pandas as pd
import yaml
from tqdm import tqdm
import requests_cache
import sqlalchemy

import urbanoccupants as uo

NUMBER_HOUSEHOLDS_HARINGEY = 101955
NUMBER_USUAL_RESIDENTS_HARINGEY = 254926
MARKOV_CHAIN_INDEX_TABLE_NAME = 'markovChains'
DWELLINGS_TABLE_NAME = 'dwellings'
PEOPLE_TABLE_NAME = 'people'
ENVIRONMENT_TABLE_NAME = 'environment'
PARAMETERS_TABLE_NAME = 'parameters'
ROOT_FOLDER = Path(os.path.abspath(__file__)).parent.parent
CACHE_PATH = ROOT_FOLDER / 'build' / 'web-cache'
MIDAS_DATABASE_PATH = ROOT_FOLDER / 'data' / 'Londhour.csv'
CACHE_PATH.mkdir(parents=True, exist_ok=True)
requests_cache.install_cache((CACHE_PATH).as_posix())


@click.command()
@click.argument('path_to_seed')
@click.argument('path_to_markov_ts')
@click.argument('path_to_settings')
@click.argument('path_to_result')
def simulation_input(path_to_seed, path_to_markov_ts, path_to_settings, path_to_result):
    _check_paths(path_to_seed, path_to_markov_ts, path_to_settings, path_to_result)
    seed = pd.read_pickle(path_to_seed)
    markov_ts = pd.read_pickle(path_to_markov_ts)
    settings = _read_settings(path_to_settings)
    features = settings['people-features'] + settings['household-features']
    seed, markov_ts = uo.tus.filter_features(seed, markov_ts, features + [uo.PeopleFeature.AGE])
    markov_chains = _create_markov_chains(
        seed,
        markov_ts,
        features,
        settings
    )
    seed = _amend_seed_by_markov_model(seed, markov_chains, features, settings['start-time'])
    seed = _amend_seed_by_metabolic_rate(seed, settings)
    census_data_ppl = {feature: feature.read_census_data(settings['spatial-resolution'])
                       for feature in settings['people-features']}
    for data in census_data_ppl.values():
        assert data.sum().sum() == NUMBER_USUAL_RESIDENTS_HARINGEY
    census_data_hh = {feature: feature.read_census_data(settings['spatial-resolution'])
                      for feature in settings['household-features']}
    for data in census_data_hh.values():
        assert data.sum().sum() == NUMBER_HOUSEHOLDS_HARINGEY
    seed = _prepare_seed_index(seed)
    households, citizens = _create_synthetic_population(
        seed,
        census_data_hh,
        census_data_ppl,
        settings
    )
    _write_dwellings_table(households, settings, path_to_result)
    _write_citizens_table(citizens, path_to_result)
    _write_markov_chains(markov_chains, path_to_result)
    _write_temperature_table(settings, path_to_result)
    _write_simulation_parameter_table(settings, path_to_result)


def _check_paths(path_to_seed, path_to_markov_ts, path_to_settings, path_to_result):
    if not Path(path_to_seed).exists():
        raise ValueError("Seed is missing: {}.".format(path_to_seed))
    if not Path(path_to_markov_ts).exists():
        raise ValueError("Markov timeseries is missing: {}.".format(path_to_markov_ts))
    if not Path(path_to_settings).exists():
        raise ValueError("Settings file is missing: {}.".format(path_to_settings))
    path_to_result = Path(path_to_result)
    if path_to_result.exists():
        path_to_result.unlink()
    if not MIDAS_DATABASE_PATH.exists():
        raise ValueError('MIDAS weather data file is missing: {}.'.format(MIDAS_DATABASE_PATH))


def _read_settings(path_to_settings):
    with open(path_to_settings, 'r') as settings_file:
        settings = yaml.load(settings_file)
    settings['people-features'] = [uo.PeopleFeature[feature]
                                   for feature in settings['people-features']]
    settings['household-features'] = [uo.HouseholdFeature[feature]
                                      for feature in settings['household-features']]
    settings['time-step-size'] = timedelta(minutes=settings['time-step-size-minutes'])
    settings['start-time'] = datetime.strptime(settings['start-time'], '%Y-%m-%d %H:%M')
    settings['spatial-resolution'] = uo.GeographicalLayer[settings['spatial-resolution']]
    return settings


def _create_markov_chains(seed, markov_ts, features, settings):
    seed_groups = seed.groupby([str(feature) for feature in features])
    print("Dividing the seed into {} cluster.".format(len(seed_groups.groups.keys())))
    print("Cluster statistics:")
    print(seed_groups.size().describe())

    with Pool(settings['number-processes']) as pool:
        feature_combinations = seed_groups.groups.keys()
        all_parameters = ( # imap_unordered allows only one parameter, hence the tuple
            (markov_ts,
             seed_groups.get_group(features),
             features,
             settings['time-step-size'])
            for features in feature_combinations
        )
        print('Calculating markov chains...')
        markov_chains = dict(pool.imap_unordered(uo.tus.markov_chain_for_cluster,
                             tqdm(all_parameters, total=len(feature_combinations))))
    return markov_chains


def _amend_seed_by_markov_model(seed, markov_chains, features, simulation_start_time):
    seed_groups = seed.groupby([str(feature) for feature in features])
    for feature_combination, index in seed_groups.groups.items():
        seed.loc[index, 'markov_id'] = uo.feature_id(feature_combination)
        seed.loc[index, 'initial_activity'] = markov_chains[feature_combination]\
            .valid_states(simulation_start_time)[0]
    return seed


def _amend_seed_by_metabolic_rate(seed, settings):
    below18 = seed[str(uo.PeopleFeature.AGE)] < uo.types.AgeStructure.AGE_18_TO_19
    above18 = seed[str(uo.PeopleFeature.AGE)] >= uo.types.AgeStructure.AGE_18_TO_19
    metabolic_heat_gain_active = settings['metabolic-heat-gain-active']
    metabolic_heat_gain_passive = settings['metabolic-heat-gain-passive']
    metabolic_ratio_child = settings['metabolic-ratio-child']
    seed.loc[below18, 'metabolic_heat_gain_active'] = (metabolic_heat_gain_active *
                                                       metabolic_ratio_child)
    seed.loc[below18, 'metabolic_heat_gain_passive'] = (metabolic_heat_gain_passive *
                                                        metabolic_ratio_child)
    seed.loc[above18, 'metabolic_heat_gain_active'] = metabolic_heat_gain_active
    seed.loc[above18, 'metabolic_heat_gain_passive'] = metabolic_heat_gain_passive
    return seed


def _prepare_seed_index(seed):
    sn1_plus_sn2 = seed.index.droplevel(2)
    seed = seed.copy()
    seed['household_id'] = list(sn1_plus_sn2)
    seed.reset_index(inplace=True)
    seed.rename(columns={'SN3': 'person_id'}, inplace=True)
    seed.set_index(['household_id', 'person_id'], inplace=True)
    seed.drop(['SN1', 'SN2'], axis=1, inplace=True)
    return seed


def _create_synthetic_population(seed, census_data_hh, census_data_ppl, settings):
    random_hh_feature = list(census_data_hh.values())[0]
    regions = list(random_hh_feature.index)
    controls_hh = {region: {str(feature): census_data_hh[feature].ix[region, :]
                            for feature in settings['household-features']}
                   for region in regions}
    controls_ppl = {region: {str(feature): census_data_ppl[feature].ix[region, :]
                             for feature in settings['people-features']}
                    for region in regions}
    number_households = {region: random_hh_feature.ix[region, :].sum() for region in regions}
    household_counter = count(start=1, step=1)
    household_ids = {region: [household_counter.__next__()
                              for _ in range(number_households[region])]
                     for region in regions}
    random_numbers = {region: [random.uniform(0, 1) for _ in range(number_households[region])]
                      for region in regions}
    hh_chunk_size = int(NUMBER_HOUSEHOLDS_HARINGEY / settings['number-processes'] / 4)

    with Pool(settings['number-processes']) as pool:
        print('Hierarchical iterative proportional fitting...')
        hipf_params = ((seed, controls_hh[region], controls_ppl[region], region)
                       for region in regions)
        household_weights = dict(tqdm(
            pool.imap_unordered(uo.synthpop.run_hipf, hipf_params),
            total=len(regions)
        ))
        print('Sampling households...')
        household_params = ((region, seed, household_weights[region],
                             random_numbers[region], household_ids[region])
                            for region in regions)
        households = list(chain(*tqdm(
            pool.imap_unordered(uo.synthpop.sample_households, household_params),
            total=len(regions)
        )))
        print('Sampling individuals...')
        household_chunks = [households[i:i + hh_chunk_size]
                            for i in range(0, len(households), hh_chunk_size)]
        citizens = list(chain(*tqdm(
            pool.imap_unordered(
                uo.synthpop.sample_citizen,
                ((households, seed) for households in household_chunks)
            ),
            total=math.ceil(NUMBER_HOUSEHOLDS_HARINGEY / hh_chunk_size)
        )))

    assert len(households) == NUMBER_HOUSEHOLDS_HARINGEY
    assert abs(len(citizens) - NUMBER_USUAL_RESIDENTS_HARINGEY) < 1000
    return households, citizens


def _df_to_input_db(df, table_name, path_to_db):
    disk_engine = sqlalchemy.create_engine('sqlite:///{}'.format(path_to_db))
    df.to_sql(name=table_name, con=disk_engine)


def _write_dwellings_table(households, settings, path_to_db):
    df = pd.DataFrame(
        index=[household.id for household in households],
        data={
            'heatMassCapacity': settings['heat-mass-capacity'],
            'heatTransmission': settings['heat-transmission'],
            'maxHeatingPower': settings['max-heating-power'],
            'initialTemperature': settings['initial-temperature'],
            'conditionedFloorArea': settings['conditioned-floor-area'],
            'heatingControlStrategy': settings['heating-control-strategy'],
            'region': [household.region for household in households]
        }
    )
    _df_to_input_db(df, DWELLINGS_TABLE_NAME, path_to_db)


def _write_citizens_table(citizens, path_to_db):
    df = pd.DataFrame(
        index=list(range(len(citizens))),
        data={
            'markovChainId': [citizen.markovId for citizen in citizens],
            'dwellingId': [citizen.householdId for citizen in citizens],
            'initialActivity': [str(citizen.initialActivity) for citizen in citizens],
            'activeMetabolicRate': [citizen.activeMetabolicRate for citizen in citizens],
            'passiveMetabolicRate': [citizen.passiveMetabolicRate for citizen in citizens],
            'randomSeed': [citizen.randomSeed for citizen in citizens]
        }
    )
    _df_to_input_db(df, PEOPLE_TABLE_NAME, path_to_db)


def _write_markov_chains(markov_chains, path_to_db):
    markov_index = pd.Series(
        {
            feature_id: "markov{}".format(feature_id)
            for feature_id in [uo.feature_id(key) for key in markov_chains.keys()]
        },
        name='tablename'
    )
    _df_to_input_db(markov_index, MARKOV_CHAIN_INDEX_TABLE_NAME, path_to_db)
    for feature_combination, markov_chain in markov_chains.items():
        df = markov_chain.to_dataframe()
        df.fromActivity = [str(x) for x in df.fromActivity]
        df.toActivity = [str(x) for x in df.toActivity]
        _df_to_input_db(df, markov_index[uo.feature_id(feature_combination)], path_to_db)


def _write_temperature_table(settings, path_to_db):
    def date_parser(date, time):
        month, day, year = [int(x) for x in date.split('/')]
        hour, minute = [int(x) for x in time.split(':')]
        return datetime(year, month, day, hour - 1, minute)

    temperature = pd.read_csv(
        MIDAS_DATABASE_PATH,
        skiprows=[0],
        header=0,
        parse_dates=[['Date (MM/DD/YYYY)', 'Time (HH:MM)']],
        date_parser=date_parser,
        index_col=[0]
    )
    temperature.rename(columns={'Dry-bulb (C)': 'temperature'}, inplace=True)
    temperature.index.name = 'index'
    df = temperature['temperature'].resample(settings['time-step-size']).ffill()
    _df_to_input_db(df, ENVIRONMENT_TABLE_NAME, path_to_db)


def _write_simulation_parameter_table(settings, path_to_db):
    _df_to_input_db(
        table_name=PARAMETERS_TABLE_NAME,
        df=pd.DataFrame(
            index=[1],
            data={
                'initialDatetime': settings['start-time'],
                'timeStepSize_in_min': settings['time-step-size-minutes'],
                'numberTimeSteps': settings['number-time-steps'],
                'setPointWhileHome': settings['set-point-while-home'],
                'setPointWhileAsleep': settings['set-point-while-asleep'],
                'wakeUpTime': settings['wake-up-time'],
                'leaveHomeTime': settings['leave-home-time'],
                'comeHomeTime': settings['come-home-time'],
                'bedTime': settings['bed-time']
            }
        ),
        path_to_db=path_to_db
    )


if __name__ == '__main__':
    simulation_input()
