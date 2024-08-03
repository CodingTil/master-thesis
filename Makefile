default:
	latexmk -pdf -lualatex -halt-on-error -shell-escape thesis.tex

.PHONY: default clean

clean:
	latexmk -pdf -c -lualatex thesis.tex