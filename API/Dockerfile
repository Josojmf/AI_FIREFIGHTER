FROM python:3.10-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# JWT FIX: Uninstall wrong packages and install PyJWT FIRST
COPY requirements.txt .
RUN pip uninstall -y jwt pyjwt || true && \
    pip install --no-cache-dir PyJWT==2.8.0 && \
    pip install --no-cache-dir -r requirements.txt && \
    python -c "import jwt; print('✅ JWT Fix:', jwt.__version__)"

# Copy application
COPY . .

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

CMD ["python", "main.py"]