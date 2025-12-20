FROM python:3.10-slim

WORKDIR /app

# ------------------------------------------------------------------------------
# System dependencies
# ------------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ------------------------------------------------------------------------------
# PIP configuración robusta (timeouts, reintentos, mirror opcional)
# ------------------------------------------------------------------------------

# Puedes sobreescribir estos valores al hacer docker build con --build-arg
ARG PIP_TIMEOUT=300
ARG PIP_RETRIES=5
ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PIP_DEFAULT_TIMEOUT=${PIP_TIMEOUT}
ENV PIP_RETRIES=${PIP_RETRIES}
ENV PIP_INDEX_URL=${PIP_INDEX_URL}

# Opcional: si tienes problemas de red, puedes forzar un mirror alternativo:
# ARG PIP_INDEX_URL=https://pypi.python.org/simple

# ------------------------------------------------------------------------------
# Dependencias Python: JWT fix + instalación robusta
# ------------------------------------------------------------------------------
COPY requirements.txt .

# 1) Limpiar jwt/pyjwt conflictivos
# 2) Instalar PyJWT explícitamente
# 3) Instalar paquetes "problemáticos" por separado (gevent) con más resiliencia
# 4) Instalar el resto de requirements
RUN set -eux; \
    pip uninstall -y jwt pyjwt || true; \
    pip install --no-cache-dir "PyJWT==2.8.0"; \
    # instalar gevent explícitamente antes, con reintentos y timeout alto
    pip install --no-cache-dir "gevent==23.9.1" || \
        (echo '⚠️  gevent falló, reintentando...' && \
         pip install --no-cache-dir "gevent==23.9.1"); \
    # instalar el resto de dependencias
    pip install --no-cache-dir -r requirements.txt; \
    python -c "import jwt; print('✅ JWT Fix:', jwt.__version__)"

# ------------------------------------------------------------------------------
# Copy application
# ------------------------------------------------------------------------------
COPY . .

EXPOSE 5000

# ------------------------------------------------------------------------------
# Healthcheck
# ------------------------------------------------------------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:5000/health || curl -fsS http://localhost:5000/ || exit 1

# ------------------------------------------------------------------------------
# Run
# ------------------------------------------------------------------------------
CMD ["python", "main.py"]
