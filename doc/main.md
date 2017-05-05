# Introduction and Related Works

Accounting for 34% of global energy end-use, the building sector is the largest energy sink and a major contributor to global CO~2~ emissions [@GEA:2012us]. Three quarters of this amount are accountable for space heating and cooling purposes. When trying to reduce this energy impact as it is done by the European Union [@Parliament:2012ut] understanding the energy demand originating in the building sector and its drivers is crucial. With more than half of the global population living in cities and with on-going urbanisation [@UnitedNations:2014uy], urban build environments are becoming more important in this regard. This is even more so true when looking at America or Europe where the urban population exceeds 70% of the total population already today [@UnitedNations:2014uy]. Estimations of energy demand for space heating are valuable during the design phase of urban build environment and its energy supply infrastructure, but also for effective retrofitting actions and performance evaluations. In particular the task of designing efficient energy supply systems asks for a high temporal resolution of the estimation [@Omu:0ca]. The built infrastructure and other factors impacting energy demand for space heating are diversely distributed in urban environments and hence analyses have recently been done on a high spatial resolution as well [@Choudhary:0kp; @Li:wp; @Anonymous:0gi].

While thermodynamic models of buildings are well understood and assumed to achieve good results, simulated energy demand for space heating in urban environments deviate largely from measured data which is often accounted to micro-climate effects [@Kolokotroni:2008kg; @Steemers:2003kd] and to the impact of occupants [@GuerraSantin:2012im; @Seryak:2003hn; @Fabi:2012gu; @Janda:2011cy]. "Buildings don't use energy: people do" [@Janda:2011cy] and hence the energy usage in a building can be accounted directly or indirectly to the way people use buildings. In residential homes people's impact on space heating demands stems mostly from the way people control the heating, cooling, and ventilation (HVAC) systems, the way people actively ventilate their buildings through window and door opening, the way people shade their rooms through blinds and curtains, the way people functionally divide their residential homes, and people's occupancy and activities performed at home which attribute in the form of heat gains [@VanRaaij:1983kt; @Paauw:2009uw]. Given the complex nature of human behaviour a comprehensive understanding of the driving forces, relationships, and feedbacks is difficult, several factors like awareness [@Janda:2011cy], socio-economic situations [@Druckman:2009kx], and rebound effects are discussed [@Edelson:1980gj; @Brannlund:2007jg]. Given the trend towards zero-energy buildings in which thermal losses are largely reduced, the impact of occupants on energy demand is relatively increasing [@Janda:2011cy] stressing the importance to account for and understand the relationships.

Several methods for modelling energy demand in buildings have been proposed. Swan and Ugursal [@Swan:2009fb] differentiate methods for modelling end-use energy demand in the residential sector into those following a top-down approach, and those following a bottom-up approach, depending on whether input data from the hierarchical level below the system under consideration is incorporated or not. For the bottom up models a differentiation is made between statistical methods in which historic consumption data is regressed onto explaining variables, and those which incorporate physical models of the building envelope and the thermodynamic processes in them which are typically referred to as engineering methods. While the data driven methods yield models that can be applied to buildings of the same archetype, only the latter allows to simulate so far unseen effects, e.g. through the introduction of new technologies. Occupants must be modelled explicitly in engineering models. On the city scale, former work include high resolution building by building models without explicit influence of occupancy [@tian2015high; @zhang2015gshp; @Li:wp], and models including people behaviour but only in aggregated form on lower spatial resolution [@BustosTuru:2016ee].

The comprehensive behaviour of occupants is typically tried to represent through several sub-models. A foundation to most of them form occupancy models determining at which point of time the building is occupied [@Richardson:2008dj; @Aerts:2015ko; @Widen:2009fo]; sometimes even disaggregated into zones of the building [@Liao:2012et]. On top of those, activity models [@Widen:2009kx; @Aerts:2015ko], window opening models [@Andersen:2013cn; @Fabi:2013tl], and HVAC control models [@Fabi:2013ch] are placed. Behaviour models are typically differentiated between deterministic and probabilistic types. Deterministic models assume a direct causal link between a driver of a certain behaviour and the actual derived action. While different methods exist, these types of models are based on rational decision making. Probabilistic models in contrast are based on likelihoods of different actions. The data source for occupancy and activity models form in many cases so called time use survey (TUS) data sets for which a standardising research centre exists [@ctus].

This paper reports the progress of on-going work of introducing models of people behaviour to high resolution bottom up city models. The model estimates energy demand for space heating in residential buildings on a city scale. Energy demand is driven by the occupancy of people in their households which itself is modelled through a time-heterogeneous Markov chain based on TUS data. Citizens are clustered through features of themselves and of the households they live in. A statistically viable urban population is formed through population synthesis. The model allows to analyse spatial patterns of energy use for space heating. It is implemented as an open-source agent-based model [@energyagents] which allows easy integration of other bottom-up effects impacting energy demand for space heating like people movement, people interactions, activity models, and urban microclimates, other energy uses like water heating and electricity, other environmental impacts e.g. on air quality, or the supply side of building energy.

This paper is structured as follows: section 2 describes the conceptual model and a general way how time use data and census data can be used to calibrate it. Simulation results for a case study of Haringey, a borough of London are presented in section 3, and section 4 concludes the findings.

# Methodology

## Conceptual Model

The general urban energy system as applied in this study consists of three distinct entities: citizens, HVAC controls, and dwellings whose models will be described in detail in the following sub sections. A dwelling forms a home for one to $n$ citizens and incorporates exactly one HVAC control system. [Fig. 1](#flow-chart-time-step) shows a flow-chart of the model. The model is time-step based where in each time step $k$, each entity updates its state: first all citizens update their occupancy, i.e. determine whether they are at home or not. Second, the HVAC control system of each dwelling updates its heating set point, potentially taken into account the occupancy of the dwelling. Lastly, each dwelling updates its indoor temperature and the thermal power needed for reaching it.

![Figure 1: Flow chart of a single time step](../doc/figures/flow-chart-time-step.png){#flow-chart-time-step .class width=500}

### Heating System Control Model

Generally, the heating set point for a heating zone $z$ can be described by $\theta_{set, z} = \theta_{set, z}(L_{P_z}, A_{P_z}, B_{P_z})$, where:

* $P_z$: set of people inside the heating zone or related to it;
* $L_{P_z}$: locations of people $P_z$;
* $A_{P_z}$: activities of people $P_z$;
* $B_{P_z}$: heating behaviour, defined by the comfort zone, awareness, socio-economic situation, usage pattern, etc. of people $P_z$.

For the simulation model of the heating system controls applied in this study the following simplifications are made compared to the general model as defined above:

* zones are entire dwellings;
* time is discrete;
* location is equal to presence, i.e. we do not incorporate indoor positions;
* heating behaviour is based on occupancy only.

The smallest unit considered is a dwelling $d$, by which we mean the fraction of a building that has a distinct energy meter and is occupied by a single household. Each dwelling $d$ is of the set $D$, i.e. of the urban residential building stock. $P_k^d$ is defined as a subset of the entire urban population $P$ comprising of all people that occupy dwelling $d$ at time $k$. Given these definitions, the heating set point for dwelling $d$ at time $k \in K$ is defined as:

$$\theta_{set, k}^d = \begin{cases}
    \theta_{set, absent}^d,   & \text{if } P_k^d = \varnothing\\
    \theta_{set, active}^d,   & \text{if } \{p \in P_k^d | \text{p is active}\} \neq \varnothing\\
    \theta_{set, passive}^d,  & \text{otherwise}
\end{cases}.$$

In this model, there are there are three distinct heating set points between which the control system toggles depending on occupancy. It shall be noted that given the desired comfort level defined by the set point temperatures $\theta_{set, absent}^d \leq \theta_{set, passive}^d \leq \theta_{set, active}^d$ this controller is close to optimal in terms of energy efficiency as the dwelling is minimally heated. As indoor temperature lags behind occupancy it is not optimal in terms of comfort level. This effect is particularly strong when occupants enter a dwelling whose indoor temperature is far from $\theta_{set, active}^d$ or $\theta_{set, passive}^d$.

### Occupancy Model

Citizens are modelled by the occupancy in their respective dwellings only, using a probabilistic occupancy model that has been applied in several similar studies [@Richardson:2008dj; @Widen:2009fo; @Aerts:2015ko]. The occupancy model consists of a time-heterogeneous Markov chain with the following states: (1) not at home, (2) active at home, and (3) asleep at home. As the Markov chain is time heterogeneous, transition probabilities between the states of the Markov chain are time dependent, and hence the transition matrix for person $p$ at time $k$ can be given as:

$$
Pr^p =
\begin{bmatrix}
    p_{11}^p(k)&p_{12}^p(k)&p_{13}^p(k)\\
    p_{21}^p(k)&p_{22}^p(k)&p_{23}^p(k)\\
    p_{31}^p(k)&p_{32}^p(k)&p_{33}^p(k)
\end{bmatrix}.
$$

Every person has exactly one home, so we can define a time-invariant set of people $P_d$ for every dwelling $d$ such that the family of sets $P_D = \{P_d | \forall d \in D\}$ form a partition of population $P$ and $\cup_{d \in D} P_d = P$ and $P_{d_1} \cap P_{d_2} = \varnothing \ \forall \ d_1 \neq d_2$ hold. The time dependent set of occupancy of dwelling $d$ at time $k$ as used in the heating system control model can then be given as $P_k^d = \{p \in P_d | \text{p is active at home or p is asleep at home} \}$.

<!--- TODO add initial state --->

### Thermal Dwelling Model

Dwellings are modelled as single thermal zones following the conceptual model of EN ISO 13790 [@cen13790:2008]. The model is derived from the simple hourly dynamic model as described in the standard but is reduced to a single capacity and a single resistance as depicted in [Fig. 2](#simple-simple). Compared to the full model there is no other than metabolic heat gain, full shading of the building, i.e. no direct or indirect sun light, no windows or doors, no ventilation, and immediate heat transfer between air and surface. Furthermore, heat transfer between dwellings is ignored.

![Figure 2: RC network of the applied dynamic thermal model of a dwelling](../doc/figures/simple-simple.jpg){#simple-simple .class width=300}

The time discrete difference equation of the indoor temperature $\theta_{m, k}^d$ of dwelling $d$ is given as:

$$\theta_{m, k}^d = \theta_{m, k-1}^d \cdot (1 - \frac{\Delta{t}}{C_{m}^d} \cdot H_{tr, em}^d) + \frac{\Delta{t}}{C_m^d} \cdot (\Phi_{HC, nd, k-1}^d + \Phi_{int,Oc, k}^d + H_{tr, em}^d \cdot \theta_{e, k-1}),$$

where

* $\Phi_{HC, nd, k}^d$: heating power at time k [W],
* $\Phi_{int,Oc, k}^d$: metabolic heat gain of occupants at time k [W],
* $C_m^d$: capacity of the dwellings's heat mass [J/K],
* $H_{tr, em}^d$: heat transmission to the outside [W/K],
* $\theta_{e, k}$: outside temperature [℃] at time k,
* $\Delta{t}$: time step size [s].

The unknown and bounded heating power $\Phi_{HC, nd, k}^d$ is determined by the need to reach the set point temperature as defined by the heating system control. According to [@cen13790:2008] it is assumed that the controller has a perfect dwelling model and can hence determine the necessary heating power in an precise manner.

## Simulation Model

The distinct sub models of the heating control systems, the dwellings, and the citizens, are linked and implemented in an open-source simulation model [@energyagents]. While the conceptual models as defined above would allow for a separate, three stages approach of simulation, in which citizens occupancy is simulated first, heating set points are simulated consecutively, and indoor temperatures and thermal powers of dwellings are simulated as a last step, the model has been implemented in an agent-based manner in which these three stages are simulated consecutively. This will allow amending the model by aspects which add other relationships between the layers than the one depicting in [Fig. 1](#flow-chart-time-step).

## Model Calibration

The following subsection describes methods to calibrate the conceptual model as defined above. In particular two types of data sets are taken into account: (1) time use survey (TUS) data and (2) aggregated census data, which both are available for many regions of the world, in the case of TUS data even in a standardised manner [@ctus]. The TUS data is used to calibrate the occupancy model, whereas the aggregated census data is used to generate a synthetic population. In addition to these, a micro sample of census data is necessary, i.e. fully detailed census data for a fraction of the population. For the approach describe in this study, that data must be available in the TUS data set, i.e. for each participant whose time use is recorded in the study, we will demand features of the participant as well, e.g. their socio-economic situation.

### Occupancy Model

The transition matrix $Pr^p$ for each citizen is derived from the TUS data set. The TUS data set contains location and activity data for each participant at a high temporal resolution in the form of a diary. Diaries span at least a day, though typically a weekday and a weekend day are recorded as time use varies between these days [@ctus]. In the following, a mapping is performed from each tuple of location and activity to one of the states of the Markov chain. As an example, the tuple (location = 'workplace or school', activity = 'lunch break') is mapped to 1 = not at home, as is (location = 'second home or weekend house', activity = 'sleep'). After the mapping, each diary can be understood as a concrete instance of a stochastic process that is described by the time heterogeneous Markov chain of the occupancy model. The set of participants is clustered by one or more household or people features $F$, e.g. age, which is available in both, the TUS data set and the aggregated census, and a time-heterogeneous Markov chain for each cluster following the approach used e.g. by [@Richardson:2008dj; @Widen:2009fo] is created. The resulting set of transition matrices $\{Pr^f| \forall f \in F\}$ then allows us to deterministically allocate a transition matrix to a citizen based on the citizens feature value $f^p$: $Pr^p = Pr^{f^p}$.

The choice of household or people features is important for the quality of this approach. Unfortunately we are not aware of a deterministic way of choosing the _correct_ set of features. We instead acknowledge the inherent uncertainty and analyse features, their correlation among each other, and their correlation to the derived time series. We furthermore discuss the sensitivity of the results to the choice of features in the case study performed.

### Synthetic Population

The urban scale occupancy model as described above needs information on household composition of every household, and household and people feature vectors $f^p$ for every individual in the population of the study area. Such disaggregated data is typically not available and hence the population is synthesised from aggregated census data. Population synthesis as a way to initialise microsimulations has been applied in the past mainly in land use and transportation models [@Beckman:1996hv; @Arentze:2007cf] but more recently in energy models as well [@Anonymous:sQCtxREz]. [@Muller:2010vx; @Barthelemy:2012ws] provide overviews over the different approaches that are available.

In population synthesis the aim is to estimate the joint probability mass function $p_{F}$ for a set of $n$ features $F = \{F_1, F_2, ..., F_n\}$ which describes the correct distribution of those features in the actual population, given a set of marginal probability mass functions $p_{\tilde{F}}$ for a subset of features $\tilde{F} \subset F$. A simple example for the two-dimensional case of $F = \{\text{sex, age}\}$ is given in Table @tbl:popsynth-example, a contingency table in which the last column shows the probability mass function for the feature 'sex', the last row shows the probability mass function for the feature 'age', and the centre shows the unknown joint probability mass function $p_F$.

+--------+----------------------------+----------------------------+-------------------+
|        | below age 50               | above age 50               |                   |
+--------+----------------------------+----------------------------+-------------------+
|  male  | $p_F(\text{male, < 50)}$   | $p_F(\text{male, > 50)}$   | $p_{sex}(male)$   |
+--------+----------------------------+----------------------------+-------------------+
|  female| $p_F(\text{female, < 50)}$ | $p_F(\text{female, > 50)}$ | $p_{sex}(female)$ |
+--------+----------------------------+----------------------------+-------------------+
|        | $p_{age}(< 50)$            | $p_{age}(> 50)$             |                   |
+--------+----------------------------+----------------------------+-------------------+

Table: A two dimensional population synthesis problem. {#tbl:popsynth-example}

In the case of this study, the relationship between households and people must be retained when creating the synthetic population. Solutions for such hierarchical problems have been discussed in the past [@Ye:2009uw; @Muller:vs0R1Q2; @Pritchard:2011gy], and in our case we are following the approach of [@Muller:vs0R1Q2].

### Thermal Dwelling Model and Heating Control System

To be able to analyse the impact of occupants on the space heating energy demand in buildings, we are assuming the same physical conditions for all dwellings. We are hence defining a default dwelling and are allocating it to each household in the study area. This can be compared to normative building energy assessment where the object of study is the building and its impact on energy demand. Heating behaviour in these assessments is considered external to the object of study and equal among all buildings which allows to compare the physical structure of buildings only. Here, the object of study is the heating behaviour of occupants and its impact on energy demand. The physical structure of the building is considered external to the object of study and always equal among all households. Equal configuration is assumed for the heating control system as well.

## Summary of Assumptions

Given the conceptual model and its calibration using census data and TUS data as described above, the resulting model allows to study spatial patterns of energy usage for space heating in the hypothetical case in which the heating behaviour is identical in all dwellings and is based on occupancy only. Using identically parameterised thermal models for dwellings allows to study the impact of occupancy in isolation ignoring the variance stemming from the physical structure. Due to the population synthesis, model results are only valid for the smallest spatial region for which aggregated census data is available.

# Case Study

short intro to London Haringey

describe data sets: UK Time Use Survey 2000, Census 2011

## Parameterisation

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

Future work:

* use survival models for occupancy, as done by [@Aerts:2015ko; @Baetens:2015gm]
* use clustering approach as used by [@Aerts:2015ko]
* use set point preference as introduced by [@Baetens:2015gm; @Leidelmeijer:2005vu]
* use fraction of room heated as in [@Baetens:2015gm; @Leidelmeijer:2005vu]
* use newly released uk TUS data set


# References <!--- filled automatically by pandoc --->
