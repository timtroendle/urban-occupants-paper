from datetime import timedelta, datetime

import yaml

from . import PeopleFeature, HouseholdFeature, GeographicalLayer


def read_simulation_config(path_to_settings):
    """Reads a simulation config file."""
    with open(path_to_settings, 'r') as settings_file:
        settings = yaml.load(settings_file)
    settings['people-features'] = [PeopleFeature[feature]
                                   for feature in settings['people-features']]
    settings['household-features'] = [HouseholdFeature[feature]
                                      for feature in settings['household-features']]
    settings['time-step-size'] = timedelta(minutes=settings['time-step-size-minutes'])
    settings['start-time'] = datetime.strptime(settings['start-time'], '%Y-%m-%d %H:%M')
    settings['spatial-resolution'] = GeographicalLayer[settings['spatial-resolution']]
    for time_str in ['wake-up-time', 'leave-home-time', 'come-home-time', 'bed-time']:
        settings[time_str] = datetime.strptime(settings[time_str], '%H:%M').time()
    return settings
