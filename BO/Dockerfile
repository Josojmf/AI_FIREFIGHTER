FROM python:3.10-slim

WORKDIR /app

# System tools (mínimas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Disable Python buffering
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --no-deps -r requirements.txt

# Copy the full app
COPY . .

EXPOSE 3001

ENV PYTHONPATH=/app
ENV FLASK_ENV=production

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
  CMD curl -f http://localhost:3001/health || exit 1

CMD ["python", "serve_waitress.py"]