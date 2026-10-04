# Hack Apertus — Track 1A. Imazh minimal per `make run` (kerkesa 3 e README: Docker).
# Riprodhimi eshte stdlib-only: asnje `pip install`, asnje peshe modeli, asnje rrjet ne replay.
# Live (opsionale): `docker run -e LLM_BASE_URL -e LLM_API_KEY -e LLM_NAME ...` — shih Makefile `run-live`.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY LICENSE README.md Makefile ./
COPY track_1a/ track_1a/
RUN mkdir -p /app/track_1a/out
CMD ["python3", "track_1a/src/reproduce.py"]
