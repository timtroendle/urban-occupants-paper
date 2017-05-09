import click
import pytus2000
import people as ppl
import pandas as pd
import numpy as np

from urbanoccupants.tus import Activity, Location, ACTIVITY_MAP, LOCATION_MAP

EXPECTED_NUMBER_OF_DIARY_ENTRIES = 2 * 24 * 6


@click.command()
@click.argument('path_to_input')
@click.argument('path_to_output')
def read_markov_ts(path_to_input, path_to_output):
    """Reads, transforms, and filters the diary data from the TUS data set.

    The raw data is mapped to occupancy states of this study. Missing entries are
    forwards filled were possible; diaries containing nan's thereafter are dropped.
    Individuals are dropped if there aren't noth diaries available, one for the
    weekday, and one for the weekend day.

    Output is written in plain pickle format.
    """
    diary_data = _read_diary_data(path_to_input)
    diary_data_ts = _read_diary_data_as_timeseries(path_to_input)
    markov_ts = _transform_to_markov_timeseries(diary_data_ts)
    print("Read diaries for {} individuals.".format(_number_individiuals(markov_ts)))
    markov_ts = _ffill_nan(markov_ts)
    markov_ts = _drop_nan(markov_ts)
    assert not markov_ts.isnull().any().any()
    markov_ts = _remove_individuals_with_less_than_two_diaries(markov_ts)
    markov_ts = _add_daytype(diary_data, markov_ts)
    print("Writing diaries for {} individuals.".format(_number_individiuals(markov_ts)))
    markov_ts.to_pickle(path_to_output)


def _number_individiuals(markov_ts):
    return markov_ts.reset_index().groupby(['SN1', 'SN2', 'SN3']).size().shape[0]


def _read_diary_data(input_file_path):
    return pytus2000.read_diary_file(input_file_path)


def _read_diary_data_as_timeseries(input_file_path):
    return pytus2000.read_diary_file_as_timeseries(input_file_path)[['activity', 'location']]


def _transform_to_markov_timeseries(diary_data_ts):
    simple_ts = pd.DataFrame({
        'location': diary_data_ts.location.map(LOCATION_MAP),
        'activity': diary_data_ts.activity.map(ACTIVITY_MAP)
    })
    markov_ts = pd.Series(index=simple_ts.index, dtype='category')
    markov_ts.cat.add_categories([state for state in ppl.Activity], inplace=True)
    mask_home = ((simple_ts.location == Location.HOME) &
                 (simple_ts.activity != Activity.SLEEP))
    mask_sleep = (((simple_ts.location == Location.HOME) |
                   (simple_ts.location == Location.IMPLICIT)) &
                  (simple_ts.activity == Activity.SLEEP))
    mask_nan = pd.isnull(simple_ts.location) | pd.isnull(simple_ts.activity)
    markov_ts[:] = ppl.Activity.NOT_AT_HOME
    markov_ts[mask_home] = ppl.Activity.HOME
    markov_ts[mask_sleep] = ppl.Activity.SLEEP_AT_HOME
    markov_ts[mask_nan] = np.nan
    return markov_ts


def _ffill_nan(markov_ts):
    # Unknowns will be filled by forward fill. That is, whenever a state is unknown it is
    # expected that the last known state is still valid.

    # When doing that, it is important to not forward fill between diaries (all diaries are
    # below each other). Hence, they must be grouped into diaries first and then forward filled.
    # This will lead to the fact that not all Unknowns can be filled (the ones at the beginning
    # of the day), but that is wanted.
    n_missing = markov_ts.isnull().sum()
    print("{:.2f}% of the diary entries are missing and will be forward filled."
          .format(n_missing / markov_ts.shape[0] * 100))
    markov_ts = markov_ts.groupby([markov_ts.index.get_level_values('SN1'),
                                   markov_ts.index.get_level_values('SN2'),
                                   markov_ts.index.get_level_values('SN3'),
                                   markov_ts.index.get_level_values('SN4')]).fillna(method='ffill')
    return markov_ts


def _drop_nan(markov_ts):
    # Remove all diaries with at least one NaN.
    n_missing = markov_ts.isnull().sum()
    print("{:.2f}% of the diary entries are still missing and their diaries will be dropped."
          .format(n_missing / markov_ts.shape[0] * 100))
    nan_mask = markov_ts.groupby(by=lambda index: (index[0], index[1], index[2], index[3]))\
        .apply(lambda values: values.isnull().any())
    return pd.DataFrame(markov_ts)[markov_ts.index.droplevel('time_of_day')
                                   .isin(nan_mask[~nan_mask].index)]


def _remove_individuals_with_less_than_two_diaries(markov_ts):
    valid_mask = markov_ts.groupby([markov_ts.index.get_level_values('SN1'),
                                    markov_ts.index.get_level_values('SN2'),
                                    markov_ts.index.get_level_values('SN3')])\
        .apply(lambda values: len(values) == EXPECTED_NUMBER_OF_DIARY_ENTRIES)
    print('{} individuals have less than two diaries and will be removed.'
          .format(valid_mask.shape[0] - valid_mask.sum()))
    return markov_ts[markov_ts.index.droplevel(['SN4', 'time_of_day'])
                     .isin(valid_mask[valid_mask].index)]


def _add_daytype(diary_data, markov_ts):
    weekdays = diary_data[diary_data.DDAYW2 == pytus2000.diary.DDAYW2.WEEKDAY_MON___FRI]
    markov_ts['daytype'] = 'weekend'
    markov_ts.loc[markov_ts.index.droplevel('time_of_day').isin(weekdays.index), 'daytype'] =\
        'weekday'
    markov_ts = markov_ts.reset_index(level=['SN4', 'time_of_day'])\
        .set_index(['daytype', 'time_of_day'], append=True)
    return markov_ts.drop('SN4', axis=1)


if __name__ == '__main__':
    read_markov_ts()
