.PHONY: run

# Hack Apertus — Track 1A.
# Gjyqtaret xhirojne 'make run' nga RRENJA e repo-s, ne checkout te paster.
# Riprodhimi eshte stdlib-only: pa Docker, pa rrjet, pa celesa API — lexon
# pergjigjet e regjistruara te modelit nga te dhenat e paketuara ne repo.
RUN_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

run:
	@python3 $(RUN_DIR)track_1a/src/reproduce.py
