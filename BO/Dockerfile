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

# Copy application
COPY . .

EXPOSE 3001

ENV PYTHONPATH=/app
ENV FLASK_ENV=production

# Healthcheck (Backoffice lightweight)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
  CMD curl -f http://localhost:3001/health || exit 1

# Run with Waitress (more threads)
CMD ["waitress-serve", "--listen=0.0.0.0:3001", "--threads=6", "app:create_app()"]
