FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV PYTHONPATH=/app
ENV FLASK_ENV=production

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
  CMD curl -f http://localhost:5000/api/health || exit 1

CMD ["gunicorn", "-b", "0.0.0.0:5000", "api:app"]
