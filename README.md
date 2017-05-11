# Working Paper KTP EECi & Improbable

This is the work in progress paper of the Knowledge Transfer Partnership between the Energy
Efficient Cities initiative (EECi) of University of Cambridge and Improbable.

## Getting ready

### Installation

To set up a environment in which the analysis can be run and the paper be build, the simplest is to use [conda](https://conda.io/docs/index.html). An environment with all dependencies can be created from the provided yaml file:

    conda env create -f conda-environment.yml

In addition you will need [Java 1.8](http://www.oracle.com/technetwork/java/javase/downloads/jre8-downloads-2133155.html) to run simulations.

You will also need `make` to automatically replicate all results. Without `make`, e.g. on Windows, you will need to manually run all steps.

### Data preparation

All open data is retrieved automatically from the web when running the analysis the first time. All closed or safeguarded data must be provided by the user. These datasets are:

* UK Time Use Survey 2001: safeguarded dataset to be placed in `./data/UKDA-4504-tab/`.
* MIDAS: safeguarded dataset to be called `./data/Londhour.csv`.

Note: the open census data is retrieved from [nomis](https://www.nomisweb.co.uk.). There is a download limit for anonymous downloads, which [is said to be limited to 25.000](https://www.nomisweb.co.uk/api/v01/help). You should not hit this limit when running this analysis.

## Run the analysis

    make paper

This will run all analysis steps to reproduce results and eventually build the paper. Depending on the machine this might take a few hours.

You can also run certain parts only by using other `make` rules; to get a list of all rules see the `Makefile`.

If you do not have `make` you can manually run the steps through the Python command line interfaces. Refer to the `Makefile` to see which commands are called to produce results.

## Run the tests

    make test

## Repo structure

* `doc`: contains all files necessary to build the paper; plots and result files are not in here but generated automatically
* `urbanoccupants`: a small Python library and their tests, containing reusable code needed several times in this study
* `scripts`: Python scripts and its tests which run this analysis
* `notebooks`: Jupyter notebooks that are not used in the main build chain of the paper

## Datasets

// TODO add licenses and copyright

* UK Census 2011: Retrieved from [nomis](https://www.nomisweb.co.uk.).
* London Shape Files: Retrieved from [London Datastore](https://data.london.gov.uk).
* UK Time Use Survey 2001: Safeguarded data set.
* MIDAS: Safeguarded data set.
