# Build MS Word paper.
build:
	mkdir ./build

.PHONY: paper clean tus_data test
paper: | build build/paper.docx

clean:
	rm -rf ./build/*

test: | build
	py.test

tus_data: build/seed.pickle build/markov_ts.pickle

build/seed.pickle: | build ./data/UKDA-4504-tab/tab/Individual_data_5.tab ./urbanoccupants/tus/individuals.py
	python urbanoccupants/urban.py read_seed ./data/UKDA-4504-tab/tab/Individual_data_5.tab ./build/seed.pickle

build/markov_ts.pickle: | build ./data/UKDA-4504-tab/tab/diary_data_8.tab ./urbanoccupants/tus/markovts.py
	python urbanoccupants/urban.py read_markov_ts ./data/UKDA-4504-tab/tab/diary_data_8.tab ./build/markov_ts.pickle

build/feature_association.pickle: ./build/seed.pickle ./urbanoccupants/tus/association.py
	python urbanoccupants/urban.py association_of_features ./build/seed.pickle ./build/feature_association.pickle

build/time_series_1d_association.pickle: ./build/seed.pickle ./build/markov_ts.pickle ./urbanoccupants/tus/association.py
	python urbanoccupants/urban.py association_of_time_series_1d ./build/seed.pickle ./build/markov_ts.pickle ./build/time_series_1d_association.pickle

build/paper.docx: | build doc/literature.bib doc/main.md doc/pandoc-metadata.yml
	cd ./doc && \
	pandoc --filter pandoc-fignos --filter pandoc-tablenos --filter pandoc-citeproc --reference-docx ./paper-template.docx main.md pandoc-metadata.yml -t docx -o ../build/paper.docx
