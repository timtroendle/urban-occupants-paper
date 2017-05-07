"""Defines all data types used in the study."""
from enum import Enum


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


class Pseudo(OrderedEnum):
    """This is a pseudo feature, that can be used instead of any real feature."""
    SINGLETON = 1


class AgeStructure(OrderedEnum):
    """The age structure of the population."""
    AGE_0_TO_4 = 0
    AGE_5_TO_7 = 1
    AGE_8_TO_9 = 2
    AGE_10_TO_14 = 3
    AGE_15 = 4
    AGE_16_TO_17 = 5
    AGE_18_TO_19 = 6
    AGE_20_TO_24 = 7
    AGE_25_TO_29 = 8
    AGE_30_TO_44 = 9
    AGE_45_TO_59 = 10
    AGE_60_TO_64 = 11
    AGE_65_TO_74 = 12
    AGE_75_TO_84 = 13
    AGE_85_TO_89 = 14
    AGE_90_AND_OVER = 15


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


class EconomicActivity(OrderedEnum):
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


class Carer(OrderedEnum):
    CARER = 1
    NO_CARER = 2


class PersonalIncome(OrderedEnum):
    BELOW_16 = 1
    LESS_THAN_GBP_215 = 2
    BETWEEN_GBP_215_AND_435 = 3
    BETWEEN_GBP_435_AND_870 = 4
    BETWEEN_GBP_870_AND_1305 = 5
    BETWEEN_GBP_1305_AND_1740 = 6
    BETWEEN_GBP_1740_AND_2820 = 7
    BETWEEN_GBP_2820_AND_3420 = 8
    BETWEEN_GBP_3420_AND_3830 = 9
    BETWEEN_GBP_3830_AND_4580 = 10
    BETWEEN_GBP_4590_AND_6670 = 11
    ABOVE_GBP_6670 = 12


class PopulationDensity(OrderedEnum):
    UP_TO_249 = 1
    BETWEEN_250_AND_999 = 2
    BETWEEN_1000_AND_1999 = 3
    BETWEEN_2000_AND_2999 = 4
    BETWEEN_3000_AND_3999 = 5
    BETWEEN_4000_AND_4999 = 6
    MORE_THAN_5000 = 7


class Region(OrderedEnum):
    LONDON = 1
    NORTH_EAST = 2
    WALES = 3
    SCOTLAND = 4
    NORTHERN_IRELAND = 5
    NORTH_WEST_INCL_MERSEYSIDE = 6
    YORKSHIRE_AND_HUMBERSIDE = 7
    EAST_MIDLANDS = 8
    WEST_MIDLANDS = 9
    EASTERN = 10
    SOUTH_EAST_EXCL_LONDON = 11
    SOUTH_WEST = 12
