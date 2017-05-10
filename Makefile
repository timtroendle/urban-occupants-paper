# Build MS Word paper.
build:
	mkdir ./build

.PHONY: paper clean tus-data test
paper: | build build/paper.docx

clean:
	rm -rf ./build/*

test: | build
	py.test

tus-data: build/seed.pickle build/markov-ts.pickle

build/seed.pickle: ./data/UKDA-4504-tab/tab/Individual_data_5.tab ./scripts/tus/seed.py | build
	python ./scripts/tus/seed.py ./data/UKDA-4504-tab/tab/Individual_data_5.tab ./build/seed.pickle

build/markov-ts.pickle: ./data/UKDA-4504-tab/tab/diary_data_8.tab ./scripts/tus/markovts.py | build
	python ./scripts/tus/markovts.py ./data/UKDA-4504-tab/tab/diary_data_8.tab ./build/markov-ts.pickle

build/feature-association.pickle build/ts-association.pickle: ./build/seed.pickle ./build/markov-ts.pickle ./scripts/tus/association.py
	python ./scripts/tus/association.py ./build/seed.pickle ./build/markov-ts.pickle ./build/feature-association.pickle ./build/ts-association.pickle

build/ts-association.png: ./build/ts-association.pickle ./scripts/plot/association.py
	python ./scripts/plot/association.py ./build/ts-association.pickle ./build/ts-association.png

build/population-cluster.png: ./build/seed.pickle ./build/markov-ts.pickle ./scripts/plot/popcluster.py
	python ./scripts/plot/popcluster.py ./build/seed.pickle ./build/markov-ts.pickle ./build/population-cluster.png

build/simulation-input.db: ./build/seed.pickle ./build/markov-ts.pickle ./simulation-config.yaml ./scripts/simulationinput.py
	python ./scripts/simulationinput.py ./build/seed.pickle ./build/markov-ts.pickle ./simulation-config.yaml build/simulation-input.db

build/energy-agents.jar: | build
	curl -Lo build/energy-agents.jar 'https://github.com/timtroendle/energy-agents/releases/download/v1.0.0-RC1/energy-agents-1.0.0-RC1-jar-with-dependencies.jar'

build/simulation-output.db: build/energy-agents.jar build/simulation-input.db scripts/runsim.py simulation-config.yaml
	python scripts/runsim.py build/energy-agents.jar build/simulation-input.db build/simulation-output.db simulation-config.yaml

build/thermal-power.png build/choropleth.png: build/simulation-output.db simulation-config.yaml scripts/plot/simulationresults.py
	python scripts/plot/simulationresults.py build/simulation-output.db simulation-config.yaml build/thermal-power.png build/choropleth.png

build/paper.docx: doc/literature.bib doc/online.bib doc/main.md doc/pandoc-metadata.yml
build/paper.docx: build/ts-association.png build/population-cluster.png build/thermal-power.png
build/paper.docx: build/choropleth.png
	cd ./doc && \
	pandoc --filter pandoc-fignos --filter pandoc-tablenos --filter pandoc-citeproc \
		--reference-docx ./paper-template.docx main.md pandoc-metadata.yml -t docx -o ../build/paper.docx
