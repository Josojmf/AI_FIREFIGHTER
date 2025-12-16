# Guía de Implementación de Kubernetes - FirefighterAI

## Paso 1: Preparar tu entorno local (Windows)

### 1.1 Habilitar Kubernetes en Docker Desktop
1. Abre Docker Desktop
2. Ve a Settings (⚙️)
3. Selecciona "Kubernetes"
4. Marca "Enable Kubernetes"
5. Aplica y reinicia Docker Desktop

### 1.2 Instalar herramientas (PowerShell como Admin)
```powershell
# Instalar kubectl
winget install -e --id Kubernetes.kubectl

# Verificar instalación
kubectl version --client
kubectl cluster-info
```

## Paso 2: Configurar secretos (IMPORTANTE)

### 2.1 Crear archivo de secretos con tus valores reales
```powershell
# En el directorio k8s/local/
Copy-Item secrets-template.yaml secrets.yaml
# Editar secrets.yaml con tus valores MongoDB, SendGrid, etc.
```

### 2.2 Valores críticos en secrets.yaml:

**USAR TUS VALORES EXACTOS DE .env:**
```yaml
stringData:
  # MongoDB Atlas (de tu API/.env)
  MONGO_USER: "joso"
  MONGO_PASS: "XyGItdDKpWkfJfjT" 
  MONGO_CLUSTER: "cluster0.yzzh9ig.mongodb.net"
  
  # JWT (de tu API/.env)
  SECRET_KEY: "5c9d8cc9ae28bc70e476842054c39d43"
  
  # Session Keys separadas (de tu BO/.env)
  FRONTEND_SECRET_KEY: "firefighter-frontend-ultra-secret-key-2024-v1-joso"
  BACKOFFICE_SECRET_KEY: "firefighter-backoffice-ultra-secret-key-2024-v1-joso"
  
  # Admin (de tu BO/.env)
  ADMIN_USERNAME: "admin3"
  ADMIN_PASSWORD: "admin123"
  
  # VAPID Keys (de tu API/.env)
  VAPID_PUBLIC_KEY: "BBvemqYjH5Al2LXlB1xN_Q_TRo-YL70eFoFDheEv-dN8S3xTPgp2XXWD67FtnC3LWagbuY4Isfslq-BdYFBLEAM"
  VAPID_PRIVATE_KEY: "zvbHKe97bF31FC3iFet-4pbXFzN9TJa_b-QLtfdG_Lg"
  
  # Email - CONFIGURAR CON TU SENDGRID API KEY
  SENDGRID_API_KEY: "TU_SENDGRID_API_KEY_AQUI"
```

## Paso 3: Desplegar localmente

```powershell
# Desde el directorio k8s/scripts/
.\deploy-local.ps1

# O con limpieza previa si hay problemas:
.\deploy-local.ps1 -Force
```

## Paso 4: Verificar el despliegue

```powershell
# Ver estado de todos los recursos
kubectl get all -n firefighter-ai

# URLs de acceso:
# Frontend: http://localhost:30080
# BackOffice: http://localhost:30081  
# Backend: http://localhost:30082

# Ver logs de un servicio específico
kubectl logs -f deployment/frontend -n firefighter-ai
```

## Paso 5: Migrar GitHub Actions a Kubernetes

### 5.1 Reemplazar cd.yml existente
Sustituye tu `.github/workflows/cd.yml` actual por el archivo `cd-kubernetes.yml` que he creado.

### 5.2 Configurar variables de GitHub Secrets
Asegúrate de que tienes estos secrets en tu repositorio:

**Secrets existentes (mantener):**
- `PRODUCTION_HOST` (167.71.63.108)
- `PRODUCTION_USER` (root)
- `PRODUCTION_SSH_KEY`
- `GHCR_USER` / `GHCR_PAT`

**Secrets nuevos necesarios:**
- `MONGO_USER` (joso)
- `MONGO_PASS` (XyGItdDKpWkfJfjT)
- `MONGO_CLUSTER` (cluster0.yzzh9ig.mongodb.net)
- `FRONTEND_SECRET_KEY` / `BACKOFFICE_SECRET_KEY`
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`
- `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY`
- `SENDGRID_API_KEY` / `SENDGRID_SENDER_EMAIL` / `SENDGRID_SENDER_NAME`

## Ventajas del nuevo setup Kubernetes

✅ **Auto-scaling**: Cada servicio puede escalarse independientemente
✅ **Health Checks**: Kubernetes reinicia automáticamente pods que fallan  
✅ **Rolling Updates**: Actualizaciones sin downtime
✅ **Resource Limits**: Control preciso de CPU y memoria
✅ **Service Discovery**: Los servicios se encuentran automáticamente por DNS
✅ **Load Balancing**: Distribución automática de tráfico entre replicas
✅ **Config Management**: Separación clara entre código y configuración
✅ **Persistent Storage**: Volúmenes persistentes para datos
✅ **Monitoring**: Métricas nativas de Kubernetes
✅ **Backup & Rollback**: Fácil rollback a versiones anteriores

## Diferencias clave con Docker Compose

### URLs y comunicación:
- **Docker Compose**: Comunicación por hostname (`backend:5000`)
- **Kubernetes**: Comunicación por service (`backend-service:5000`)

### Escalabilidad:
- **Docker Compose**: Escalado manual con `--scale`
- **Kubernetes**: Escalado declarativo con `replicas: 3`

### Health Checks:
- **Docker Compose**: Health checks básicos
- **Kubernetes**: Health checks sofisticados (liveness, readiness, startup)

### Networking:
- **Docker Compose**: Red bridge simple
- **Kubernetes**: CNI con networking avanzado

## Comandos útiles para gestión

```powershell
# Obtener información del cluster
kubectl cluster-info

# Ver todos los namespaces
kubectl get namespaces

# Ver pods en tiempo real
kubectl get pods -n firefighter-ai -w

# Escalar servicios
kubectl scale deployment/frontend --replicas=3 -n firefighter-ai

# Port forwarding para desarrollo
kubectl port-forward service/backend-service 5000:5000 -n firefighter-ai

# Ver logs de todos los contenedores de un pod
kubectl logs deployment/backend -n firefighter-ai --all-containers=true

# Ejecutar comando en un pod
kubectl exec -it deployment/frontend -n firefighter-ai -- /bin/bash

# Ver uso de recursos
kubectl top pods -n firefighter-ai

# Describir un recurso para troubleshooting
kubectl describe pod <nombre-pod> -n firefighter-ai

# Limpiar todo
.\cleanup.ps1
```

## Solución de problemas

### Si los pods no inician:
```powershell
# Ver eventos del namespace
kubectl get events -n firefighter-ai --sort-by='.lastTimestamp'

# Ver logs de un pod que falló
kubectl logs <nombre-pod> -n firefighter-ai --previous

# Ver descripción detallada del pod
kubectl describe pod <nombre-pod> -n firefighter-ai
```

### Si hay problemas de comunicación entre servicios:
```powershell
# Verificar DNS interno
kubectl exec -it deployment/frontend -n firefighter-ai -- nslookup backend-service

# Probar conectividad desde un pod
kubectl exec -it deployment/frontend -n firefighter-ai -- curl http://backend-service:5000/
```

### Si falta espacio en el servidor:
```powershell
# Limpiar imágenes no utilizadas
kubectl delete pod --field-selector=status.phase==Succeeded -n firefighter-ai

# Ver uso de disco por namespace
kubectl get pods -n firefighter-ai -o=custom-columns=NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName
```

## Migración de producción

Cuando tengas el setup local funcionando:
1. Haz commit y push del nuevo workflow
2. El GitHub Action automáticamente:
   - Instala Kubernetes en tu droplet
   - Migra de Docker Compose a Kubernetes
   - Despliega los servicios con alta disponibilidad

Las URLs de producción seguirán siendo las mismas:
- Frontend: http://167.71.63.108:30080
- Backend: http://167.71.63.108:30082
- BackOffice: http://167.71.63.108:30081

¡Tu aplicación estará ejecutándose en Kubernetes con toda la robustez y escalabilidad que eso conlleva!