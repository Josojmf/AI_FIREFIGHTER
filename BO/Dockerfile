FROM python:3.10-slim

WORKDIR /app

# System libs
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Expose Backoffice port
EXPOSE 3001

ENV PYTHONPATH=/app
ENV FLASK_ENV=production

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
  CMD curl -f http://localhost:3001/health || exit 1

# Run with Waitress
CMD ["python", "serve_waitress.py"]