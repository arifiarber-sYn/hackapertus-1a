# Hack Apertus — Track 1A. Minimal image for `make run` (README requirement 3: Docker).
# The reproduction is stdlib-only: no `pip install`, no model weights, no network in replay mode.
# Live (optional): `docker run -e LLM_BASE_URL -e LLM_API_KEY -e LLM_NAME ...` — see Makefile `run-live`.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY LICENSE README.md Makefile ./
COPY track_1a/ track_1a/
RUN mkdir -p /app/track_1a/out
CMD ["python3", "track_1a/src/reproduce.py"]
