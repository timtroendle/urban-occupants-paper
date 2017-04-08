"""Census related functions and type mappings.

For definitions of any of the terms see [the original glossary]
(http://www.ons.gov.uk/ons/guide-method/census/2011/census-data/2011-census-data/2011-first-release/
2011-census-definitions/2011-census-glossary.pdf).

Census data is retrieved from nomis, see https://www.nomisweb.co.uk.
"""
from enum import Enum
import io

import requests
import numpy as np
import pandas as pd

from .types import AgeStructure, EconomicActivity, Qualification, HouseholdType, Pseudo

NOMIS_KS102EW_DATASET_ID = "NM_145_1"
NOMIS_QS116EW_DATASET_ID = "NM_516_1"
NOMIS_KS501EW_DATASET_ID = "NM_623_1"
NOMIS_KS601EW_DATASET_ID = "NM_624_1"
# the following are nomis geography codes for Haringey on different layer
NOMIS_WARD_GEOGRAPHY = "1237319929...1237319939,1237319941,1237319940,1237319942...1237319947"
NOMIS_MSOA_GEOGRPAHY = "1245708671...1245708705,1245714941"
NOMIS_LSOA_GEOGRAPHY = ("1249904514,1249904516,1249904519,1249904520,1249904579,1249904580," +
                        "1249904582,1249904583,1249904507,1249904515,1249904517,1249904518," +
                        "1249904633,1249904636,1249904639,1249904640,1249904634,1249904635," +
                        "1249904637,1249904638,1249904641,1249904644,1249904645,1249904648," +
                        "1249904642,1249904643,1249904646,1249904647,1249904508...1249904511," +
                        "1249904571,1249904572,1249904576,1249904577,1249904521...1249904524," +
                        "1249904617,1249904620,1249904622,1249904624,1249904625,1249904629," +
                        "1249904631,1249904632,1249904512,1249904513,1249904541,1249904542," +
                        "1249904618,1249904619,1249904621,1249904623,1249904570," +
                        "1249904573...1249904575,1249904536...1249904538,1249904540," +
                        "1249904525...1249904528,1249904626...1249904628,1249904630,1249904558," +
                        "1249904559,1249904562,1249934828,1249934829,1249904564,1249904566," +
                        "1249904567,1249904569,1249904557,1249904563,1249904565,1249904568," +
                        "1249904543,1249904544,1249904548,1249904549,1249904610,1249904612," +
                        "1249904613,1249904616,1249904609,1249904611,1249904614,1249904615," +
                        "1249904586,1249904588,1249904589,1249904592,1249904585,1249904587," +
                        "1249904590,1249904591,1249904560,1249904561,1249904602,1249904603," +
                        "1249904593...1249904595,1249904598,1249904539,1249904553,1249904555," +
                        "1249904556,1249904545...1249904547,1249904601,1249904596,1249904597," +
                        "1249904599,1249904600,1249904529,1249904530,1249904532,1249904534," +
                        "1249904531,1249904533,1249904535,1249904605,1249904550...1249904552," +
                        "1249904554,1249904604,1249904606...1249904608,1249904578,1249904581," +
                        "1249904584,1249934354")
NOMIS_OA_GEOGRAPHY = "1254106458...1254107181,1254258316,1254262366...1254262393"
NOMIS_GEOGRAPHY_CODE_COLUMN_NAME = "GEOGRAPHY_CODE"
NOMIS_VALUE_NAME_COLUMN_NAME = "CELL_NAME"
NOMIS_VALUE_COLUMN_NAME = "OBS_VALUE"


class GeographicalLayer(Enum):
    """The geographical layer at which census data should be retrieved."""
    OA = (NOMIS_OA_GEOGRAPHY)
    LSOA = (NOMIS_LSOA_GEOGRAPHY)
    MSOA = (NOMIS_MSOA_GEOGRPAHY)
    WARD = (NOMIS_WARD_GEOGRAPHY)

    def __init__(self, geo_codes):
        self.geo_codes = geo_codes


AGE_STRUCTURE_MAP = {
    "Age 0 to 4": AgeStructure.AGE_0_TO_4,
    "Age 5 to 7": AgeStructure.AGE_5_TO_7,
    "Age 8 to 9": AgeStructure.AGE_8_TO_9,
    "Age 10 to 14": AgeStructure.AGE_10_TO_14,
    "Age 15": AgeStructure.AGE_15,
    "Age 16 to 17": AgeStructure.AGE_16_TO_17,
    "Age 18 to 19": AgeStructure.AGE_18_TO_19,
    "Age 20 to 24": AgeStructure.AGE_20_TO_24,
    "Age 25 to 29": AgeStructure.AGE_25_TO_29,
    "Age 30 to 44": AgeStructure.AGE_30_TO_44,
    "Age 45 to 59": AgeStructure.AGE_45_TO_59,
    "Age 60 to 64": AgeStructure.AGE_60_TO_64,
    "Age 65 to 74": AgeStructure.AGE_65_TO_74,
    "Age 75 to 84": AgeStructure.AGE_75_TO_84,
    "Age 85 to 89": AgeStructure.AGE_85_TO_89,
    "Age 90 and over": AgeStructure.AGE_90_AND_OVER
}


ECONOMIC_ACTIVITY_MAP = {
    'Economically active: Employee: Part-time': EconomicActivity.EMPLOYEE_PART_TIME,
    'Economically active: Employee: Full-time': EconomicActivity.EMPLOYEE_FULL_TIME,
    'Economically active: Self-employed': EconomicActivity.SELF_EMPLOYED,
    'Economically active: Unemployed': EconomicActivity.UNEMPLOYED,
    'Economically active: Full-time student': EconomicActivity.ACTIVE_FULL_TIME_STUDENT,
    'Economically inactive: Retired': EconomicActivity.RETIRED,
    'Economically inactive: Student (including full-time students)':
        EconomicActivity.INACTIVE_FULL_TIME_STUDENT,
    'Economically inactive: Looking after home or family': EconomicActivity.LOOKING_AFTER_HOME,
    'Economically inactive: Long-term sick or disabled': EconomicActivity.LONG_TERM_SICK,
    'Economically inactive: Other': EconomicActivity.INACTIVE_OTHER
}


QUALIFICATION_MAP = {
    'No qualifications': Qualification.NO_QUALIFICATIONS,
    'Highest level of qualification: Level 1 qualifications': Qualification.LEVEL_1,
    'Highest level of qualification: Level 2 qualifications': Qualification.LEVEL_2,
    'Highest level of qualification: Apprenticeship': Qualification.APPRENTICESHIP,
    'Highest level of qualification: Level 3 qualifications': Qualification.LEVEL_3,
    'Highest level of qualification: Level 4 qualifications and above': Qualification.LEVEL_45,
    'Highest level of qualification: Other qualifications': Qualification.OTHER_QUALIFICATION
}


HOUSEHOLDTYPE_MAP = {
    'One person household': HouseholdType.ONE_PERSON_HOUSEHOLD,
    'Married couple household: With dependent children':
        HouseholdType.COUPLE_WITH_DEPENDENT_CHILDREN,
    'Married couple household: No dependent children':
        HouseholdType.COUPLE_WITHOUT_DEPENDENT_CHILDREN,
    'Same-sex civil partnership couple household: With dependent children':
        HouseholdType.COUPLE_WITH_DEPENDENT_CHILDREN,
    'Same-sex civil partnership couple household: No dependent children':
        HouseholdType.COUPLE_WITHOUT_DEPENDENT_CHILDREN,
    'Cohabiting couple household: With dependent children':
        HouseholdType.COUPLE_WITH_DEPENDENT_CHILDREN,
    'Cohabiting couple household: No dependent children':
        HouseholdType.COUPLE_WITHOUT_DEPENDENT_CHILDREN,
    'Lone parent household: With dependent children':
        HouseholdType.LONE_PARENT_WITH_DEPENDENT_CHILDREN,
    'Lone parent household: No dependent children':
        HouseholdType.ONE_PERSON_HOUSEHOLD,
    'Multi-person household: All full-time students':
        HouseholdType.MULTI_PERSON_HOUSEHOLD,
    'Multi-person household: Other':
        HouseholdType.MULTI_PERSON_HOUSEHOLD
}


def read_age_structure_data(geographical_layer=GeographicalLayer.LSOA):
    """Retrieves age structure date from Census 2011 for Haringey.

    Data is taken from the KS102EW table from the UK Census 2011.
    Data is retrieved from nomis, see https://www.nomisweb.co.uk.
    """
    url = ("https://www.nomisweb.co.uk/api/v01/dataset/{}.data.csv" +
           "?date=latest&geography={}&rural_urban=0&measures=20100" +
           "&select=geography_code,cell_name,obs_value").format(NOMIS_KS102EW_DATASET_ID,
                                                                geographical_layer.geo_codes)
    r = requests.get(url)
    df = pd.read_csv(io.BytesIO(r.content))
    df = df.pivot(
        index='GEOGRAPHY_CODE',
        columns='CELL_NAME',
        values='OBS_VALUE'
    )[list(AGE_STRUCTURE_MAP.keys())].astype(np.int64)
    df = df.rename(columns=AGE_STRUCTURE_MAP).groupby(lambda x: x, axis=1).sum()
    return df


def read_household_type_data(geographical_layer=GeographicalLayer.LSOA):
    """Retrieves household type date from Census 2011 for Haringey.

    Data is taken from the QS116EW table from the UK Census 2011.
    Data is retrieved from nomis, see https://www.nomisweb.co.uk.
    """
    url = ("https://www.nomisweb.co.uk/api/v01/dataset/{}.data.csv" +
           "?date=latest&geography={}&rural_urban=0&measures=20100" +
           "&select=geography_code,c_ahthuk11_name,obs_value").format(NOMIS_QS116EW_DATASET_ID,
                                                                      geographical_layer.geo_codes)
    r = requests.get(url)
    df = pd.read_csv(io.BytesIO(r.content))
    df = df.pivot(
        index='GEOGRAPHY_CODE',
        columns='C_AHTHUK11_NAME',
        values='OBS_VALUE'
    )[list(HOUSEHOLDTYPE_MAP.keys())].astype(np.int64)
    df = df.rename(columns=HOUSEHOLDTYPE_MAP).groupby(lambda x: x, axis=1).sum()
    return df


def read_qualification_level_data(geographical_layer=GeographicalLayer.LSOA):
    """Retrieves highest qualification level data from Census 2011 for Haringey.

    Data is taken from the KS501EW table from the UK Census 2011.
    Data is retrieved from nomis, see https://www.nomisweb.co.uk.
    """
    url = ("https://www.nomisweb.co.uk/api/v01/dataset/{}.data.csv" +
           "?date=latest&geography={}&rural_urban=0&measures=20100" +
           "&select=geography_code,cell_name,obs_value").format(NOMIS_KS501EW_DATASET_ID,
                                                                geographical_layer.geo_codes)
    r = requests.get(url)
    df = pd.read_csv(io.BytesIO(r.content))
    df = df.pivot(
        index='GEOGRAPHY_CODE',
        columns='CELL_NAME',
        values='OBS_VALUE'
    )[list(QUALIFICATION_MAP.keys())].astype(np.int64)
    df = df.rename(columns=QUALIFICATION_MAP).groupby(lambda x: x, axis=1).sum()
    return df


def read_economic_activity_data(geographical_layer=GeographicalLayer.LSOA):
    """Retrieves economic activity data from Census 2011 for Haringey.

    Data is taken from the KS601EW table from the UK Census 2011.
    Data is retrieved from nomis, see https://www.nomisweb.co.uk.
    """
    url = ("https://www.nomisweb.co.uk/api/v01/dataset/{}.data.csv" +
           "?date=latest&geography={}&rural_urban=0&measures=20100" +
           "&c_sex=0" +
           "&select=geography_code,cell_name,obs_value").format(NOMIS_KS601EW_DATASET_ID,
                                                                geographical_layer.geo_codes)
    r = requests.get(url)
    df = pd.read_csv(io.BytesIO(r.content))
    df = df.pivot(
        index='GEOGRAPHY_CODE',
        columns='CELL_NAME',
        values='OBS_VALUE'
    )[list(ECONOMIC_ACTIVITY_MAP.keys())].astype(np.int64)
    df = df.rename(columns=ECONOMIC_ACTIVITY_MAP).groupby(lambda x: x, axis=1).sum()
    return df


def read_pseudo_individual_data(geographical_layer=GeographicalLayer.LSOA):
    """Creates pseudo feature data for people.

    The data set will be equivalent to the population sum.
    """
    data = read_age_structure_data(geographical_layer)
    data[Pseudo.SINGLETON] = data.sum(axis=1)
    return data[[Pseudo.SINGLETON]]


def read_pseudo_household_data(geographical_layer=GeographicalLayer.LSOA):
    """Creates pseudo feature data for households.

    The data set will be equivalent to the household sum.
    """
    data = read_household_type_data(geographical_layer)
    data[Pseudo.SINGLETON] = data.sum(axis=1)
    return data[[Pseudo.SINGLETON]]
