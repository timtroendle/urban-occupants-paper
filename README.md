# Working Paper KTP EECi & Improbable

This is the work in progress paper of the Knowledge Transfer Partnership between the Energy
Efficient Cities initiative (EECi) of University of Cambridge and Improbable.

## Installation

To set up a environment in which the analysis can be run and the paper be build, the simplest is to use [conda](https://conda.io/docs/index.html). An environment with all dependencies can be created from the provided yaml file:

    conda env create -f conda-environment.yml

In addition you will need [Java 1.8](http://www.oracle.com/technetwork/java/javase/downloads/jre8-downloads-2133155.html) to run simulations.

## Build the paper

    make paper

## Run the analysis

### Data preparation

All open data is retrieved automatically from the web when running the analysis the first time. All closed or safeguarded data must be provided by the user. These datasets are:

* UK Time Use Survey 2001: safeguarded dataset to be placed in `./notebooks/data/UKDA-4504-tab/`.
* MIDAS: safeguarded dataset to be called `./notebooks/data/Londhour.csv`.

Note: the open census data is retrieved from [nomis](https://www.nomisweb.co.uk.). There is a download limit for anonymous downloads, which [is said to be limited to 25.000](https://www.nomisweb.co.uk/api/v01/help). You should not hit this limit when running this analysis.

## Datasets

// TODO add licenses and copyright

* UK Census 2011: Retrieved from [nomis](https://www.nomisweb.co.uk.).
* London Shape Files: Retrieved from [London Datastore](https://data.london.gov.uk).
* UK Time Use Survey 2001: Safeguarded data set.
* MIDAS: Safeguarded data set.
