# Introduction and Related Works

* heating system set points have high impact on building energy usage, as shown in former research

* if, contrary to normative building energy assessment, one is interested in _actual_ energy usage and not normative energy usage, exact heating set points are hence of high importance

* predictions of status quo could be made with data analysis, but predictions involving system changes, simulation is necessary

* generally, the heating set point for a heating Zone z can be described by $\theta_{set, z} = \theta_{set, z}(L_{P_z}, A_{P_z}, B_{P_z})$, where:

    * $P_z$: set of people inside the heating zone or related to it
    * $L_{P_z}$ location of People $P_z$
    * $A_{P_z}$ activity of People $P_z$
    * $B_{P_z}$ heating behaviour (comfort zone, awareness, financial situation, usage pattern) of People $P_z$

* for all (comfort zone, location, activity, heating behaviour), the social context is important, which brings spatial dimension into play // TODO rational for the need of spatial dimension still weak

[@Richardson:2008dj; @Muller:2010vx] shows a test citation. See also [Synthetic Population](#synthetic_population).

# Methodology

## Conceptual Model

### Set Point Model

Here the following simplifications are made compared to the general model above:

* zones = entire dwellings
* location = presence
* discrete time with steps of 10 min length
* heating behaviour reduced to simple categories

This leads to the simplified dynamic model of a heating set point for a dwelling d: $\theta_{set, d, k} = \theta_{set, d, k}(P_{d, k}, a_{P, k}, B_{d})$, where:

* $k \in K = \text{{all time steps}}$
* $P_{d, k} = \{p \in P_d | \text{p is in dwelling d at time step k}\}$
* $a_{P, k} = 1$ if at least someone in $P_k$ awake, 0 otherwise
* $B_d = \text{{'constant set point', 'time triggered', 'presence & activity triggered'}}$, time invariant heating behaviour for dwelling d

### People Model

Time heterogeneous markov chain with the following states:

* not at home
* active at home
* asleep at home

### Thermal Model of Dwelling

See description of [conceptual model](https://github.com/timtroendle/spatial-cimo/blob/develop/doc/conceptual-model.md). // TODO update

Simplified 1 zone building energy model. Using the same model for each dwelling (?).

Rational for using the exact same model for each dwelling: this can be seen similar to the normative building energy assessment where the object of study is the building and its impact on energy demand. Heating behaviour is considered external *and always equal*. Here, the object of study is the heating behaviour of people and its impact on energy demand. The building could be considered external *and always equal*.

## Simulation Platform

agent based simulation

## Model Calibration

### People Model

using time use survey data: cluster set of people by certain attributes (for example work status, role in household, household income, ...) and derive markov chain for all cluster of people.

The clustering must use and retain the features that will later be used for the synthetic population.

Possible procedure:

* create a people-model time series for each individual in the time use survey
* through feature selection identify the features of individuals that explain their day time series best
* start selecting features starting from the most important one, as long as the remaining cluster will stay large enough (must be at at least > 20) (maybe using ANOVA, analysis of variance)
* cluster people by those features (simply by their different values) and calculate markov chain for all cluster
* (later below: use those features as control features for the synthetic population)

### Synthetic Population {#synthetic_population}

Synthetic population using Hierarchical Iterative Proportional Fitting: fitting households and individuals at the same time

## Optional: Identification of Heating behaviour

Using measured energy data and using Bayesian inference, estimate the likelihood for a certain heating behaviour in a region.

# Case Study

short intro to London Haringey

describe data sets: UK Time Use Survey 2000, Census 2011, (UKBuildings?)

## Model Calibration Results

which attributes are significant in terms of energy usage?

## Simulation Results

test beds: (a) deterministic versus proposed ABM apporach -- compare timing and magnitude of peak; (b) relative importance of setpoint versus timing and duration of use; (c) relative importance of physical characterstics of dwelling versus stochastic representation of occupant activities

![Average thermal power per ward](../doc/figures/thermal_power_per_ward.png)
![Average thermal power per LSOA](../doc/figures/thermal_power_per_lsoa.png)
![Average thermal power per LSOA choropleth](../doc/figures/thermal_power_lsoa_choropleth.png)
![Distribution of average power](../doc/figures/distributation-average-power.png)
![Thermal power vs household size](../doc/figures/thermal-power-vs-household-size.png)

### Impact of Population attributes on Energy Demand using Presence&Activity based heating

using the presence&activity based heating behaviour, run full simulation (for a week?) and discuss spatial patterns: different energy usage in certain regions based on population structure

### Energy Savings Potential

Run another full simulation with a baseline heating behaviour (only time triggered or a mix //TODO howto define realistically?) and compare to the presence&activity based heating. Are there spatial patterns?

### Likelihood of disaggregated heating behaviour

(optional): if possible, discuss likelihood of certain disaggregated heating behaviour per ward/lsoa

# Discussion & Conclusion

---

# Optional

Validate people's schedule against test data set.

Validate people's travels against London data set.

Validate energy simulation results. Goal: stay in certain *plausible* ranges.

Compare comfort level (temperature when home) for different HVAC control strategies.

# References
