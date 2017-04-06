from collections import namedtuple
from itertools import chain
import math

from .hipf import fit_hipf

Household = namedtuple('Household', ['id', 'seedId', 'householdType', 'region'])
Citizen = namedtuple('Citizen', ['householdId', 'markovId', 'initialActivity'])


def run_hipf(param_tuple):
    """Performs HIPF for a single geographical region.

    This function is intened to be used with `multiprocessing.imap_unordered` which allows
    only one parameter, hence the inconvenient tuple parameter design.

    See `ktp.hipf.fit_hipf` for further information on the algorithm and parameters.

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
    number_households = sum(controls_hh[list(controls_hh.keys())[0]].values())
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
    return [Household(household_id, seed_hh_ids, seed.ix[(seed_hh_ids), :].iloc[0].hhtype, region)
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
    return list(chain(*([Citizen(householdId=household.id,
                                 markovId=row.markov_id,
                                 initialActivity=row.initial_activity)
                        for index, row in seed.ix[household.seedId, :].iterrows()]
                        for household in households)))
