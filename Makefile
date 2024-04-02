default:
	latexmk -pdf -lualatex thesis.tex

.PHONY: default clean

clean:
	latexmk -pdf -c -lualatex thesis.tex