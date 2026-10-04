.PHONY: run run-local test

# 'make run' — riprodhimi i gjetjeve te Track 1A.
# Funksionon edhe vetiu (make -C track_1a run) edhe i deleguar nga Makefile i rrenjes
# (Makefile i rrenjes shton Docker-in; ketu vetem python3 stdlib).
TRACK_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

run run-local:
	@python3 $(TRACK_DIR)src/reproduce.py

test:
	@cd $(TRACK_DIR).. && python3 -m unittest discover -s track_1a/tests -t . -v
