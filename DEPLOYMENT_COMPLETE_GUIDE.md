# 🚀 AI Firefighter - Deployment Complete Guide

Guía completa para desplegar la aplicación AI Firefighter con Docker, GitHub Actions, y configuración SSO portable.

---

## 📋 Tabla de Contenidos

1. [Arquitectura General](#arquitectura-general)
2. [Configuración de Archivos .env](#configuración-de-archivos-env)
3. [GitHub Secrets](#github-secrets)
4. [Flujo de Despliegue](#flujo-de-despliegue)
5. [Verificación Post-Deployment](#verificación-post-deployment)
6. [Troubleshooting](#troubleshooting)

---

## 🏗️ Arquitectura General

### Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │    FO    │  │   API    │  │    BO    │                  │
│  │Frontend  │  │ Backend  │  │Backoffice│                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ git push main
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   GitHub Actions                             │
│  ┌──────────────┐              ┌──────────────┐            │
│  │ CI Pipeline  │─────────────▶│ CD Pipeline  │            │
│  │  (tests)     │   success    │  (deploy)    │            │
│  └──────────────┘              └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ 1. Build Docker images
                         │ 2. Push to GHCR
                         │ 3. SSH to server
                         │ 4. Pull images
                         │ 5. docker-compose up
                         ▼
┌─────────────────────────────────────────────────────────────┐
│       Production Server (167.71.63.108)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ Frontend │  │ Backend  │  │Backoffice│                 │
│  │  :8000   │  │  :5000   │  │  :3001   │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│       │              │              │                       │
│       └──────────────┴──────────────┘                       │
│                      │                                       │
│              ┌───────┴────────┐                            │
│              │ MongoDB Atlas  │                            │
│              └────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

### Puertos

| Servicio | Puerto Local | Puerto Producción | Docker Network |
|----------|--------------|-------------------|----------------|
| Frontend | 8000 | 8000 | firefighter_frontend |
| Backend API | 5000 | 5000 | firefighter_backend |
| BackOffice | 8080 | 3001 | firefighter_backoffice |

---

## 📝 Configuración de Archivos .env

### Estructura de Archivos

```
AI_Firefighter/
├── .env                      # ✅ Principal (desarrollo local)
├── .env.example              # 📄 Template para otros devs
├── .env.production           # ⚠️ Template (NO se usa en Docker)
│
├── API/
│   ├── .env                  # ✅ Para desarrollo local del API
│   └── .env.production       # ⚠️ Template (NO se usa en Docker)
│
├── FO/
│   ├── .env                  # ✅ Para desarrollo local del Frontend
│   └── .env.production       # ⚠️ Template (NO se usa en Docker)
│
└── BO/
    ├── .env                  # ✅ Para desarrollo local del BackOffice
    └── .env.production       # ⚠️ Template (NO se usa en Docker)
```

### Variables de Entorno por Servicio

#### `.env` (raíz - desarrollo local)

```bash
# MongoDB
MONGO_USER=joso
MONGO_PASS=XyGItdDKpWkfJfjT
MONGO_CLUSTER=cluster0.yzzh9ig.mongodb.net
DB_NAME=FIREFIGHTER

# Security
SECRET_KEY=5c9d8cc9ae28bc70e476842054c39d43
FRONTEND_SECRET_KEY=firefighter-frontend-2024-secret-key-very-secure
BACKOFFICE_SECRET_KEY=firefighter-backoffice-2024-super-secret-admin-key

# SSO & CORS
PRODUCTION_URL=http://167.71.63.108
NGROK_URL=https://geekily-unmaterial-nancy.ngrok-free.dev

# Environment
ENVIRONMENT=development
DOCKER_ENV=false
DEBUG=true
```

#### `/root/firefighter.env` (servidor producción - generado por GitHub Actions)

Este archivo se genera automáticamente en el servidor por GitHub Actions (ver `.github/workflows/cd.yml` líneas 269-350).

**Contiene**:
- Todos los secrets de GitHub
- IP del servidor detectada automáticamente
- URLs configuradas dinámicamente
- Variables de ambiente de producción

---

## 🔐 GitHub Secrets

### Lista Completa (20 secrets)

Ver guía completa en: [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md)

**Resumen rápido**:

```bash
# MongoDB
MONGO_USER, MONGO_PASS, MONGO_CLUSTER, DB_NAME

# Security
SECRET_KEY, FRONTEND_SECRET_KEY, BACKOFFICE_SECRET_KEY, JWT_EXPIRES_HOURS

# Admin
ADMIN_USERNAME, ADMIN_PASSWORD

# Push Notifications
VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY

# Email
SENDGRID_API_KEY, SENDGRID_SENDER_EMAIL, SENDGRID_SENDER_NAME

# Server
PRODUCTION_HOST, PRODUCTION_USER, PRODUCTION_SSH_KEY

# Docker Registry
GHCR_USER, GHCR_PAT
```

### Cómo Configurarlos

```bash
# 1. Ve a tu repo en GitHub
Settings → Secrets and variables → Actions → New repository secret

# 2. Añade cada secret de la lista
# 3. Verifica que hay 20 secrets en total
```

---

## 🔄 Flujo de Despliegue

### Diagrama de Flujo

```
Developer pushes to main
         │
         ▼
┌────────────────────┐
│  CI Pipeline       │
│  ✓ Syntax check    │
│  ✓ Security scan   │
│  ✓ Tests           │
└────────────────────┘
         │ ✅ Success
         ▼
┌────────────────────┐
│  CD Pipeline       │
│  Step 1: Build     │
└────────────────────┘
         │
         ▼
┌────────────────────┐
│  Build Docker      │
│  Images:           │
│  - Frontend        │
│  - Backend         │
│  - BackOffice      │
└────────────────────┘
         │
         ▼
┌────────────────────┐
│  Push to GHCR      │
│  ghcr.io/josojmf/  │
│  ai-firefighter-*  │
└────────────────────┘
         │
         ▼
┌────────────────────┐
│  SSH to Server     │
│  167.71.63.108     │
└────────────────────┘
         │
         ▼
┌────────────────────┐
│  Server Prep       │
│  1. Stop services  │
│  2. Clean space    │
│  3. Backup         │
└────────────────────┘
         │
         ▼
┌────────────────────┐
│  Generate ENV      │
│  /root/            │
│  firefighter.env   │
└────────────────────┘
         │
         ▼
┌────────────────────┐
│  Pull Images       │
│  with retry logic  │
└────────────────────┘
         │
         ▼
┌────────────────────┐
│  docker-compose    │
│  up -d             │
└────────────────────┘
         │
         ▼
┌────────────────────┐
│  Health Checks     │
│  - Backend: 5000   │
│  - Frontend: 8000  │
│  - Backoffice:3001 │
└────────────────────┘
         │
         ▼
     ✅ DONE!
```

### Comandos Manuales

Si necesitas desplegar manualmente:

```bash
# 1. SSH al servidor
ssh root@167.71.63.108

# 2. Ve al directorio
cd /opt/emergency

# 3. Pull latest images
docker-compose -f docker-compose.prod.yml pull

# 4. Restart services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# 5. Ver logs
docker-compose -f docker-compose.prod.yml logs -f

# 6. Ver estado
docker-compose -f docker-compose.prod.yml ps
```

---

## ✅ Verificación Post-Deployment

### Checklist Completo

#### 1. Servicios en Ejecución

```bash
# SSH al servidor
ssh root@167.71.63.108

# Verificar contenedores
docker ps

# Deberías ver 3 contenedores corriendo:
# - firefighter_frontend (port 8000)
# - firefighter_backend (port 5000)
# - firefighter_backoffice (port 3001)
```

#### 2. Endpoints Accesibles

**Frontend**:
```bash
curl http://167.71.63.108:8000/
# Debería retornar HTML
```

**Backend API**:
```bash
curl http://167.71.63.108:5000/api/health
# Debería retornar: {"status": "ok", ...}
```

**BackOffice**:
```bash
curl http://167.71.63.108:3001/
# Debería retornar HTML
```

#### 3. Navegador

Abre en tu navegador:

- http://167.71.63.108:8000 → Frontend (login de usuarios)
- http://167.71.63.108:5000 → API (debería mostrar algo)
- http://167.71.63.108:3001 → BackOffice (login de admin)

#### 4. SSO Funcional

1. Ve a http://167.71.63.108:8000/login
2. Abre consola del navegador (F12)
3. Deberías ver:
   ```
   🔐 Inicializando SSO...
   📡 API URL: http://167.71.63.108:5000
   ```
4. Click en "Continuar con Google"
5. Debería abrir el popup de Google OAuth

#### 5. Variables de Entorno en Contenedores

```bash
# Verificar variables en backend
docker exec firefighter_backend env | grep MONGO_USER
# Debería mostrar: MONGO_USER=joso

# Verificar CORS configurado
docker exec firefighter_backend env | grep PRODUCTION_URL
# Debería mostrar: PRODUCTION_URL=http://167.71.63.108

# Verificar email configurado
docker exec firefighter_backend env | grep SENDGRID
# Debería mostrar tus keys de SendGrid
```

#### 6. Logs Sin Errores

```bash
# Ver logs de cada servicio
docker logs firefighter_frontend --tail 50
docker logs firefighter_backend --tail 50
docker logs firefighter_backoffice --tail 50

# Buscar errores
docker logs firefighter_backend 2>&1 | grep -i error
# No debería mostrar errores críticos
```

---

## 🐛 Troubleshooting

### Problema: Contenedores no inician

**Síntomas**:
```bash
docker ps
# No muestra los 3 contenedores
```

**Solución**:
```bash
# Ver por qué fallaron
docker-compose -f /opt/emergency/docker-compose.prod.yml logs

# Reiniciar
docker-compose -f /opt/emergency/docker-compose.prod.yml down
docker-compose -f /opt/emergency/docker-compose.prod.yml up -d
```

### Problema: Error CORS en navegador

**Síntomas**:
```
Access to fetch at 'http://167.71.63.108:5000/api/...' from origin 'http://167.71.63.108:8000' has been blocked by CORS
```

**Solución**:
```bash
# 1. Verificar que PRODUCTION_URL está configurado
docker exec firefighter_backend env | grep PRODUCTION_URL

# 2. Si no está, verificar GitHub Secrets
# Settings → Secrets → PRODUCTION_HOST debe ser 167.71.63.108

# 3. Re-deploy
git commit --allow-empty -m "Trigger re-deployment"
git push origin main
```

### Problema: SSO no funciona

**Síntomas**:
- Botón SSO no hace nada
- Error "Google SDK no cargado"

**Solución**:

1. **Verificar consola del navegador**:
   ```javascript
   console.log(API_BASE_URL);
   // Debería mostrar: http://167.71.63.108:5000
   ```

2. **Verificar Google OAuth configurado**:
   - Ve a [Google Cloud Console](https://console.cloud.google.com/)
   - APIs & Services → Credentials
   - Verifica que http://167.71.63.108:8000 está en "Authorized JavaScript origins"

3. **Verificar Client ID en código**:
   ```bash
   # En tu máquina local
   grep "clientId" FO/static/js/sso-handler.js
   # Debería mostrar tu Client ID real
   ```

### Problema: Email no se envía

**Síntomas**:
- No llegan emails de recuperación de contraseña
- Error en logs: "SendGrid authentication failed"

**Solución**:

1. **Verificar SendGrid API Key**:
   ```bash
   docker exec firefighter_backend env | grep SENDGRID_API_KEY
   # Debería mostrar: SENDGRID_API_KEY=SG.xxxxx
   ```

2. **Si no aparece**:
   - Ve a GitHub → Settings → Secrets
   - Verifica que `SENDGRID_API_KEY` existe
   - Re-deploy

3. **Verificar sender verificado**:
   - Ve a SendGrid → Settings → Sender Authentication
   - Email debe estar verificado

### Problema: Espacio en disco lleno

**Síntomas**:
```bash
df -h
# / está al 100%
```

**Solución**:
```bash
# Limpieza agresiva
docker system prune -a -f --volumes

# Limpiar logs del sistema
journalctl --vacuum-size=50M

# Limpiar cache de apt
apt clean
apt autoremove -y

# Verificar espacio recuperado
df -h
```

### Problema: GitHub Actions falla en deployment

**Síntomas**:
- Workflow CD falla
- Error: "SSH connection refused"

**Solución**:

1. **Verificar SSH key**:
   ```bash
   # En tu máquina local
   ssh -i ~/.ssh/tu_clave root@167.71.63.108
   # Debería conectar sin pedir contraseña
   ```

2. **Si no conecta**:
   ```bash
   # Copiar clave pública al servidor
   ssh-copy-id -i ~/.ssh/tu_clave.pub root@167.71.63.108
   ```

3. **Actualizar secret en GitHub**:
   ```bash
   # Copiar clave PRIVADA
   cat ~/.ssh/tu_clave

   # Pegar TODO (incluye BEGIN y END) en GitHub Secret:
   # Settings → Secrets → PRODUCTION_SSH_KEY
   ```

---

## 📚 Referencias

- [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md) - Configuración de secrets
- [PORTABLE_CONFIGURATION.md](PORTABLE_CONFIGURATION.md) - Sistema portable
- [QUICK_SSO_SETUP.md](QUICK_SSO_SETUP.md) - Configuración SSO rápida
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.MD) - Despliegue detallado

---

## 🎯 Quick Start

**Para empezar desde cero**:

```bash
# 1. Configura GitHub Secrets (20 secrets)
# Ver: GITHUB_SECRETS_SETUP.md

# 2. Commit y push
git add .
git commit -m "Configure production deployment"
git push origin main

# 3. Ve a GitHub Actions
# Espera ~10-15 minutos

# 4. Verifica deployment
open http://167.71.63.108:8000

# 5. Celebra! 🎉
```

---

**Última actualización**: 1 de Diciembre 2025
**Versión**: 1.0 - Deployment Automatizado con SSO
