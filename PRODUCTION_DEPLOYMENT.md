# 🚀 Despliegue a Producción - SSO Configuration

## 📍 Servidor de Producción

**IP**: `167.71.63.108` (DigitalOcean)

## ✅ Configuración Completada

### Backend (API)

El archivo [api.py](API/api.py#L60-L77) ya está configurado con CORS para:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": [
            # Desarrollo local
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            # Producción - DigitalOcean
            "http://167.71.63.108:8000",
            "http://167.71.63.108:3000",
            "http://167.71.63.108"
        ],
        ...
    }
})
```

### Frontend (FO)

El archivo [sso-handler.js](FO/static/js/sso-handler.js#L7-L28) detecta automáticamente el entorno:

```javascript
const API_BASE_URL = (() => {
  const hostname = window.location.hostname;

  // Desarrollo local
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:5000';
  }

  // Producción - Servidor en DigitalOcean
  if (hostname === '167.71.63.108') {
    return 'http://167.71.63.108:5000';
  }

  // ...
})();
```

---

## 🔐 Configurar SSO para Producción

### Google OAuth 2.0

**1. Authorized JavaScript Origins**

Añade estas URLs en [Google Cloud Console](https://console.cloud.google.com/):

```
http://localhost:8000          # Desarrollo
http://127.0.0.1:8000          # Desarrollo alternativo
http://167.71.63.108:8000      # Producción (con puerto)
http://167.71.63.108           # Producción (sin puerto)
```

**2. Authorized Redirect URIs**

```
http://localhost:8000/login
http://localhost:8000/register
http://167.71.63.108:8000/login
http://167.71.63.108:8000/register
http://167.71.63.108/login
http://167.71.63.108/register
```

**3. OAuth Consent Screen**

Para producción:
- ✅ Cambia de "Testing" a "Production"
- ✅ Completa todos los campos requeridos
- ✅ Añade política de privacidad
- ✅ Añade términos de servicio
- ⚠️ Google puede requerir verificación si superas 100 usuarios

---

### Facebook Login

**1. App Domains**

En [Facebook Developers](https://developers.facebook.com/):

Settings → Basic → App Domains:
```
localhost
167.71.63.108
```

**2. Valid OAuth Redirect URIs**

En Facebook Login → Settings:
```
http://localhost:8000/
http://localhost:8000/login
http://localhost:8000/register
http://167.71.63.108:8000/
http://167.71.63.108:8000/login
http://167.71.63.108:8000/register
http://167.71.63.108/
http://167.71.63.108/login
http://167.71.63.108/register
```

**3. Site URL**

Settings → Basic → Site URL:
```
http://167.71.63.108:8000
```

**4. App Mode**

Para producción:
- ✅ Cambia app de "Development" a "Live"
- ✅ Completa App Review si es necesario
- ✅ Configura Data Deletion URL
- ✅ Añade política de privacidad

---

## 🚀 Desplegar en Producción

### Paso 1: Subir Archivos al Servidor

```bash
# Desde tu máquina local
scp -r API root@167.71.63.108:/var/www/onfire-ai/
scp -r FO root@167.71.63.108:/var/www/onfire-ai/
```

### Paso 2: Instalar Dependencias

```bash
# SSH al servidor
ssh root@167.71.63.108

# API
cd /var/www/onfire-ai/API
pip install -r requirements.txt

# Frontend
cd /var/www/onfire-ai/FO
pip install -r requirements.txt
```

### Paso 3: Configurar Variables de Entorno

```bash
# Crear archivo .env en API
cd /var/www/onfire-ai/API
nano .env
```

Contenido del `.env`:
```env
MONGO_USER=joso
MONGO_PASS=XyGItdDKpWkfJfjT
MONGO_CLUSTER=cluster0.yzzh9ig.mongodb.net
DB_NAME=FIREFIGHTER
SECRET_KEY=tu-secret-key-produccion-super-segura
JWT_EXPIRES_HOURS=24
```

### Paso 4: Iniciar Servicios con Systemd

**API Service** (`/etc/systemd/system/onfire-api.service`):

```ini
[Unit]
Description=Onfire AI API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/onfire-ai/API
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Frontend Service** (`/etc/systemd/system/onfire-frontend.service`):

```ini
[Unit]
Description=Onfire AI Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/onfire-ai/FO
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Activar servicios:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable onfire-api
sudo systemctl enable onfire-frontend
sudo systemctl start onfire-api
sudo systemctl start onfire-frontend

# Verificar estado
sudo systemctl status onfire-api
sudo systemctl status onfire-frontend
```

### Paso 5: Configurar Nginx (Opcional)

Si quieres usar Nginx como proxy reverso:

```nginx
# /etc/nginx/sites-available/onfire-ai

server {
    listen 80;
    server_name 167.71.63.108;

    # Frontend
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, PATCH, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
}
```

Activar:
```bash
sudo ln -s /etc/nginx/sites-available/onfire-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔍 Testing en Producción

### Test 1: Verificar API

```bash
curl http://167.71.63.108:5000/api/health
# Debería retornar: {"status": "ok", ...}
```

### Test 2: Verificar Frontend

Abre en navegador:
```
http://167.71.63.108:8000/login
```

Abre consola (F12) y verifica:
```
🔐 Inicializando SSO...
📡 API URL: http://167.71.63.108:5000
```

### Test 3: Probar SSO

1. Click en "Continuar con Google"
2. Selecciona cuenta
3. Verifica que crea usuario en MongoDB
4. Verifica redirección a dashboard

---

## 🔒 Seguridad en Producción

### ⚠️ IMPORTANTE: Migrar a HTTPS

Para producción real, **debes usar HTTPS**:

1. **Obtener Dominio**
   - Compra dominio (ej: `onfire-ai.com`)
   - Apunta a `167.71.63.108`

2. **Certificado SSL/TLS**
   ```bash
   # Instalar Certbot
   sudo apt install certbot python3-certbot-nginx

   # Obtener certificado
   sudo certbot --nginx -d onfire-ai.com -d www.onfire-ai.com
   ```

3. **Actualizar URLs a HTTPS**
   - En Google OAuth: `https://onfire-ai.com`
   - En Facebook: `https://onfire-ai.com`
   - En código: Cambiar `http://` a `https://`

### Otras Medidas de Seguridad

- ✅ Firewall (UFW):
  ```bash
  sudo ufw allow 22    # SSH
  sudo ufw allow 80    # HTTP
  sudo ufw allow 443   # HTTPS
  sudo ufw enable
  ```

- ✅ Cambiar puerto SSH por defecto
- ✅ Deshabilitar login root
- ✅ Usar claves SSH en lugar de contraseñas
- ✅ Mantener sistema actualizado: `sudo apt update && sudo apt upgrade`
- ✅ Monitoreo con Fail2Ban
- ✅ Backup automático de MongoDB

---

## 📊 Monitoreo

### Logs de Aplicación

```bash
# API logs
sudo journalctl -u onfire-api -f

# Frontend logs
sudo journalctl -u onfire-frontend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Verificar Servicios

```bash
# Estado de servicios
sudo systemctl status onfire-api onfire-frontend nginx

# Reiniciar si es necesario
sudo systemctl restart onfire-api
sudo systemctl restart onfire-frontend
```

---

## 🐛 Troubleshooting Producción

### Error: "Connection refused" al API

```bash
# Verificar que API está corriendo
sudo systemctl status onfire-api

# Ver logs
sudo journalctl -u onfire-api -n 50

# Reiniciar
sudo systemctl restart onfire-api
```

### Error: CORS en producción

Verifica que las URLs están en la configuración:
- `api.py` líneas 69-71
- Google Console → Authorized origins
- Facebook → Valid OAuth Redirect URIs

### Error: "Token expired"

- Verifica `JWT_EXPIRES_HOURS` en `.env`
- Sincroniza hora del servidor: `sudo timedatectl set-ntp true`

---

## 📝 Checklist Pre-Producción

- [ ] Credenciales SSO configuradas (Google + Facebook)
- [ ] URLs de producción añadidas en Google/Facebook
- [ ] Variables de entorno (.env) configuradas
- [ ] MongoDB accesible desde servidor
- [ ] Servicios systemd creados y activos
- [ ] Firewall configurado
- [ ] SSL/TLS configurado (si tienes dominio)
- [ ] Backup de base de datos configurado
- [ ] Logs funcionando correctamente
- [ ] Testing completo de flujo SSO

---

## 🎉 ¡Listo para Producción!

Tu aplicación está configurada para funcionar tanto en:
- 💻 **Desarrollo**: `localhost:8000` → `localhost:5000`
- 🌐 **Producción**: `167.71.63.108:8000` → `167.71.63.108:5000`

El código detecta automáticamente el entorno y usa la configuración correcta.
