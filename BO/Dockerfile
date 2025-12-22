# Fase 1: Builder
FROM python:3.10-slim AS builder

WORKDIR /app

# Variables de entorno para builder
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar requirements primero para cache de Docker
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --user --no-cache-dir -r requirements.txt


# Fase 2: Runtime
FROM python:3.10-slim AS runtime

WORKDIR /app

# Variables de entorno para runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.local/bin:$PATH" \
    PYTHONPATH="/app" \
    FLASK_APP="app" \
    FLASK_ENV="production" \
    ENVIRONMENT="production" \
    DOCKER="true" \
    PORT="3001" \
    HOST="0.0.0.0"

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear usuario no-root
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Copiar dependencias instaladas desde builder
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /app/requirements.txt .

# Copiar aplicación
COPY --chown=appuser:appuser . .

# Cambiar a usuario no-root
USER appuser

# Crear directorios necesarios
RUN mkdir -p /tmp/flask_sessions_backoffice && \
    chmod 700 /tmp/flask_sessions_backoffice && \
    mkdir -p /tmp/uploads && \
    chmod 700 /tmp/uploads

# Verificar instalación
RUN python -c "import flask; print(f'Flask version: {flask.__version__}')" && \
    python -c "import waitress; print(f'Waitress disponible')" && \
    python -c "from cryptography import __version__ as cver; print(f'Cryptography version: {cver}')"

# Exponer puerto
EXPOSE 3001

# Healthcheck optimizado
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
  CMD curl -f http://localhost:3001/health || exit 1

# Comando de entrada
CMD ["python", "serve_waitress.py"]

# Labels para Docker
LABEL maintainer="Firefighter AI Team" \
      version="2.0.0" \
      description="Firefighter AI BackOffice - Administración del sistema" \
      org.label-schema.name="firefighter-backoffice" \
      org.label-schema.vendor="Firefighter AI" \
      org.label-schema.schema-version="1.0"