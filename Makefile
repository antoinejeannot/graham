.PHONY: pdf fetch

fetch:
	python fetch.py

pdf:
    pandoc $(shell cat essays-list.txt) \
    -o graham_essays.pdf \
    --toc \
    --toc-depth=2 \
    --pdf-engine=xelatex \
    --include-in-header=toc-style.tex \
    --include-before-body=title.tex \
    -V documentclass=book \
    -V paper=letter \
    -V fontsize=11pt \
    -V geometry:top=1.2in,bottom=1.2in,left=1.5in,right=1in \
    -V linestretch=1.15 \
    -V urlcolor=blue \
    -V indent=true \
    -V classoption=openright \
    -V toc-title="Table of Contents" \
    -V book=true