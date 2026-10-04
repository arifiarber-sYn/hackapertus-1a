# Hack Apertus — Track 1A.
# Gjyqtaret xhirojne `make run` nga RRENJA e repo-s, ne checkout te paster (README, kerkesa 3–4):
#   run        → ndërton imazhin Docker dhe xhiron riprodhimin brenda kontejnerit;
#                nese Docker mungon ose daemon-i s'pergjigjet, bie automatikisht te `run-local`.
#   run-local  → i njejti riprodhim direkt me python3 (vetem stdlib, pa rrjet, pa celesa).
#   run-live   → riprodhim LIVE kunder endpoint-it (LLM_BASE_URL/LLM_API_KEY/LLM_NAME nga mjedisi
#                ose .env), <=50 thirrje, roja e fingerprint-it; pa celes bie ne replay.
#   test       → testet (unittest, stdlib) te paketes: krahaso(), te dhenat, skema, make run-local.
IMAGE ?= hackapertus-1a:local
RUN_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
PY ?= python3
LIVE_ENV := -e LLM_BASE_URL -e LLM_API_KEY -e LLM_NAME

.PHONY: run run-local run-live build test

run:
	@if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then \
		echo ">> Docker i disponueshem: ndertoj $(IMAGE) dhe xhiroj riprodhimin ne kontejner"; \
		docker build -q -t $(IMAGE) $(RUN_DIR) >/dev/null && docker run --rm $(LIVE_ENV) $(IMAGE); \
	else \
		echo ">> Docker i padisponueshem ne kete makine: xhiroj riprodhimin lokalisht (python3, stdlib)"; \
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
