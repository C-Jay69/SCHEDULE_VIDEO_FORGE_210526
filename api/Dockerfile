FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# api/requirements.txt is referenced relative to the build context root.
# The cache mount persists pip's wheel cache across builds so re-running the
# build after a failure doesn't re-download the whole dependency tree.
COPY api/requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --retries 10 --timeout 300 -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY api/ .
COPY seed.py /seed.py

EXPOSE 8000

# Production by default. Set DEV=1 to enable --reload for local development.
# WORKERS controls the uvicorn worker count in production mode.
CMD ["sh", "-c", "if [ \"$DEV\" = \"1\" ]; then exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload; else exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-2}; fi"]