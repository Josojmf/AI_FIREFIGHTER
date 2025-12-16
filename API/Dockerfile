FROM python:3.10-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# ✅ CORRECTO: api:app (no app:app) + timeout 300s
CMD ["gunicorn", "-b", "0.0.0.0:5000", \
     "--workers", "2", \
     "--timeout", "300", \
     "--graceful-timeout", "300", \
     "--keep-alive", "5", \
     "--log-level", "info", \
     "api:app"]
