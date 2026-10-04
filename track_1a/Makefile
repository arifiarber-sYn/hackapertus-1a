.PHONY: run

# 'make run' — riprodhimi i gjetjeve te Track 1A.
# Funksionon edhe vetiu (make -C track_1a run) edhe i deleguar nga Makefile i rrenjes.
TRACK_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

run:
	@python3 $(TRACK_DIR)src/reproduce.py
