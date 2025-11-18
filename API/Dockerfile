FROM python:3.10-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 5000

ENV PYTHONPATH=/app
ENV FLASK_ENV=production

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run with gunicorn (production-ready)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "api:app"]
