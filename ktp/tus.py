"""Functions and mapping for the UK Time Use Study 2000 data.

The mappings bring the data into categories that are used in this study. Typically
that means the number of categories is reduces vastly.
"""
from enum import Enum

import numpy as np
import pandas as pd

from pytus2000 import diary, individual
import people as ppl
from .types import EconomicActivity, Qualification, HouseholdType


def markov_chain_for_cluster(param_tuple):
    """Creating a heterogenous markov chain for a cluster of the TUS sample.

    This function is intened to be used with `multiprocessing.imap_unordered` which allows
    only one parameter, hence the inconvenient tuple parameter design.

    Parameters:
        * param_tuple(0): time series for all people, with index (SN1, SN2, SN3, SN4, timeofday)
        * param_tuple(1): a subset of the individual data set representing the cluster for which
                          the markov chain should be created, with index (SN1, SN2, SN3)
        * param_tuple(2): the tuple of people features representing the cluster, this is not used
                          in this function, but only passed through
        * param_tuple(3): a subset of the diary data set representing weekdays, with index
                          (SN1, SN2, SN3, SN4)
        * param_tuple(4): a subset of the diary data set representing weekend days, with index
                          (SN1, SN2, SN3, SN4)
        * param_tuple(5): the time step size of the markov chain, a datetime.timedelta object

    Returns:
        a tuple of
            * param_tuple(2)
            * the heterogeneous markov chain for the cluster
    """
    markov_ts, group_of_people, features, weekdays, weekenddays, time_step_size = param_tuple
    # filter by people
    people_mask = markov_ts.index.droplevel([3, 4]).isin(group_of_people.index)
    filtered_markov = pd.DataFrame(markov_ts)[people_mask]
    # filter by weekday
    weekday_mask = filtered_markov.index.droplevel([4]).isin(weekdays.index)
    filtered_markov_weekday = filtered_markov[weekday_mask]
    # filter by weekend
    weekend_mask = filtered_markov.index.droplevel([4]).isin(weekenddays.index)
    filtered_markov_weekend = filtered_markov[weekend_mask]
    return features, ppl.WeekMarkovChain(
        weekday_time_series=filtered_markov_weekday.unstack(level=[0, 1, 2, 3]),
        weekend_time_series=filtered_markov_weekend.unstack(level=[0, 1, 2, 3]),
        time_step_size=time_step_size
    )


class Location(Enum):
    """Simplified TUS 2000 locations."""
    HOME = 1
    OTHER_HOME = 2
    WORK_OR_SCHOOL = 3
    RESTO = 4
    SPORTS_FACILITY = 5
    ARTS_OR_CULTURAL_CENTRE = 6
    OUTSIDE = 7
    TRAVELLING = 8
    UNKNOWN = 9
    IMPLICIT = 10


class Activity(Enum):
    """Simplified TUS 2000 activities."""
    SLEEP = 1
    WORK_OR_STUDY = 2
    OTHER = 3
    UNKNOWN = 4


def from_simplified_location_and_activity_to_people_model(df):
    markov_states = pd.Series(index=df.index, dtype='category')
    markov_states.cat.add_categories([state for state in ppl.Activity], inplace=True)
    mask_home = (df.location == Location.HOME) & (df.activity != Activity.SLEEP)
    mask_sleep = (((df.location == Location.HOME) | (df.location == Location.IMPLICIT)) &
                  (df.activity == Activity.SLEEP))
    mask_other_home = (df.location == Location.OTHER_HOME) & (df.activity != Activity.SLEEP)
    mask_sleep_other_home = (df.location == Location.OTHER_HOME) & (df.activity == Activity.SLEEP)
    mask_not_at_home = ((df.location != Location.HOME) &
                        (df.location != Location.OTHER_HOME) &
                        (df.activity != Activity.SLEEP))
    mask_nan = pd.isnull(df.location) | pd.isnull(df.activity)
    markov_states[mask_home] = ppl.Activity.HOME
    markov_states[mask_sleep] = ppl.Activity.SLEEP_AT_HOME
    markov_states[mask_other_home] = ppl.Activity.OTHER_HOME
    markov_states[mask_sleep_other_home] = ppl.Activity.SLEEP_AT_OTHER_HOME
    markov_states[mask_not_at_home] = ppl.Activity.NOT_AT_HOME
    markov_states[mask_nan] = np.nan
    return markov_states


LOCATION_MAP = {
    diary.WHER_001.MAIN_ACTVTY_EQUAL_SLEEPWORKSTUDY___NO_CODE_REQUIRED: Location.IMPLICIT,
    diary.WHER_001._MISSING: Location.UNKNOWN,
    diary.WHER_001.MISSING2: Location.UNKNOWN,
    diary.WHER_001._UNSPECIFIED_LOCATION: Location.UNKNOWN,
    diary.WHER_001._UNSPECIFIED_LOCATION_NOT_TRAVELLING: Location.UNKNOWN,
    diary.WHER_001._HOME: Location.HOME,
    diary.WHER_001._SECOND_HOME_OR_WEEKEND_HOUSE: Location.OTHER_HOME,
    diary.WHER_001._WORKING_PLACE_OR_SCHOOL: Location.WORK_OR_SCHOOL,
    diary.WHER_001._OTHER_PEOPLE_S_HOME: Location.OTHER_HOME,
    diary.WHER_001._RESTAURANT__CAFÉ_OR_PUB: Location.RESTO,
    diary.WHER_001._SPORTS_FACILITY: Location.SPORTS_FACILITY,
    diary.WHER_001._WHER_001__ARTS_OR_CULTURAL_CENTRE: Location.ARTS_OR_CULTURAL_CENTRE,
    diary.WHER_001._THE_COUNTRY_COUNTRYSIDE__SEASIDE__BEACH_OR_COAST: Location.OUTSIDE,
    diary.WHER_001._OTHER_SPECIFIED_LOCATION_NOT_TRAVELLING: Location.UNKNOWN,
    diary.WHER_001._UNSPECIFIED_PRIVATE_TRANSPORT_MODE: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_ON_FOOT: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_BY_BICYCLE: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_BY_MOPED__MOTORCYCLE_OR_MOTORBOAT: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_BY_PASSENGER_CAR_AS_THE_DRIVER: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_BY_PASSENGER_CAR_AS_A_PASSENGER: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_BY_PASSENGER_CAR_DRIVER_STATUS_UNSPECIFIED: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_BY_LORRY__OR_TRACTOR: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_BY_VAN: Location.TRAVELLING,
    diary.WHER_001._OTHER_SPECIFIED_PRIVATE_TRAVELLING_MODE: Location.TRAVELLING,
    diary.WHER_001._UNSPECIFIED_PUBLIC_TRANSPORT_MODE: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_BY_TAXI: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_BY_BUS: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_BY_TRAM_OR_UNDERGROUND: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_BY_TRAIN: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_BY_AEROPLANE: Location.TRAVELLING,
    diary.WHER_001._TRAVELLING_BY_BOAT_OR_SHIP: Location.TRAVELLING,
    diary.WHER_001._WHER_001__TRAVELLING_BY_COACH: Location.TRAVELLING,
    diary.WHER_001._WAITING_FOR_PUBLIC_TRANSPORT: Location.TRAVELLING,
    diary.WHER_001._OTHER_SPECIFIED_PUBLIC_TRANSPORT_MODE: Location.TRAVELLING,
    diary.WHER_001._UNSPECIFIED_TRANSPORT_MODE: Location.TRAVELLING,
    diary.WHER_001._ILLEGIBLE_LOCATION_OR_TRANSPORT_MODE: Location.UNKNOWN
}


ACTIVITY_MAP = {
    diary.ACT1_001.UNSPECIFIED_PERSONAL_CARE: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_SLEEP: Activity.SLEEP,
    diary.ACT1_001.SLEEP: Activity.SLEEP,
    diary.ACT1_001.SICK_IN_BED: Activity.SLEEP,
    diary.ACT1_001.EATING: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_OTHER_PERSONAL_CARE: Activity.OTHER,
    diary.ACT1_001.WASH_AND_DRESS: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_PERSONAL_CARE: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_EMPLOYMENT: Activity.WORK_OR_STUDY,
    diary.ACT1_001.WORKING_TIME_IN_MAIN_JOB: Activity.WORK_OR_STUDY,
    diary.ACT1_001.COFFEE_AND_OTHER_BREAKS_IN_MAIN_JOB: Activity.OTHER,
    diary.ACT1_001.WORKING_TIME_IN_SECOND_JOB: Activity.WORK_OR_STUDY,
    diary.ACT1_001.COFFEE_AND_OTHER_BREAKS_IN_SECOND_JOB: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_ACTIVITIES_RELATED_TO_EMPLOYMENT: Activity.WORK_OR_STUDY,
    diary.ACT1_001.LUNCH_BREAK: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_ACTIVITIES_RELATED_TO_EMPLOYMENT: Activity.WORK_OR_STUDY,
    diary.ACT1_001.ACTIVITIES_RELATED_TO_JOB_SEEKING: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_ACTIVITIES_RELATED_TO_EMPLOYMENT2: Activity.WORK_OR_STUDY,
    diary.ACT1_001.UNSPECIFIED_STUDY: Activity.WORK_OR_STUDY,
    diary.ACT1_001.UNSPECIFIED_ACTIVITIES_RELATED_TO_SCHOOL_OR_UNIVERSITY: Activity.WORK_OR_STUDY,
    diary.ACT1_001.CLASSES_AND_LECTURES: Activity.WORK_OR_STUDY,
    diary.ACT1_001.HOMEWORK: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_ACTIVITIES_RELATED_TO_SCHOOL_OR_UNIVERSITY:
        Activity.WORK_OR_STUDY,
    diary.ACT1_001.FREE_TIME_STUDY: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_HOUSEHOLD_AND_FAMILY_CARE: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_FOOD_MANAGEMENT: Activity.OTHER,
    diary.ACT1_001.FOOD_PREPARATION: Activity.OTHER,
    diary.ACT1_001.BAKING: Activity.OTHER,
    diary.ACT1_001.DISH_WASHING: Activity.OTHER,
    diary.ACT1_001.PRESERVING: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_FOOD_MANAGEMENT: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_HOUSEHOLD_UPKEEP: Activity.OTHER,
    diary.ACT1_001.CLEANING_DWELLING: Activity.OTHER,
    diary.ACT1_001.CLEANING_YARD: Activity.OTHER,
    diary.ACT1_001.HEATING_AND_WATER: Activity.OTHER,
    diary.ACT1_001.VARIOUS_ARRANGEMENTS: Activity.OTHER,
    diary.ACT1_001.DISPOSAL_OF_WASTE: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_HOUSEHOLD_UPKEEP: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_MAKING_AND_CARE_FOR_TEXTILES: Activity.OTHER,
    diary.ACT1_001.LAUNDRY: Activity.OTHER,
    diary.ACT1_001.IRONING: Activity.OTHER,
    diary.ACT1_001.HANDICRAFT_AND_PRODUCING_TEXTILES: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_MAKING_AND_CARE_FOR_TEXTILES: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_GARDENING_AND_PET_CARE: Activity.OTHER,
    diary.ACT1_001.GARDENING: Activity.OTHER,
    diary.ACT1_001.TENDING_DOMESTIC_ANIMALS: Activity.OTHER,
    diary.ACT1_001.CARING_FOR_PETS: Activity.OTHER,
    diary.ACT1_001.WALKING_THE_DOG: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_GARDENING_AND_PET_CARE: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_CONSTRUCTION_AND_REPAIRS: Activity.OTHER,
    diary.ACT1_001.HOUSE_CONSTRUCTION_AND_RENOVATION: Activity.OTHER,
    diary.ACT1_001.REPAIRS_OF_DWELLING: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_MAKING__REPAIRING_AND_MAINTAINING_EQUIPMENT: Activity.OTHER,
    diary.ACT1_001.WOODCRAFT__METAL_CRAFT__SCULPTURE_AND_POTTERY: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_MAKING__REPAIRING_AND_MAINTAINING_EQUIPMENT: Activity.OTHER,
    diary.ACT1_001.VEHICLE_MAINTENANCE: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_CONSTRUCTION_AND_REPAIRS: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_SHOPPING_AND_SERVICES: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_SHOPPING: Activity.OTHER,
    diary.ACT1_001.SHOPPING_MAINLY_FOR_FOOD: Activity.OTHER,
    diary.ACT1_001.SHOPPING_MAINLY_FOR_CLOTHING: Activity.OTHER,
    diary.ACT1_001.SHOPPING_MAINLY_RELATED_TO_ACCOMMODATION: Activity.OTHER,
    diary.ACT1_001.SHOPPING_OR_BROWSING_AT_CAR_BOOT_SALES_OR_ANTIQUE_FAIRS: Activity.OTHER,
    diary.ACT1_001.WINDOW_SHOPPING_OR_OTHER_SHOPPING_AS_LEISURE: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_SHOPPING: Activity.OTHER,
    diary.ACT1_001.COMMERCIAL_AND_ADMINISTRATIVE_SERVICES: Activity.OTHER,
    diary.ACT1_001.PERSONAL_SERVICES: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_SHOPPING_AND_SERVICES: Activity.OTHER,
    diary.ACT1_001.HOUSEHOLD_MANAGEMENT_NOT_USING_THE_INTERNET: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_HOUSEHOLD_MANAGEMENT_USING_THE_INTERNET: Activity.OTHER,
    diary.ACT1_001.SHPING_FORANDORDRING_UNSPEC_GDSANDSRVS_VIA_INTERNET: Activity.OTHER,
    diary.ACT1_001.SHPING_FORANDORDRING_FOOD_VIA_THE_INTERNET: Activity.OTHER,
    diary.ACT1_001.SHPING_FORANDORDRING_CLOTHING_VIA_THE_INTERNET: Activity.OTHER,
    diary.ACT1_001.SHPING_FORANDORDRING_GDSANDSRV_RELATED_TO_ACC_VIA_INTERNET: Activity.OTHER,
    diary.ACT1_001.SHPING_FORANDORDRING_MASS_MEDIA_VIA_THE_INTERNET: Activity.OTHER,
    diary.ACT1_001.SHPING_FORANDORDRING_ENTERTAINMENT_VIA_THE_INTERNET: Activity.OTHER,
    diary.ACT1_001.BANKING_AND_BILL_PAYING_VIA_THE_INTERNET: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_HOUSEHOLD_MANAGEMENT_USING_THE_INTERNET: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_CHILDCARE: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_PHYSICAL_CARE_AND_SUPERVISION_OF_A_CHILD: Activity.OTHER,
    diary.ACT1_001.FEEDING_THE_CHILD: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_PHYSICAL_CARE_AND_SUPERVISION_OF_A_CHILD: Activity.OTHER,
    diary.ACT1_001.TEACHING_THE_CHILD: Activity.OTHER,
    diary.ACT1_001.READING__PLAYING_AND_TALKING_WITH_CHILD: Activity.OTHER,
    diary.ACT1_001.ACCOMPANYING_CHILD: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_CHILDCARE: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_HELP_TO_AN_ADULT_HOUSEHOLD_MEMBER: Activity.OTHER,
    diary.ACT1_001.PHYSICAL_CARE_AND_SUPERVISION_OF_AN_ADULT_HOUSEHOLD_MEMBER: Activity.OTHER,
    diary.ACT1_001.ACCOMPANYING_AN_ADULT_HOUSEHOLD_MEMBER: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_HELP_TO_AN_ADULT_HOUSEHOLD_MEMBER: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_VOLUNTEER_WORK_AND_MEETINGS: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_ORGANISATIONAL_WORK: Activity.OTHER,
    diary.ACT1_001.WORK_FOR_AN_ORGANISATION: Activity.OTHER,
    diary.ACT1_001.VOLUNTEER_WORK_THROUGH_AN_ORGANISATION: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_ORGANISATIONAL_WORK: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_INFORMAL_HELP: Activity.OTHER,
    diary.ACT1_001.FOOD_MANAGEMENT_AS_HELP: Activity.OTHER,
    diary.ACT1_001.HOUSEHOLD_UPKEEP_AS_HELP: Activity.OTHER,
    diary.ACT1_001.GARDENING_AND_PET_CARE_AS_HELP: Activity.OTHER,
    diary.ACT1_001.CONSTRUCTION_AND_REPAIRS_AS_HELP: Activity.OTHER,
    diary.ACT1_001.SHOPPING_AND_SERVICES_AS_HELP: Activity.OTHER,
    diary.ACT1_001.HELP_IN_EMPLOYMENT_AND_FARMING: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_CHILDCARE_AS_HELP: Activity.OTHER,
    diary.ACT1_001.PHYSICAL_CARE_AND_SUPERVISION_OF_A_CHILD_AS_HELP: Activity.OTHER,
    diary.ACT1_001.TEACHING_THE_CHILD_AS_HELP: Activity.OTHER,
    diary.ACT1_001.READING__PLAYING_AND_TALKING_TO_THE_CHILD_AS_HELP: Activity.OTHER,
    diary.ACT1_001.ACCOMPANYING_THE_CHILD_AS_HELP: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_CHILDCARE_AS_HELP: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_HELP_TO_AN_ADULT_MEMBER_OF_ANOTHER_HOUSEHOLD: Activity.OTHER,
    diary.ACT1_001.PHYSICAL_CARE_AND_SUPERVISION_OF_AN_ADULT_AS_HELP: Activity.OTHER,
    diary.ACT1_001.ACCOMPANYING_AN_ADULT_AS_HELP: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_HELP_TO_AN_ADULT_MEMBER_OF_ANOTHER_HOUSEHOLD: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_INFORMAL_HELP: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_PARTICIPATORY_ACTIVITIES: Activity.OTHER,
    diary.ACT1_001.MEETINGS: Activity.OTHER,
    diary.ACT1_001.RELIGIOUS_ACTIVITIES: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_PARTICIPATORY_ACTIVITIES: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_SOCIAL_LIFE_AND_ENTERTAINMENT: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_SOCIAL_LIFE: Activity.OTHER,
    diary.ACT1_001.SOCIALISING_WITH_HOUSEHOLD_MEMBERS: Activity.OTHER,
    diary.ACT1_001.VISITING_AND_RECEIVING_VISITORS: Activity.OTHER,
    diary.ACT1_001.FEASTS: Activity.OTHER,
    diary.ACT1_001.TELEPHONE_CONVERSATION: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_SOCIAL_LIFE: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_ENTERTAINMENT_AND_CULTURE: Activity.OTHER,
    diary.ACT1_001.CINEMA: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_THEATRE_OR_CONCERTS: Activity.OTHER,
    diary.ACT1_001.PLAYS__MUSICALS_OR_PANTOMIMES: Activity.OTHER,
    diary.ACT1_001.OPERA__OPERETTA_OR_LIGHT_OPERA: Activity.OTHER,
    diary.ACT1_001.CONCERTS_OR_OTHER_PERFORMANCES_OF_CLASSICAL_MUSIC: Activity.OTHER,
    diary.ACT1_001.LIVE_MUSIC_OTHER_THAN_CLASSICAL_CONCERTS__OPERA_AND_MUSICALS: Activity.OTHER,
    diary.ACT1_001.DANCE_PERFORMANCES: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_THEATRE_OR_CONCERTS: Activity.OTHER,
    diary.ACT1_001.ART_EXHIBITIONS_AND_MUSEUMS: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_LIBRARY: Activity.OTHER,
    diary.ACT1_001.BRWING_BKS_RCDS_AUDIO_VIDEO_CDS_VDS_FROM_LIBRARY: Activity.OTHER,
    diary.ACT1_001.REFERENCE_TO_BKS_AND_OTHER_LIBRARY_MATERIALS_WITHIN_LIBRARY: Activity.OTHER,
    diary.ACT1_001.USING_INTERNET_IN_THE_LIBRARY: Activity.OTHER,
    diary.ACT1_001.USING_COMPUTERS_IN_THE_LIBRARY_OTHER_THAN_INTERNET_USE: Activity.OTHER,
    diary.ACT1_001.READING_NEWSPAPERS_IN_A_LIBRARY: Activity.OTHER,
    diary.ACT1_001.LISTENING_TO_MUSIC_IN_A_LIBRARY: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_LIBRARY_ACTIVITIES: Activity.OTHER,
    diary.ACT1_001.SPORTS_EVENTS: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_ENTERTAINMENT_AND_CULTURE: Activity.OTHER,
    diary.ACT1_001.VISITING_A_HISTORICAL_SITE: Activity.OTHER,
    diary.ACT1_001.VISITING_A_WILDLIFE_SITE: Activity.OTHER,
    diary.ACT1_001.VISITING_A_BOTANICAL_SITE: Activity.OTHER,
    diary.ACT1_001.VISITING_A_LEISURE_PARK: Activity.OTHER,
    diary.ACT1_001.VISITING_AN_URBAN_PARK__PLAYGROUND_OR_DESIGNATED_PLAY_AREA: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_ENTERTAINMENT_OR_CULTURE: Activity.OTHER,
    diary.ACT1_001.RESTING_TIME_OUT: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_SPORTS_AND_OUTDOOR_ACTIVITIES: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_PHYSICAL_EXERCISE: Activity.OTHER,
    diary.ACT1_001.WALKING_AND_HIKING: Activity.OTHER,
    diary.ACT1_001.TAKING_A_WALK_OR_HIKE_THAT_LASTS_AT_LEAST_2_MILES_OR_1_HOUR: Activity.OTHER,
    diary.ACT1_001.OTHER_WALK_OR_HIKE: Activity.OTHER,
    diary.ACT1_001.JOGGING_AND_RUNNING: Activity.OTHER,
    diary.ACT1_001.BIKING__SKIING_AND_SKATING: Activity.OTHER,
    diary.ACT1_001.BIKING: Activity.OTHER,
    diary.ACT1_001.SKIING_OR_SKATING: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_BALL_GAMES: Activity.OTHER,
    diary.ACT1_001.INDOOR_PAIRS_OR_DOUBLES_GAMES: Activity.OTHER,
    diary.ACT1_001.INDOOR_TEAM_GAMES: Activity.OTHER,
    diary.ACT1_001.OUTDOOR_PAIRS_OR_DOUBLES_GAMES: Activity.OTHER,
    diary.ACT1_001.OUTDOOR_TEAM_GAMES: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_BALL_GAMES: Activity.OTHER,
    diary.ACT1_001.GYMNASTICS: Activity.OTHER,
    diary.ACT1_001.FITNESS: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_WATER_SPORTS: Activity.OTHER,
    diary.ACT1_001.SWIMMING: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_WATER_SPORTS: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_PHYSICAL_EXERCISE: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_PRODUCTIVE_EXERCISE: Activity.OTHER,
    diary.ACT1_001.HUNTING_AND_FISHING: Activity.OTHER,
    diary.ACT1_001.PICKING_BERRIES__MUSHROOM_AND_HERBS: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_PRODUCTIVE_EXERCISE: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_SPORTS_RELATED_ACTIVITIES: Activity.OTHER,
    diary.ACT1_001.ACTIVITIES_RELATED_TO_SPORTS: Activity.OTHER,
    diary.ACT1_001.ACTIVITIES_RELATED_TO_PRODUCTIVE_EXERCISE: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_HOBBIES_AND_GAMES: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_ARTS: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_VISUAL_ARTS: Activity.OTHER,
    diary.ACT1_001.PAINTING__DRAWING_OR_OTHER_GRAPHIC_ARTS: Activity.OTHER,
    diary.ACT1_001.MAKING_VIDEOS__TAKING_PHOTOS_OR_RELATED_ACTIVITIES: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_VISUAL_ARTS: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_PERFORMING_ARTS: Activity.OTHER,
    diary.ACT1_001.SINGING_OR_OTHER_MUSICAL_ACTIVITIES: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_PERFORMING_ARTS: Activity.OTHER,
    diary.ACT1_001.LITERARY_ARTS: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_ARTS: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_HOBBIES: Activity.OTHER,
    diary.ACT1_001.COLLECTING: Activity.OTHER,
    diary.ACT1_001.COMPUTING_PROGRAMMING: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_INFORMATION_BY_COMPUTING: Activity.OTHER,
    diary.ACT1_001.INFORMATION_SEARCHING_ON_THE_INTERNET: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_INFORMATION_BY_COMPUTING: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_COMMUNICATION_BY_COMPUTER: Activity.OTHER,
    diary.ACT1_001.COMMUNICATION_ON_THE_INTERNET: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_COMMUNICATION_BY_COMPUTING: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_OTHER_COMPUTING: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_INTERNET_USE: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_COMPUTING: Activity.OTHER,
    diary.ACT1_001.CORRESPONDENCE: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_HOBBIES: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_GAMES: Activity.OTHER,
    diary.ACT1_001.SOLO_GAMES_AND_PLAY: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_GAMES_AND_PLAY_WITH_OTHERS: Activity.OTHER,
    diary.ACT1_001.BILLIARDS__POOL__SNOOKER_OR_PETANQUE: Activity.OTHER,
    diary.ACT1_001.CHESS_AND_BRIDGE: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_PARLOUR_GAMES_AND_PLAY: Activity.OTHER,
    diary.ACT1_001.COMPUTER_GAMES: Activity.OTHER,
    diary.ACT1_001.GAMBLING: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_GAMES: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_MASS_MEDIA: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_READING: Activity.OTHER,
    diary.ACT1_001.READING_PERIODICALS: Activity.OTHER,
    diary.ACT1_001.READING_BOOKS: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_READING: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_TV_WATCHING: Activity.OTHER,
    diary.ACT1_001.WATCHING_A_FILM_ON_TV: Activity.OTHER,
    diary.ACT1_001.WATCHING_SPORT_ON_TV: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_TV_WATCHING: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_VIDEO_WATCHING: Activity.OTHER,
    diary.ACT1_001.WATCHING_A_FILM_ON_VIDEO: Activity.OTHER,
    diary.ACT1_001.WATCHING_SPORT_ON_VIDEO: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_VIDEO_WATCHING: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_LISTENING_TO_RADIO_AND_MUSIC: Activity.OTHER,
    diary.ACT1_001.UNSPECIFIED_RADIO_LISTENING: Activity.OTHER,
    diary.ACT1_001.LISTENING_TO_MUSIC_ON_THE_RADIO: Activity.OTHER,
    diary.ACT1_001.LISTENING_TO_SPORT_ON_THE_RADIO: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_RADIO_LISTENING: Activity.OTHER,
    diary.ACT1_001.LISTENING_TO_RECORDINGS: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_UNSPECIFIED_TIME_USE: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_PERSONAL_BUSINESS: Activity.OTHER,
    diary.ACT1_001.TRAVEL_IN_THE_COURSE_OF_WORK: Activity.OTHER,
    diary.ACT1_001.TRAVEL_TO_WORK_FROM_HOME_AND_BACK_ONLY: Activity.OTHER,
    diary.ACT1_001.TRAVEL_TO_WORK_FROM_A_PLACE_OTHER_THAN_HOME: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_EDUCATION: Activity.OTHER,
    diary.ACT1_001.TRAVEL_ESCORTING_TO_FROM_EDUCATION: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_HOUSEHOLD_CARE: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_SHOPPING: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_SERVICES: Activity.OTHER,
    diary.ACT1_001.TRAVEL_ESCORTING_A_CHILD_OTHER_THAN_EDUCATION: Activity.OTHER,
    diary.ACT1_001.TRAVEL_ESCORTING_AN_ADULT_OTHER_THAN_EDUCATION: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_ORGANISATIONAL_WORK: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_INFORMAL_HELP_TO_OTHER_HOUSEHOLDS: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_RELIGIOUS_ACTIVITIES: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RLT_TO_PARTICIPATORY_ACTV_EXCEPT_REL_ACTV: Activity.OTHER,
    diary.ACT1_001.TRAVEL_TO_VISIT_FRIENDS_RELATIVES_IN_THEIR_HOMES: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_OTHER_SOCIAL_ACTIVITIES: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_ENTERTAINMENT_AND_CULTURE: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_PHYSICAL_EXERCISE: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_HUNTING_AND_FISHING: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_PRODUCTIVE_EXCS_EXPT_HUNTING_AND_FISHING: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_GAMBLING: Activity.OTHER,
    diary.ACT1_001.TRAVEL_RELATED_TO_HOBBIES_OTHER_THAN_GAMBLING: Activity.OTHER,
    diary.ACT1_001.TRAVEL_TO_HOLIDAY_BASE: Activity.OTHER,
    diary.ACT1_001.TRAVEL_FOR_DAY_TRIP_JUST_WALK: Activity.OTHER,
    diary.ACT1_001.OTHER_SPECIFIED_TRAVEL: Activity.OTHER,
    diary.ACT1_001.PUNCTUATING_ACTIVITY: Activity.OTHER,
    diary.ACT1_001.FILLING_IN_THE_TIME_USE_DIARY: Activity.OTHER,
    diary.ACT1_001.NO_MAIN_ACTIVITY__NO_IDEA_WHAT_IT_MIGHT_BE: Activity.UNKNOWN,
    diary.ACT1_001.NO_MAIN_ACTIVITY__SOME_IDEA_WHAT_IT_MIGHT_BE: Activity.UNKNOWN,
    diary.ACT1_001.ILLEGIBLE_ACTIVITY: Activity.UNKNOWN,
    diary.ACT1_001.UNSPECIFIED_TIME_USE: Activity.UNKNOWN,
    diary.ACT1_001.MISSING1: Activity.UNKNOWN
}


ECONOMIC_ACTIVITY_MAP = {
    individual.ECONACT2.ECON_ACTIVE___EMPLOYEE___FULL_TIME: EconomicActivity.EMPLOYEE_FULL_TIME,
    individual.ECONACT2.ECON_INACTIVE___LONG_TERM_SICK_DISABLED: EconomicActivity.LONG_TERM_SICK,
    individual.ECONACT2.ECON_INACTIVE___OTHER_REASONS_EG_TEMP_SICK__BELIEVES_NO_JOBS:
        EconomicActivity.INACTIVE_OTHER,
    individual.ECONACT2.ECON_INACTIVE___DK_REASONS: np.nan, # FIXME
    individual.ECONACT2.ADULT___NOT_CLASSIFIABLE_EITHER_EMP__UNEMP_OR_INACTIVE: np.nan,
    individual.ECONACT2.UNDER_16YRS___INELIGIBLE_FOR_EMPLOYMENT_QUESTIONS:
        EconomicActivity.BELOW_16,
    individual.ECONACT2.ECON_ACTIVE___EMPLOYEE___PART_TIME: EconomicActivity.EMPLOYEE_PART_TIME,
    individual.ECONACT2.ECON_ACTIVE___SELF_EMPLOYED___FULL_TIME: EconomicActivity.SELF_EMPLOYED,
    individual.ECONACT2.ECON_ACTIVE___SELF_EMPLOYED___PART_TIME: EconomicActivity.SELF_EMPLOYED,
    individual.ECONACT2.ECON_ACTIVE___DK_EMPSELFFULLPART: np.nan, # FIXME
    individual.ECONACT2.ECON_ACTIVE___UNEMPLOYED_ILO_DEFINITION: EconomicActivity.UNEMPLOYED,
    individual.ECONACT2.ECON_INACTIVE___RETIRED: EconomicActivity.RETIRED,
    individual.ECONACT2.ECON_INACTIVE___FULL_TIME_STUDENT:
        EconomicActivity.INACTIVE_FULL_TIME_STUDENT,
    individual.ECONACT2.ECON_INACTIVE___LOOKING_AFTER_FAMILY_HOME:
        EconomicActivity.LOOKING_AFTER_HOME
}


QUALIFICATION_MAP = { # FIXME all must be checked again
    individual.HIQUAL4.DEGREE_LEVEL_QUALIFICATION_OR_ABOVE: Qualification.LEVEL_45,
    individual.HIQUAL4.QUALIFICATIONS___CITY_AND_GUILDS___DK_LEVEL: np.nan,
    individual.HIQUAL4.QUALIFICATIONS___OTHER___BUT_DK_GRADELEVEL: np.nan,
    individual.HIQUAL4.NO_QUALIFICATIONS: Qualification.NO_QUALIFICATIONS,
    individual.HIQUAL4.ELIGIBLE___NO_ANSWER: np.nan,
    individual.HIQUAL4.UNDER_16YRS___INELIGIBLE_FOR_QUALIFICATIONS_QUESTIONS:
        Qualification.BELOW_16,
    individual.HIQUAL4.HIGHER_EDN_BELOW_DEGREE_LEVEL_EG_HNC__NURSING_QUAL: Qualification.LEVEL_3,
    individual.HIQUAL4.A_LEVELS__VOCATIONAL_LEVEL_3_AND_EQUIVLNT_EG_AS_LEVEL__NVQ_3:
        Qualification.LEVEL_3,
    individual.HIQUAL4.O_LEVELS__GCSE_GRADE_A_C__VOCATIONAL_LEVEL_2_AND_EQUIVLNT:
        Qualification.LEVEL_2,
    individual.HIQUAL4.GCSE_BELOW_GRADE_C__CSE__VOCATIONAL_LEVEL_1_AND_EQUIVLNT:
        Qualification.LEVEL_1,
    individual.HIQUAL4.QUALIFICATION_BELOW_GCSEO_LEVEL_EG_TRADE_APPRENTICESHIPS:
        Qualification.APPRENTICESHIP,
    individual.HIQUAL4.OTHER_QUALIFICATION_INCL_PROFESSIONAL__VOCATIONAL__FOREIGN:
        Qualification.OTHER_QUALIFICATION,
    individual.HIQUAL4.QUALIFICATIONS___BUT_DK_WHICH: Qualification.OTHER_QUALIFICATION,
    individual.HIQUAL4.QUALIFICATIONS___GCSE___BUT_DK_GRADE: np.nan
}


HOUSEHOLDTYPE_MAP = {
    individual.HHTYPE4.SINGLE_PERSON_HOUSEHOLD:
        HouseholdType.ONE_PERSON_HOUSEHOLD,
    individual.HHTYPE4.SINGLE_PARENT___WITH_CHILDREN_GREATEREQUAL_16:
        HouseholdType.LONE_PARENT_WITH_DEPENDENT_CHILDREN,
    individual.HHTYPE4.TWO_OR_MORE_COUPLES_MARRIED_OR_COHAB_WITHWITHOUT_CHILDRN:
        HouseholdType.MULTI_PERSON_HOUSEHOLD,
    individual.HHTYPE4.SAME_SEX_COUPLES___SPONTANEOUSLY_DESCRIBED:
        HouseholdType.COUPLE_WITHOUT_DEPENDENT_CHILDREN,
    individual.HHTYPE4.UNCLASSIFIED___MARRIED_COUPLES_IN_COMPLEX_HHLDS:
        HouseholdType.MULTI_PERSON_HOUSEHOLD,
    individual.HHTYPE4.UNCLASSIFIED___COHABITING_COUPLES_IN_COMPLEX_HHLDS:
        HouseholdType.MULTI_PERSON_HOUSEHOLD,
    individual.HHTYPE4.UNCLASSIFIED___SINGLE_PARENTS_IN_COMPLEX_HHLDS:
        HouseholdType.MULTI_PERSON_HOUSEHOLD,
    individual.HHTYPE4.UNCLASSIFIED___OTHER_HHLDS_WITHOUT_COUPLES_EG_BROTHERS_DK:
        HouseholdType.MULTI_PERSON_HOUSEHOLD,
    individual.HHTYPE4.HHLDS_WITH_2_OR_MORE_UNRELATED_PEOPLE_ONLY:
        HouseholdType.MULTI_PERSON_HOUSEHOLD,
    individual.HHTYPE4.MARRIED_COUPLE___NO_CHILDREN_COUPLE_ONLY:
        HouseholdType.COUPLE_WITHOUT_DEPENDENT_CHILDREN,
    individual.HHTYPE4.MARRIED_COUPLE___WITH_CHILDREN_SMALLEREQUAL_15:
        HouseholdType.COUPLE_WITH_DEPENDENT_CHILDREN,
    individual.HHTYPE4.MARRIED_COUPLE___WITH_CHILDREN_GREATEREQUAL_16:
        HouseholdType.COUPLE_WITH_DEPENDENT_CHILDREN,
    individual.HHTYPE4.COHAB_COUPLE___NO_CHILDREN_COUPLE_ONLY:
        HouseholdType.COUPLE_WITHOUT_DEPENDENT_CHILDREN,
    individual.HHTYPE4.COHAB_COUPLE___WITH_CHILDREN_SMALLEREQUAL_15:
        HouseholdType.COUPLE_WITH_DEPENDENT_CHILDREN,
    individual.HHTYPE4.COHAB_COUPLE___WITH_CHILDREN_GREATEREQUAL_16:
        HouseholdType.COUPLE_WITH_DEPENDENT_CHILDREN,
    individual.HHTYPE4.SINGLE_PARENT____WITH_CHILDREN_SMALLEREQUAL_15:
        HouseholdType.LONE_PARENT_WITH_DEPENDENT_CHILDREN
}
