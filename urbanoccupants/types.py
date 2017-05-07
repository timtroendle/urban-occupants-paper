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
