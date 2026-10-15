.PHONY: run run-local test

# 'make run' — reproduction of the Track 1A findings.
# Works both on its own (make -C track_1a run) and delegated from the root Makefile
# (the root Makefile adds Docker; here python3 stdlib only).
TRACK_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

run run-local:
	@python3 $(TRACK_DIR)src/reproduce.py

test:
	@cd $(TRACK_DIR).. && python3 -m unittest discover -s track_1a/tests -t . -v
