from collections import namedtuple
from enum import Enum
from itertools import chain
import math

from .hipf import fit_hipf
from .types import AgeStructure, EconomicActivity, HouseholdType, Qualification, Pseudo, Carer,\
    PersonalIncome, PopulationDensity, Region
from .tus import AGE_MAP, ECONOMIC_ACTIVITY_MAP, HOUSEHOLDTYPE_MAP, QUALIFICATION_MAP, PSEUDO_MAP,\
    CARER_MAP, PERSONAL_INCOME_MAP, POPULATION_DENSITY_MAP, REGION_MAP
from .census import read_age_structure_data, read_household_type_data, \
    read_qualification_level_data, read_economic_activity_data,\
    read_pseudo_individual_data, read_pseudo_household_data

Household = namedtuple('Household', ['id', 'seedId', 'region'])
Citizen = namedtuple('Citizen', ['householdId', 'markovId', 'initialActivity',
                                 'activeMetabolicRate', 'passiveMetabolicRate', 'randomSeed'])

RANDOM_SEED = 123456789
MAX_HOUSEHOLD_SIZE = 70


def _unimplemented_census_read_function(geographical_layer):
    # lambda function cannot raise errors, hence the function definition here
    raise NotImplementedError()


class HouseholdFeature(Enum):
    """Household features to be used as controls in the creation of a synthetic population."""
    PSEUDO = (Pseudo, 'CHILD', PSEUDO_MAP, read_pseudo_household_data) # 'CHILD' is arbitrary
    HOUSEHOLD_TYPE = (HouseholdType, 'HHTYPE4', HOUSEHOLDTYPE_MAP, read_household_type_data)
    POPULATION_DENSITY = (PopulationDensity, 'POP_DEN2', POPULATION_DENSITY_MAP,
                          _unimplemented_census_read_function)
    REGION = (Region, 'GORPAF', REGION_MAP, _unimplemented_census_read_function)

    def __init__(self, uo_type, tus_variable_name, tus_mapping, census_read_function):
        self.uo_type = uo_type
        self.tus_variable_name = tus_variable_name
        self.tus_mapping = tus_mapping
        self._census_read_function = census_read_function

    def __repr__(self):
        return str(self)

    def tus_value_to_uo_value(self, feature_values, age):
        return feature_values.map(self.tus_mapping)
        return new_values

    def read_census_data(self, geographical_layer):
        return self._census_read_function(geographical_layer)


class PeopleFeature(Enum):
    """People features to be used as controls in the creation of a synthetic population.

    These features are as well used to cluster the seed in order to form markov chains
    for these clusters.
    """
    PSEUDO = (Pseudo, True, True, 'CHILD', PSEUDO_MAP, read_pseudo_individual_data)
    AGE = (AgeStructure, True, True, 'IAGE', AGE_MAP, read_age_structure_data)
    ECONOMIC_ACTIVITY = (EconomicActivity, False, False, 'ECONACT2',
                         ECONOMIC_ACTIVITY_MAP, read_economic_activity_data)
    QUALIFICATION = (Qualification, False, True, 'HIQUAL4', QUALIFICATION_MAP,
                     read_qualification_level_data)
    CARER = (Carer, True, True, 'PROVCARE', CARER_MAP, _unimplemented_census_read_function)
    PERSONAL_INCOME = (PersonalIncome, False, True, 'TOTPINC', PERSONAL_INCOME_MAP,
                       _unimplemented_census_read_function)

    def __init__(self, uo_type, includes_below_16, includes_above_74,
                 tus_variable_name, tus_mapping, census_read_function):
        self.uo_type = uo_type
        self.tus_variable_name = tus_variable_name
        self.tus_mapping = tus_mapping
        self._includes_below_16 = includes_below_16
        self._includes_above_74 = includes_above_74
        self._census_read_function = census_read_function

    def __repr__(self):
        return str(self)

    def tus_value_to_uo_value(self, feature_values, age):
        new_values = feature_values.map(self.tus_mapping)
        if not self._includes_below_16:
            new_values[age < 16] = self.uo_type.BELOW_16
        if not self._includes_above_74:
            new_values[age > 74] = self.uo_type.ABOVE_74
        return new_values

    def read_census_data(self, geographical_layer):
        data = self._census_read_function(geographical_layer)
        if not self._includes_below_16:
            usual_residents = PeopleFeature.AGE.read_census_data(geographical_layer)
            younger_than_sixteen = usual_residents.ix[:, :AgeStructure.AGE_15].sum(axis=1)
            data[self.uo_type.BELOW_16] = younger_than_sixteen
        if not self._includes_above_74:
            usual_residents = PeopleFeature.AGE.read_census_data(geographical_layer)
            older_than_74 = usual_residents.ix[:, AgeStructure.AGE_75_TO_84:].sum(axis=1)
            data[self.uo_type.ABOVE_74] = older_than_74
        return data


def run_hipf(param_tuple):
    """Performs HIPF for a single geographical region.

    This function is intened to be used with `multiprocessing.imap_unordered` which allows
    only one parameter, hence the inconvenient tuple parameter design.

    See `urbanoccupants.hipf.fit_hipf` for further information on the algorithm and parameters.

    Parameters:
        * param_tuple(0): the seed for the fitting
        * param_tuple(1): the controls for the households
        * param_tuple(2): the controls for the individuals
        * param_tuple(3): the region string, not used here, only bypassed

    Returns:
        a tuple of
            * param_tuple(3)
            * the fitted weights for the households in the seed
    """
    seed, controls_hh, controls_ppl, region = param_tuple
    number_households = list(controls_hh.values())[0].sum()
    household_weights = fit_hipf(
        reference_sample=seed,
        controls_households=controls_hh,
        controls_individuals=controls_ppl,
        residuals_tol=0.0001,
        weights_tol=0.0001,
        maxiter=100
    )
    assert number_households - household_weights.sum() < 0.1
    assert not any(household_weights.isnull())
    return (region, household_weights)


def sample_households(param_tuple):
    """Samples households from a seed with fitted weights.

    This function is intened to be used with `multiprocessing.imap_unordered` which allows
    only one parameter, hence the inconvenient tuple parameter design.

    Parameters:
        * param_tuple(0): the region string
        * param_tuple(1): the seed from which to sample
        * param_tuple(2): the fitted weights on household level
        * param_tuple(3): a random number for each household, to ensure reproducibility
        * param_tuple(4): an id for each household, to ensure reproducibility

    Returns:
        a list of Households
    """
    region, seed, household_weights, random_numbers, household_ids = param_tuple
    assert len(random_numbers) == len(household_ids)

    norm_hh_weights = household_weights / household_weights.sum()
    cum_norm_hh_weights = norm_hh_weights.cumsum()
    assert math.isclose(cum_norm_hh_weights[-1], 1, abs_tol=0.001)

    seed_hh_ids = (cum_norm_hh_weights[cum_norm_hh_weights >= random_number].index[0]
                   for random_number in random_numbers)
    return [Household(household_id, seed_hh_ids, region)
            for household_id, seed_hh_ids in zip(household_ids, seed_hh_ids)]


def sample_citizen(param_tuple):
    """Samples citizens from a seed for a given set of sampled households.

    This function is intened to be used with `multiprocessing.imap_unordered` which allows
    only one parameter, hence the inconvenient tuple parameter design.

    Parameters:
        * param_tuple(0): the households for which citizens should be sampled
        * param_tuple(1): the seed from which to sample

    Returns:
        a list of Citizens
    """
    households, seed = param_tuple
    return list(chain(
        *([Citizen(householdId=household.id,
                   markovId=row.markov_id,
                   initialActivity=row.initial_activity,
                   activeMetabolicRate=row.metabolic_rate_active,
                   passiveMetabolicRate=row.metabolic_rate_passive,
                   randomSeed=_citizen_random_seed(household.id, occupant_id))
          for occupant_id, (index, row) in enumerate(seed.ix[household.seedId, :].iterrows())]
          for household in households)))


def _citizen_random_seed(household_id, occupant_id):
    return RANDOM_SEED + household_id * MAX_HOUSEHOLD_SIZE + occupant_id
