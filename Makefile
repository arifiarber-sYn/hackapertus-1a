# Hack Apertus — Track 1A.
# Judges run `make run` from the repo ROOT, on a clean checkout (README, requirements 3–4):
#   run        → builds the Docker image and runs the reproduction inside the container;
#                if Docker is missing or the daemon does not respond, falls back to `run-local`.
#   run-local  → the same reproduction directly with python3 (stdlib only, no network, no keys).
#   run-live   → LIVE reproduction against the endpoint (LLM_BASE_URL/LLM_API_KEY/LLM_NAME from env
#                or .env), <=50 calls, fingerprint guard; without a key falls back to replay.
#   test       → package tests (unittest, stdlib): krahaso(), data, schema, make run-local.
IMAGE ?= hackapertus-1a:local
RUN_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
PY ?= python3
LIVE_ENV := -e LLM_BASE_URL -e LLM_API_KEY -e LLM_NAME

#   collect    → reusable harness: collects a new battery against the endpoint (BATTERY=..., LIMIT=...);
#                collect-dry = validation + plan, 0 calls. See track_1a/docs/add-your-battery.md.
BATTERY ?= track_1a/data/example_battery.json
LIMIT ?= 50

.PHONY: run run-local run-live build test collect collect-dry

collect:
	@if [ -f $(RUN_DIR).env ]; then set -a; . $(RUN_DIR).env; set +a; fi; \
	$(PY) $(RUN_DIR)track_1a/src/harness/collect.py --battery $(BATTERY) --limit $(LIMIT)

collect-dry:
	@$(PY) $(RUN_DIR)track_1a/src/harness/collect.py --battery $(BATTERY) --limit $(LIMIT) --dry-run

run:
	@if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then \
		echo ">> Docker available: building $(IMAGE) and running the reproduction in the container"; \
		docker build -q -t $(IMAGE) $(RUN_DIR) >/dev/null && docker run --rm $(LIVE_ENV) $(IMAGE); \
	else \
		echo ">> Docker unavailable on this machine: running the reproduction locally (python3, stdlib)"; \
		$(MAKE) --no-print-directory -f $(RUN_DIR)Makefile run-local; \
	fi

run-local:
	@$(PY) $(RUN_DIR)track_1a/src/reproduce.py

run-live:
	@if [ -f $(RUN_DIR).env ]; then set -a; . $(RUN_DIR).env; set +a; fi; \
	$(PY) $(RUN_DIR)track_1a/src/reproduce.py --live

build:
	docker build -t $(IMAGE) $(RUN_DIR)

test:
	@cd $(RUN_DIR) && $(PY) -m unittest discover -s track_1a/tests -t . -v
