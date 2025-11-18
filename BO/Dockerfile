FROM python:3.10-slim

WORKDIR /app

# System tools
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Disable Python buffering (better logs)
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip

# Copy the full app
COPY . .

EXPOSE 3001

ENV PYTHONPATH=/app
ENV FLASK_ENV=production

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
  CMD curl -f http://localhost:3001/health || exit 1

# IMPORTANT: Run using our script, not waitress-serve
CMD ["python", "serve_waitress.py"]
