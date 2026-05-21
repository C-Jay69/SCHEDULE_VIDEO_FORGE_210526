FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpq-dev \
    gcc \
    espeak-ng \
    libgomp1 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# All paths are relative to the ROOT context
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY worker/ .

# Copy api models (needed by worker)
COPY api /api

# Download Whisper model on build (optional - can be done at runtime)
ENV WHISPER_MODEL_SIZE=base

CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info", "--concurrency=2", "-Q", "default,priority"]
