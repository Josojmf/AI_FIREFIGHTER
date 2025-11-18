FROM python:3.10-slim

WORKDIR /app

# System libs
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code
COPY . .

# Expose Backoffice port
EXPOSE 3001

ENV PYTHONPATH=/app
ENV FLASK_ENV=production

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
  CMD curl -f http://localhost:3001/health || exit 1

# Run with Waitress (PRODUCCIÓN)
CMD ["python", "serve_waitress.py"]
