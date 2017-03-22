# Energy Impact of Occupant Activity in Urban Built Environments

// TODO update title

## Abstract

// TODO update abstract

Occupants are driving the energy demand in buildings, either directly for example through the use of appliances, or more indirectly through comfort preferences like heating set points and the energy demand of auxiliary functions like fridges. The significance of occupants and their activities and behaviours for energy demand estimations has been identified in former studies and a lot of work is undertaken in quantifying this relationship and explicitly modelling occupants to understand and predict choices of activities and behaviours and their impact on energy demands in single households, public buildings and offices, and settlements of detached buildings.

On the district and urban scale occupants are still typically represented by implicit and general load profiles ignoring occupant activities as the main driver for energy demand, and ignoring spatial and temporal dependencies. This work aims at identifying the impact of occupant activity on the heating and cooling energy demand in buildings on an urban scale by representing occupants as agents in a city-wide model with high spatial and temporal resolution. The agent-based approach of the model allows for representing spatial variability and analysing space-time relationships by linking energy usage in space and time through occupants, their locations and activities. The model is applied in a case study of London.

## Introduction and Related Works

* heating system set points have high impact on building energy usage, as shown in former research

* if, contrary to normative building energy assessment, one is interested in _actual_ energy usage and not normative energy usage, exact heating set points are hence of high importance

* generally, the heating set point for a heating Zone z can be described by &theta;<sub>set, z</sub> = &theta;<sub>set, z</sub>(L<sub>P<sub>z</sub></sub>, A<sub>P<sub>z</sub></sub>, B<sub>P<sub>z</sub></sub>), where:

    * P<sub>z</sub>: set of people inside the heating zone or related to it
    * L<sub>P<sub>z</sub></sub> location of People P<sub>z</sub>
    * A<sub>P<sub>z</sub></sub> activity of People P<sub>z</sub>
    * B<sub>P<sub>z</sub></sub> heating behaviour (comfort zone, awareness, financial situation, usage pattern) of People P<sub>z</sub>

* for all (comfort zone, location, activity, heating behaviour), the social context is important, which brings spatial dimension into play // TODO rational for the need of spatial dimension still weak

## Methodology

### Conceptual Model

#### Set Point Model

Here the following simplifications are made compared to the general model above:

* zones = entire dwellings
* location = presence
* discrete time with steps of 10 min length
* heating behaviour reduced to simple categories

This leads to the simplified dynamic model of a heating set point for a dwelling d: &theta;<sub>set, d, k</sub> = &theta;<sub>set, d, k</sub>(P<sub>d, k</sub>, a<sub>P, k</sub>, B<sub>d</sub>), where:

* k in K = {all time steps}
* P<sub>d, k</sub> = {p in P<sub>d</sub> | p is in dwelling d at time step k}
* a<sub>P, k</sub> = 1 if at least someone in P<sub>k</sub> awake, 0 otherwise
* B<sub>d</sub> = {'constant set point', 'time triggered', 'presence & activity triggered'}, time invariant heating behaviour for dwelling d

#### People Model

Time heterogeneous markov chain with the following states:

* not at home
* active at home
* asleep at home
* active at other people's home (// TODO are these relevant? probably rather rarely alone in other people's home. When not alone, this additional person has no impact on energy demand.)
* asleep at other people's home

Location choice model:

* each person has a home
* when at other home must decide which (//TODO how? this is important as it links dwellings/households)

#### Thermal Model of Dwelling

See description of [conceptual model](https://github.com/timtroendle/spatial-cimo/blob/develop/doc/conceptual-model.md). // TODO update

Simplified 1 zone building energy model. Using the same model for each dwelling (?).

Rational for using the exact same model for each dwelling: this can be seen similar to the normative building energy assessment where the object of study is the building and its impact on energy demand. Heating behaviour is considered external *and always equal*. Here, the object of study is the heating behaviour of people and its impact on energy demand. The building could be considered external *and always equal*.

### Simulation Platform

agent based simulation

### Model Calibration

#### People Model

using time use survey data: classify set of people by certain attributes (for example work status, role in household, household income, ...) and derive markov chain for all classes of people. Possible procedures:

##### On the Household Level

* map all people features (attributes) to household features (attributes); e.g. labour status of all residents is mapped to
    * household feature 1: number of unemployed residents
    * household feature 2: number of employed residents
* // TODO why not doing everything on household level?!
* define norm dwelling used for all households (see above)
* simulate energy demand (for one day or week) for every household
* use regression (e.g. principal component regression) to identify relationship of all (categorical) features of the household with energy demand
* choose 2-4 most significant features to cluster seed
* calculate markov chain for each cluster

##### On the Individual Level

* define norm dwelling used for all households (see above)
* simulate energy demand (for one day or week) for every household
* map energy demand to person (when that person is driving energy demand by being at home, associate fraction of energy demand to that person); this will give a distribution of energy demands for the entire population (seed)
* use ANOVA (analysis of variance) to test whether clustering of individuals by certain attributes (for example labour status) explains the resulting per-person-energy-demand best

#### Location choice model // TODO unknown

#### Synthetic Population

Synthetic population using Hierarchical Iterative Proportional Fitting: fitting households and individuals at the same time

### Optional: Identification of Heating behaviour

Using measured energy data and using Bayesian inference, estimate the likelihood for a certain heating behaviour in a region.

## Case Study

short intro to London Haringey

describe data sets: UK Time Use Survey 2000, Census 2011, (UKBuildings?)

### Model Calibration Results

which attributes are significant in terms of energy usage?

// TODO should this be done with or without linkage of people (=other people's home)?

### Simulation Results

#### Impact of Population attributes on Energy Demand using Presence&Activity based heating

using the presence&activity based heating behaviour, run full simulation (for a week?) and discuss spatial patterns: different energy usage in certain regions based on population structure

#### Energy Savings Potential

Run another full simulation with a baseline heating behaviour (only time triggered or a mix //TODO howto define realistically?) and compare to the presence&activity based heating. Are there spatial patterns?

#### Likelihood of disaggregated heating behaviour

(optional): if possible, discuss likelihood of certain disaggregated heating behaviour per ward/lsoa

## Discussion & Conclusion

---

## Optional

Validate people's schedule against test data set.

Validate people's travels against London data set.

Validate energy simulation results. Goal: stay in certain *plausible* ranges.

Compare comfort level (temperature when home) for different HVAC control strategies.
