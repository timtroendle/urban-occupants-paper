"""Census related functions and type mappings.

For definitions of any of the terms see [the original glossary]
(http://www.ons.gov.uk/ons/guide-method/census/2011/census-data/2011-census-data/2011-first-release/
2011-census-definitions/2011-census-glossary.pdf).

Census data is retrieved from nomis, see https://www.nomisweb.co.uk.
"""
from enum import Enum
import io
from pathlib import Path
import tempfile
import zipfile

import requests
import numpy as np
import pandas as pd
import geopandas as gpd

from .types import AgeStructure, EconomicActivity, Qualification, HouseholdType, Pseudo

NOMIS_KS102EW_DATASET_ID = "NM_145_1"
NOMIS_QS116EW_DATASET_ID = "NM_516_1"
NOMIS_KS501EW_DATASET_ID = "NM_623_1"
NOMIS_KS601EW_DATASET_ID = "NM_624_1"
# the following are nomis geography codes for Haringey on different layer
NOMIS_WARD_HARINGEY = "1237319929...1237319939,1237319941,1237319940,1237319942...1237319947"
NOMIS_MSOA_HARINGEY = "1245708671...1245708705,1245714941"
NOMIS_LSOA_HARINGEY = ("1249904514,1249904516,1249904519,1249904520,1249904579,1249904580," +
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
NOMIS_OA_HARINGEY = "1254106458...1254107181,1254258316,1254262366...1254262393"
# the following are nomis geography codes for Greater London on different layer
# LSOA and OA are skipped as the collection of numbers is too large and links would become huge
NOMIS_WARD_GREATER_LONDON = ("1237319791...1237319808,1237319681...1237319688," +
                             "1237319894...1237319947,1237320029...1237320062," +
                             "1237320079...1237320117,1237320138...1237320157," +
                             "1237320197...1237320217,1237320236...1237320252," +
                             "1237320273...1237320312,1237319689...1237319790," +
                             "1237319809...1237319893,1237319948...1237320028," +
                             "1237320063...1237320078,1237320118...1237320137," +
                             "1237320158...1237320196,1237320218...1237320235," +
                             "1237320253...1237320272")

NOMIS_MSOA_GREATER_LONDON = ("1245708449...1245708476,1245708289,1245708620...1245708645," +
                             "1245715064,1245715067,1245708646...1245708705,1245714941," +
                             "1245708822...1245708865,1245708886...1245708919,1245714947," +
                             "1245708920...1245708952,1245714930,1245714931,1245714944," +
                             "1245708978...1245709014,1245709066...1245709097,1245714948," +
                             "1245709121...1245709150,1245714999,1245715000," +
                             "1245709179...1245709239,1245708290...1245708310,1245714945," +
                             "1245708311...1245708378,1245714932,1245708379...1245708448," +
                             "1245714929,1245714934,1245714936,1245708477...1245708519," +
                             "1245714935,1245708520...1245708557,1245714938," +
                             "1245708558...1245708592,1245714940,1245708593...1245708619," +
                             "1245714933,1245715072...1245715076,1245708706...1245708733," +
                             "1245714942,1245715028,1245708734...1245708794,1245714943," +
                             "1245708795...1245708821,1245714939,1245708866...1245708885," +
                             "1245708953...1245708977,1245709015...1245709042,1245714946," +
                             "1245715069,1245715070,1245709043...1245709065," +
                             "1245709098...1245709120,1245714982,1245709151...1245709178")
LONDON_BOROUGHS = ["Westminster", "Kensington and Chelsea",
                   "Hammersmith and Fulham", "Wandsworth", "Lambeth", "Southwark", "Tower Hamlets",
                   "Hackney", "Islington", "Camden", "Brent", "Ealing", "Hounslow",
                   "Richmond upon Thames", "Kingston upon Thames", "Merton", "Sutton", "Croydon",
                   "Bromley", "Lewisham", "Greenwich", "Bexley", "Havering", "Barking and Dagenham",
                   "Redbridge", "Newham", "Waltham Forest", "Haringey", "Enfield", "Barnet",
                   "Harrow", "Hillingdon"]
NOMIS_GEOGRAPHY_CODE_COLUMN_NAME = "GEOGRAPHY_CODE"
NOMIS_VALUE_NAME_COLUMN_NAME = "CELL_NAME"
NOMIS_VALUE_COLUMN_NAME = "OBS_VALUE"

LONDON_BOUNDARY_FILE_URL = ('https://files.datapress.com/london/dataset/statistical-gis-boundary-'
                            'files-london/2016-10-03T13:52:28/statistical-gis-boundaries-'
                            'london.zip')
WARD_SHAPE_FILE_PATH = Path('./statistical-gis-boundaries-london/ESRI/London_Ward.shp')
MSOA_SHAPE_FILE_PATH = Path('./statistical-gis-boundaries-london/ESRI/MSOA_2011_London_gen_MHW.shp')
LSOA_SHAPE_FILE_PATH = Path('./statistical-gis-boundaries-london/ESRI/LSOA_2011_London_gen_MHW.shp')
OA_SHAPE_FILE_PATH = Path('./statistical-gis-boundaries-london/ESRI/OA_2011_London_gen_MHW.shp')
BOROUGH_ID_IN_WARD_DATA_SET = 'BOROUGH'
BOROUGH_ID_COLUMN_NAME = 'LAD11NM'
WARD_ID_COLUMN_NAME = 'GSS_CODE'
MSOA_ID_COLUMN_NAME = 'MSOA11CD'
LSOA_ID_COLUMN_NAME = 'LSOA11CD'
OA_ID_COLUMN_NAME = 'OA11CD'


class GeographicalLayer(Enum):
    """The geographical layer at which census data should be retrieved."""
    OA = (OA_SHAPE_FILE_PATH, BOROUGH_ID_COLUMN_NAME, OA_ID_COLUMN_NAME)
    LSOA = (LSOA_SHAPE_FILE_PATH, BOROUGH_ID_COLUMN_NAME, LSOA_ID_COLUMN_NAME)
    MSOA = (MSOA_SHAPE_FILE_PATH, BOROUGH_ID_COLUMN_NAME, MSOA_ID_COLUMN_NAME)
    WARD = (WARD_SHAPE_FILE_PATH, BOROUGH_ID_IN_WARD_DATA_SET, WARD_ID_COLUMN_NAME)

    def __init__(self, shape_file_path, borough_col_name, index_col_name):
        self.shape_file_path = shape_file_path
        self.borough_col_name = borough_col_name
        self.index_col_name = index_col_name


class StudyArea(Enum):
    """The study area inside of Greater London for which census data should be retrieved.

    A study area comprises of one or more boroughs.
    """
    HARINGEY = (['Haringey'], 101955, 254926, NOMIS_OA_HARINGEY, NOMIS_LSOA_HARINGEY,
                NOMIS_MSOA_HARINGEY, NOMIS_WARD_HARINGEY)
    GREATER_LONDON = (LONDON_BOROUGHS, 3266173, 8173941, None, None,
                      NOMIS_MSOA_GREATER_LONDON, NOMIS_WARD_GREATER_LONDON)

    def __init__(self, borough_names, number_households, number_usual_residents,
                 nomis_oa_geo_codes, nomis_lsoa_geo_codes,
                 nomis_msoa_geo_codes, nomis_ward_geo_codes):
        self.borough_names = borough_names
        self.number_households = number_households
        self.number_usual_residents = number_usual_residents
        self._nomis_geo_codes = {
            GeographicalLayer.OA: nomis_oa_geo_codes,
            GeographicalLayer.LSOA: nomis_lsoa_geo_codes,
            GeographicalLayer.MSOA: nomis_msoa_geo_codes,
            GeographicalLayer.WARD: nomis_ward_geo_codes
        }

    def nomis_geo_codes(self, geographical_layer):
        if self == StudyArea.GREATER_LONDON and (geographical_layer == GeographicalLayer.LSOA or
                                                 geographical_layer == GeographicalLayer.OA):
            raise ValueError("LSOA and OA levels not supported for Greater London.")
        else:
            return self._nomis_geo_codes[geographical_layer]


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


def read_shape_file(study_area=StudyArea.HARINGEY, geographical_layer=GeographicalLayer.LSOA):
    """Reads shape file of the study area from London Data Store.

    Make sure to use requests_cache to cache the retrieved data.
    """
    r = requests.get(LONDON_BOUNDARY_FILE_URL)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    with tempfile.TemporaryDirectory(prefix='london-boundary-files') as tmpdir:
        z.extractall(path=tmpdir)
        shape_file = Path(tmpdir) / geographical_layer.shape_file_path
        data = gpd.read_file(shape_file.as_posix())
    data = data[data[geographical_layer.borough_col_name].isin(study_area.borough_names)]
    return data.set_index(geographical_layer.index_col_name)


def read_age_structure_data(study_area=StudyArea.HARINGEY,
                            geographical_layer=GeographicalLayer.LSOA):
    """Retrieves age structure date from UK Census 2011.

    Data is taken from the KS102EW table from the UK Census 2011.
    Data is retrieved from nomis, see https://www.nomisweb.co.uk.
    """
    url = (
        "https://www.nomisweb.co.uk/api/v01/dataset/{}.data.csv" +
        "?date=latest&geography={}&rural_urban=0&measures=20100" +
        "&select=geography_code,cell_name,obs_value").format(
        NOMIS_KS102EW_DATASET_ID,
        study_area.nomis_geo_codes(geographical_layer)
    )
    r = requests.get(url)
    df = pd.read_csv(io.BytesIO(r.content))
    df = df.pivot(
        index='GEOGRAPHY_CODE',
        columns='CELL_NAME',
        values='OBS_VALUE'
    )[list(AGE_STRUCTURE_MAP.keys())].astype(np.int64)
    df = df.rename(columns=AGE_STRUCTURE_MAP).groupby(lambda x: x, axis=1).sum()
    return df




def read_household_type_data(study_area=StudyArea.HARINGEY,
                             geographical_layer=GeographicalLayer.LSOA):
    """Retrieves household type date from UK Census 2011.

    Data is taken from the QS116EW table from the UK Census 2011.
    Data is retrieved from nomis, see https://www.nomisweb.co.uk.
    """
    url = ("https://www.nomisweb.co.uk/api/v01/dataset/{}.data.csv" +
           "?date=latest&geography={}&rural_urban=0&measures=20100" +
           "&select=geography_code,c_ahthuk11_name," +
           "obs_value").format(NOMIS_QS116EW_DATASET_ID,
                               study_area.nomis_geo_codes(geographical_layer))
    r = requests.get(url)
    df = pd.read_csv(io.BytesIO(r.content))
    df = df.pivot(
        index='GEOGRAPHY_CODE',
        columns='C_AHTHUK11_NAME',
        values='OBS_VALUE'
    )[list(HOUSEHOLDTYPE_MAP.keys())].astype(np.int64)
    df = df.rename(columns=HOUSEHOLDTYPE_MAP).groupby(lambda x: x, axis=1).sum()
    return df


def read_qualification_level_data(study_area=StudyArea.HARINGEY,
                                  geographical_layer=GeographicalLayer.LSOA):
    """Retrieves highest qualification level data from UK Census 2011.

    Data is taken from the KS501EW table from the UK Census 2011.
    Data is retrieved from nomis, see https://www.nomisweb.co.uk.
    """
    url = (
        "https://www.nomisweb.co.uk/api/v01/dataset/{}.data.csv" +
        "?date=latest&geography={}&rural_urban=0&measures=20100" +
        "&select=geography_code,cell_name,obs_value").format(
        NOMIS_KS501EW_DATASET_ID,
        study_area.nomis_geo_codes(geographical_layer)
    )
    r = requests.get(url)
    df = pd.read_csv(io.BytesIO(r.content))
    df = df.pivot(
        index='GEOGRAPHY_CODE',
        columns='CELL_NAME',
        values='OBS_VALUE'
    )[list(QUALIFICATION_MAP.keys())].astype(np.int64)
    df = df.rename(columns=QUALIFICATION_MAP).groupby(lambda x: x, axis=1).sum()
    return df


def read_economic_activity_data(study_area=StudyArea.HARINGEY,
                                geographical_layer=GeographicalLayer.LSOA):
    """Retrieves economic activity data from UK Census 2011.

    Data is taken from the KS601EW table from the UK Census 2011.
    Data is retrieved from nomis, see https://www.nomisweb.co.uk.
    """
    url = (
        "https://www.nomisweb.co.uk/api/v01/dataset/{}.data.csv" +
        "?date=latest&geography={}&rural_urban=0&measures=20100" +
        "&c_sex=0" +
        "&select=geography_code,cell_name,obs_value").format(
        NOMIS_KS601EW_DATASET_ID,
        study_area.nomis_geo_codes(geographical_layer)
    )
    r = requests.get(url)
    df = pd.read_csv(io.BytesIO(r.content))
    df = df.pivot(
        index='GEOGRAPHY_CODE',
        columns='CELL_NAME',
        values='OBS_VALUE'
    )[list(ECONOMIC_ACTIVITY_MAP.keys())].astype(np.int64)
    df = df.rename(columns=ECONOMIC_ACTIVITY_MAP).groupby(lambda x: x, axis=1).sum()
    return df


def read_pseudo_individual_data(study_area=StudyArea.HARINGEY,
                                geographical_layer=GeographicalLayer.LSOA):
    """Creates pseudo feature data for people.

    The data set will be equivalent to the population sum.
    """
    data = read_age_structure_data(study_area, geographical_layer)
    data[Pseudo.SINGLETON] = data.sum(axis=1)
    return data[[Pseudo.SINGLETON]]


def read_pseudo_household_data(study_area=StudyArea.HARINGEY,
                               geographical_layer=GeographicalLayer.LSOA):
    """Creates pseudo feature data for households.

    The data set will be equivalent to the household sum.
    """
    data = read_household_type_data(study_area, geographical_layer)
    data[Pseudo.SINGLETON] = data.sum(axis=1)
    return data[[Pseudo.SINGLETON]]
