#!/usr/bin/env bash
# scripts/backup.sh
set -e

BACKUP_DIR="/opt/emergency/backups"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "${BACKUP_DIR}"

echo "📦 Creando backup en ${BACKUP_DIR}/${TIMESTAMP}..."

# Backup de docker-compose y envs (ajusta nombres si cambian)
cp /opt/emergency/docker-compose.prod.yml "${BACKUP_DIR}/docker-compose.prod.yml.${TIMESTAMP}" 2>/dev/null || true
cp /opt/emergency/docker-compose.swarm.yml "${BACKUP_DIR}/docker-compose.swarm.yml.${TIMESTAMP}" 2>/dev/null || true
cp /opt/emergency/docker-compose.monitoring.yml "${BACKUP_DIR}/docker-compose.monitoring.yml.${TIMESTAMP}" 2>/dev/null || true

# Si tienes algún volumen crítico (ejemplo: db_data), aquí iría el dump
# docker run --rm -v db_data:/var/lib/postgresql/data -v "${BACKUP_DIR}":/backup alpine tar czf /backup/db_data.${TIMESTAMP}.tar.gz /var/lib/postgresql/data

echo "✅ Backup básico completado"
