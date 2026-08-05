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
    curl \
    && rm -rf /var/lib/apt/lists/*

# All paths are relative to the ROOT context
COPY worker/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --retries 10 --timeout 300 -r requirements.txt

# Piper TTS model (voice). The piper binary ships with piper-tts.
RUN mkdir -p /app/models && \
    curl -fSL -o /app/models/en_US-lessac-medium.onnx \
      https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx && \
    curl -fSL -o /app/models/en_US-lessac-medium.onnx.json \
      https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Copy worker code (celery_app.py, db.py, tasks/, pipeline/) into /app
COPY worker/ .

# Copy api/app/* into /app/app so worker code can do `from app.models import X`
COPY api/app /app/app

# Make /app importable as the package root
ENV PYTHONPATH=/app

# Download Whisper model on build (optional - can be done at runtime)
ENV WHISPER_MODEL_SIZE=base

CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info", "--concurrency=2", "-Q", "default,priority"]