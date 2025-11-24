FROM python:3.10-slim

WORKDIR /app

# System libs
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Build arguments for React/Vue app
ARG API_BASE_URL=http://firefighter_backend:5000
ENV API_BASE_URL=$API_BASE_URL

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy full application
COPY . .

EXPOSE 8000

ENV PYTHONPATH=/app
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Healthcheck (extended)
HEALTHCHECK --interval=30s --timeout=15s --retries=10 \
  CMD curl -f http://localhost:8000/health || exit 1

# FIX: Gunicorn extended timeout (MUST BE SINGLE LINE)
CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8000", "--timeout", "180", "--graceful-timeout", "180", "--worker-class", "sync", "--workers", "1"]