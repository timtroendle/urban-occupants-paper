# Introduction and Related Works

* people have high impact on energy use for space heating, especially with buildings become more efficient, through:

    * control of heating/cooling system <!--- TODO add ref --->
    * ventilation <!--- TODO add ref --->
    * shading <!--- TODO add ref --->

* here: focus on control of heating/cooling system

* differentiate between statistical and top down methods and "physical" and bottom up methods
    * predictions of status quo could be made with data analysis, but predictions involving system changes, simulation is necessary

* similar work has been done on building, or district level, but not on the city scale incorporating people traits <!-- TODO add references --->

* somewhere here add vision, proof of concept model

[@Richardson:2008dj; @Muller:2010vx] shows a test citation. See also [Synthetic Population](#synthetic_population).

# Methodology

## Conceptual Model

### Model of Heating System Control

* generally, the heating set point for a heating Zone z can be described by $\theta_{set, z} = \theta_{set, z}(L_{P_z}, A_{P_z}, B_{P_z})$, where:

    * $P_z$: set of people inside the heating zone or related to it
    * $L_{P_z}$: location of People $P_z$
    * $A_{P_z}$: activity of People $P_z$
    * $B_{P_z}$: heating behaviour (comfort zone, awareness, financial situation, usage pattern) of People $P_z$

Here the following simplifications are made compared to the general model above:

* zones = entire dwellings
* location = presence
* discrete time with steps of 10 min length
* heating behaviour ignored

This leads to the simplified dynamic model of a heating set point for a dwelling d:

$\theta_{set, d, k} = \begin{cases}
    \text{off},             & \text{if } P_{d, k} = \varnothing\\
    \theta_{set, active},   & \text{if } \{p \in P_{d, k} | \text{p is active}\} \neq \varnothing\\
    \theta_{set, passive},  & \text{otherwise}
\end{cases}$

where:

* $k \in K = \text{{all time steps}}$
* $P_{d, k} = \{p \in P_d | \text{p is in dwelling d at time step k}\}$
* $\theta_{set, active}$: assumed static set point whenever dwelling is occupied by at least one active person
* $\theta_{set, passive}$: assumed static set point whenever dwelling is occupied by only passive people

### People Model

Time heterogeneous markov chain with the following states:

* not at home
* active at home
* asleep at home

### Thermal Model of Dwelling

Simplified 1 zone building energy model.

The model is derived from the hourly dynamic model in ISO 13790. It has only one capacity and one resistance.

Compared to the ISO 13790 there is

* only metabolic heat gain,
* full shading of the building, no direct or indirect sun light,
* no windows or doors,
* no ventilation,
* immediate heat transfer between air and surface.

![Average thermal power per ward](../doc/figures/simple-simple.jpg){#simple-simple .class width=300}

$\theta_{m, k} = \theta_{m, k-1} \cdot (1 - \frac{\Delta{t}}{C_{m}} \cdot H_{tr, em}) + \frac{\Delta{t}}{C_m} \cdot (\Phi_{HC, nd, k-1} + H_{tr, em} \cdot \theta_{e, k-1})$

where

<!--- FIXME many of the following not in equation --->
<!--- TODO add metabolic heat gain --->
* $\Phi_{HC, nd, t}$: cooling or heating power at time k
* $\theta_{m, k}$: building temperature [℃] at time k
* $\theta_{e, k}$: outside temperature [℃] at time k
* $A_f$: conditioned floor area [m^2^]
* $C_m$: capacity of the building's heat mass [J/K]
* $\Delta{t}$: time step size [s]
* $H_{tr, em}$: heat transmission to the outside [W/K]
* $\theta_{int, set}$: heating set point temperature [℃]
* $\Phi_{max}$: maximum heating power [W]

## Simulation Platform

agent based simulation

## Model Calibration

### People Model

using time use survey data: cluster set of people by certain attributes (for example work status, role in household, household income, ...) and derive markov chain for all cluster of people.

The clustering must use and retain the features that will later be used for the synthetic population.

Possible procedure:

* create a people-model time series for each individual in the time use survey
* through feature selection identify the features of individuals that explain their day time series best using Cramer's V
* start selecting features starting from the most important one, as long as the remaining cluster will stay large enough (must be at at least > 20) (maybe using ANOVA, analysis of variance)
* cluster people by those features (simply by their different values) and calculate markov chain for all cluster
* (later below: use those features as control features for the synthetic population)

Discuss difficulty of problem: there is no _correct_ way of doing this.

### Synthetic Population {#synthetic_population}

Synthetic population using Hierarchical Iterative Proportional Fitting: fitting households and individuals at the same time

### Building Energy Model

Using the same model for each dwelling

Rational for using the exact same model for each dwelling: this can be seen similar to the normative building energy assessment where the object of study is the building and its impact on energy demand. Heating behaviour is considered external *and always equal*. Here, the object of study is the heating behaviour of people and its impact on energy demand. The building could be considered external *and always equal*.

# Case Study

short intro to London Haringey

describe data sets: UK Time Use Survey 2000, Census 2011

## Feature Selection Results

Discuss correlation of features between features and to the time series.

## Simulation Results

### Results for Time Triggered Strategy (optional)

### Results for Preferred Features

* discuss variation between wards in terms of energy usage and in terms of dynamic load profile

### Results for Alternative Feature Selection

![Average thermal power per ward](../doc/figures/thermal_power_per_ward.png)
![Average thermal power per LSOA](../doc/figures/thermal_power_per_lsoa.png)
![Average thermal power per LSOA choropleth](../doc/figures/thermal_power_lsoa_choropleth.png)
![Distribution of average power](../doc/figures/distributation-average-power.png)
![Thermal power vs household size](../doc/figures/thermal-power-vs-household-size.png)

# Discussion & Conclusion

# References
