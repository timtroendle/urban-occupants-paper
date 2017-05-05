# Build MS Word paper.
./build:
	mkdir ./build

.PHONY: paper
paper: ./build build/paper.docx

.PHONY: clean
clean:
	rm -rf ./build/*

build/paper.docx: ./build doc/literature.bib doc/main.md doc/pandoc-metadata.yml
	cd ./doc && \
	pandoc --filter pandoc-tablenos --filter pandoc-citeproc --reference-docx ./paper-template.docx main.md pandoc-metadata.yml -t docx -o ../build/paper.docx
