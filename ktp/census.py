"""Census related functions and mappings.

For defintions of any of the terms see [the original glossary]
(http://www.ons.gov.uk/ons/guide-method/census/2011/census-data/2011-census-data/2011-first-release/
2011-census-definitions/2011-census-glossary.pdf).
"""
from enum import Enum
from pathlib import Path
import io
import zipfile
import tempfile

import requests
import numpy as np
import pandas as pd

LABOUR_URL = 'https://files.datapress.com/london/dataset/2011-census-labour-and-qualifications/visualisation-data-labour.zip'
QUALIFICATION_URL = 'https://files.datapress.com/london/dataset/2011-census-labour-and-qualifications/visualisation-data-qualifications.zip'
WARD_POPULATION_URL = 'https://files.datapress.com/london/dataset/2011-census-demography/ward-pop-ONS-GLA-Census.xls'
BOROUGH_POPULATION_URL = 'https://files.datapress.com/london/dataset/2011-census-demography/london-unrounded-data.xls'
HOUSEHOLD_URL = 'https://files.datapress.com/london/dataset/2011-census-households-families/visualisation-data-households.zip'
HOUSING_URL = 'https://files.datapress.com/london/dataset/2011-census-housing/visualisation-data-housing.zip'

LABOUR_FILE_PATH = Path('./LABOUR.xlsx')
QUALIFICATION_FILE_PATH = Path('./QUALIFICATIONS.xlsx')
HOUSEHOLDS_FILE_PATH = Path('./HOUSEHOLDS.xlsx')
HOUSING_FILE_PATH = Path('./HOUSING.xlsx')


class OrderedEnum(Enum):
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class HouseholdType(OrderedEnum):
    """Simplified household type derived from census household type."""
    ONE_PERSON_HOUSEHOLD = 1
    COUPLE_WITH_DEPENDENT_CHILDREN = 2
    COUPLE_WITHOUT_DEPENDENT_CHILDREN = 3
    LONE_PARENT_WITH_DEPENDENT_CHILDREN = 4
    MULTI_PERSON_HOUSEHOLD = 5


class Qualification(OrderedEnum):
    NO_QUALIFICATIONS = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_45 = 4
    APPRENTICESHIP = 5
    OTHER_QUALIFICATION = 6
    BELOW_16 = 7


class Labour(OrderedEnum):
    EMPLOYEE_PART_TIME = 1
    EMPLOYEE_FULL_TIME = 2
    SELF_EMPLOYED = 3
    UNEMPLOYED = 4
    ACTIVE_FULL_TIME_STUDENT = 5
    RETIRED = 6
    INACTIVE_FULL_TIME_STUDENT = 7
    LOOKING_AFTER_HOME = 8
    LONG_TERM_SICK = 9
    INACTIVE_OTHER = 10
    BELOW_16 = 11
    ABOVE_74 = 12


LABOUR_MAP = {
    'Economically active: Employee: Part-time': Labour.EMPLOYEE_PART_TIME,
    'Economically active: Employee: Full-time': Labour.EMPLOYEE_FULL_TIME,
    'Economically active: Self-employed': Labour.SELF_EMPLOYED,
    'Economically active: Unemployed': Labour.UNEMPLOYED,
    'Economically active: Full-time student': Labour.ACTIVE_FULL_TIME_STUDENT,
    'Economically inactive: Retired': Labour.RETIRED,
    'Economically inactive: Student (including full-time students)':
        Labour.INACTIVE_FULL_TIME_STUDENT,
    'Economically inactive: Looking after home or family': Labour.LOOKING_AFTER_HOME,
    'Economically inactive: Long-term sick or disabled': Labour.LONG_TERM_SICK,
    'Economically inactive: Other': Labour.INACTIVE_OTHER
}


QUALIFICATION_MAP = {
    'No qualifications': Qualification.NO_QUALIFICATIONS,
    'Level 1': Qualification.LEVEL_1,
    'Level 2': Qualification.LEVEL_2,
    'Apprenticeship': Qualification.APPRENTICESHIP,
    'Level 3': Qualification.LEVEL_3,
    'Level 4/5': Qualification.LEVEL_45,
    'Other qualificatinon': Qualification.OTHER_QUALIFICATION
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


def read_households(borough_name):
    return _read_census_file(
        url=HOUSEHOLD_URL,
        filename=HOUSEHOLDS_FILE_PATH,
        borough_name=borough_name
    )


def read_qualification(borough_name):
    return _read_census_file(
        url=QUALIFICATION_URL,
        filename=QUALIFICATION_FILE_PATH,
        borough_name=borough_name
    )


def read_labour_data(borough_name):
    return _read_census_file(
        url=LABOUR_URL,
        filename=LABOUR_FILE_PATH,
        borough_name=borough_name
    )


def read_ward_population_data(borough_name):
    """Reads census 2011 demographic data on ward level from the London data store.

    The dataset is reduced to the specified borough and ward resolution.
    All other data is discarded.
    """
    r = requests.get(WARD_POPULATION_URL)
    df = pd.read_excel(
        io.BytesIO(r.content),
        sheetname='2011 Census',
        skiprows=[0],
        header=[0]
    )
    df = df.ix[:, :23] # only totals, cut sex specifics
    df = df[df.Borough == borough_name]
    del df['Borough']
    del df['Persons: All Ages'] # cut totals
    del df['Ward Code']
    df.set_index('Ward Name', inplace=True)
    return df


def read_borough_population_data(borough_name):
    """Reads census 2011 demographic data on borough level from the London data store."""
    r = requests.get(BOROUGH_POPULATION_URL)
    df = pd.read_excel(
        io.BytesIO(r.content),
        sheetname='Persons',
        skiprows=[0],
        header=[0]
    )
    df.drop(df.columns[[0, 2]], axis=1, inplace=True)
    df.drop([0, 34, 35, 36, 37, 38], axis=0, inplace=True)
    df.rename(columns={'Unnamed: 1': 'ward'}, inplace=True)
    df.set_index('ward', inplace=True)
    df = df.astype(np.int16)
    return df.ix['Haringey', :]


def _read_census_file(url, filename, borough_name):
    """Reads census 2011 data from the London data store.

    There doesn't seem to be a consistent formatting of the census data in the data store,
    but _many_ datasets follow a certain convention which is used here.

    The dataset is reduced to a certain borough and ward resolution. All other data is discarded.
    """
    r = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    with tempfile.TemporaryDirectory(prefix='london-census-files') as tmpdir:
        z.extractall(path=tmpdir)
        path_to_temp_file = Path(tmpdir) / filename
        df = pd.read_excel(
            path_to_temp_file,
            sheetname='2011 Data',
            skiprows=[0],
            header=[0]
        )
    df.rename(columns={'Unnamed: 1': 'area_type'}, inplace=True)
    df['area_type'] = df['area_type'].ffill()
    df = df[(df.DISTLABEL == borough_name) & (df.area_type == 'ward')]
    del df['DISTLABEL']
    del df['area_type']
    del df['ZONEID']
    del df['Unnamed: 2']
    df.set_index('ZONELABEL', inplace=True)
    df.index.rename('ward', inplace=True)
    return df
