FROM python:3.10-slim

WORKDIR /app

# System libs
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps - copiar PRIMERO requirements para mejor cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code - COPIA EXPLÍCITA Y VERIFICADA
COPY app/ ./app/
COPY templates/ ./templates/ 2>/dev/null || echo "⚠️ No templates directory"
COPY static/ ./static/ 2>/dev/null || echo "⚠️ No static directory" 
COPY *.py ./
COPY *.txt ./
COPY *.html ./ 2>/dev/null || echo "⚠️ No HTML files"

# Verificar estructura de archivos copiada
RUN echo "📁 Estructura final en /app:" && \
    find . -name "*.py" -type f | head -20 && \
    echo "📋 Archivos en models:" && \
    find ./app/models -name "*.py" 2>/dev/null | head -10 && \
    echo "✅ Verificación completada"

# Expose Backoffice port
EXPOSE 3001

ENV PYTHONPATH=/app
ENV FLASK_ENV=production

# Healthcheck mejorado
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
  CMD curl -f http://localhost:3001/health || exit 1

# Run with Waitress (PRODUCCIÓN)
CMD ["python", "serve_waitress.py"]