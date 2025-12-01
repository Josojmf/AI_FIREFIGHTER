# 🌍 Configuración Portable - Múltiples Entornos

Esta aplicación está diseñada para funcionar en **cualquier entorno** sin modificar código. Todo se configura mediante **variables de entorno**.

---

## 📋 Tabla de Contenidos

1. [Arquitectura Portable](#arquitectura-portable)
2. [Configuración por Entorno](#configuración-por-entorno)
3. [Guía de Uso](#guía-de-uso)
4. [Troubleshooting](#troubleshooting)

---

## 🏗️ Arquitectura Portable

### Backend (API)

**Archivo**: `API/api.py` (líneas 60-91)

```python
# CORS origins se construyen dinámicamente desde variables de entorno
cors_origins = ["http://localhost:8000", ...]

production_url = os.getenv("PRODUCTION_URL")
if production_url:
    cors_origins.extend([f"{production_url}:8000", ...])

ngrok_url = os.getenv("NGROK_URL")
if ngrok_url:
    cors_origins.append(ngrok_url)
```

**Variables de entorno usadas**:
- `PRODUCTION_URL`: URL de producción (e.g., `http://167.71.63.108`)
- `NGROK_URL`: URL temporal de ngrok (e.g., `https://xyz.ngrok-free.dev`)

### Frontend (FO/BO)

**Archivo**: `FO/static/js/sso-handler.js` (líneas 7-40)

```javascript
const API_BASE_URL = (() => {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;

  // Detección automática del entorno
  if (hostname === 'localhost') return 'http://localhost:5000';
  if (hostname.includes('ngrok')) return 'http://localhost:5000';

  // Producción: mismo hostname con puerto 5000
  return `${protocol}//${hostname}:5000`;
})();
```

**No requiere variables de entorno** - Detección automática basada en URL del navegador.

---

## 🔧 Configuración por Entorno

### 1. Desarrollo Local (localhost)

**Sin ngrok (HTTP)**:

```bash
# API/.env
PRODUCTION_URL=  # Vacío o comentado
NGROK_URL=       # Vacío o comentado
```

**URLs resultantes**:
- Frontend: `http://localhost:8000`
- BackOffice: `http://localhost:8080`
- API: `http://localhost:5000`
- CORS permitido desde: `localhost:8000`, `localhost:8080`, `localhost:3000`

**Iniciar servidores**:
```bash
# Terminal 1 - API
cd API
python api.py

# Terminal 2 - Frontend
cd FO
python main.py

# Terminal 3 - BackOffice
cd BO
python app.py
```

---

### 2. Desarrollo con ngrok (HTTPS)

**Para probar SSO con Google/Facebook** (requieren HTTPS o localhost):

```bash
# 1. Iniciar ngrok
ngrok http 8000

# Output:
# Forwarding  https://abc-xyz-123.ngrok-free.dev -> http://localhost:8000
```

```bash
# 2. Actualizar API/.env
NGROK_URL=https://abc-xyz-123.ngrok-free.dev
```

```bash
# 3. Reiniciar API
cd API
python api.py
```

**URLs resultantes**:
- Frontend (HTTPS): `https://abc-xyz-123.ngrok-free.dev`
- Frontend (local): `http://localhost:8000`
- BackOffice (local): `http://localhost:8080`
- API: `http://localhost:5000`
- CORS permitido desde: `localhost:8000`, `https://abc-xyz-123.ngrok-free.dev`

**Configuración de Google OAuth**:
```
Authorized JavaScript origins:
  http://localhost:8000
  https://abc-xyz-123.ngrok-free.dev

Authorized redirect URIs:
  http://localhost:8000/login
  https://abc-xyz-123.ngrok-free.dev/login
```

---

### 3. Producción (DigitalOcean / VPS)

**Configuración**:

```bash
# API/.env (en el servidor)
PRODUCTION_URL=http://167.71.63.108
NGROK_URL=  # Vacío
```

**URLs resultantes**:
- Frontend: `http://167.71.63.108:8000`
- BackOffice: `http://167.71.63.108:8080`
- API: `http://167.71.63.108:5000`
- CORS permitido desde: `167.71.63.108:8000`, `167.71.63.108:8080`, `167.71.63.108:3000`

**Despliegue**:
```bash
# En el servidor
cd /var/www/ai-firefighter

# Actualizar .env
nano API/.env
# Añadir: PRODUCTION_URL=http://167.71.63.108

# Reiniciar servicios
sudo systemctl restart onfire-api
sudo systemctl restart onfire-frontend
sudo systemctl restart onfire-backoffice
```

---

### 4. Producción con Dominio (Recomendado)

**Configuración**:

```bash
# API/.env (en el servidor)
PRODUCTION_URL=https://onfire-ai.com
NGROK_URL=  # Vacío
```

**URLs resultantes**:
- Frontend: `https://onfire-ai.com`
- BackOffice: `https://onfire-ai.com:8080` (o subdominio: `https://admin.onfire-ai.com`)
- API: `https://onfire-ai.com:5000` (o subdominio: `https://api.onfire-ai.com`)
- CORS permitido desde: `https://onfire-ai.com`, `https://admin.onfire-ai.com`

**Configuración de Google OAuth**:
```
Authorized JavaScript origins:
  https://onfire-ai.com
  https://admin.onfire-ai.com

Authorized redirect URIs:
  https://onfire-ai.com/login
  https://onfire-ai.com/register
```

---

## 📖 Guía de Uso

### Cambiar de Localhost a ngrok

1. **Iniciar ngrok**:
   ```bash
   ngrok http 8000
   ```

2. **Copiar URL generada**:
   ```
   https://new-random-url.ngrok-free.dev
   ```

3. **Actualizar API/.env**:
   ```bash
   NGROK_URL=https://new-random-url.ngrok-free.dev
   ```

4. **Reiniciar API** (Ctrl+C y `python api.py`)

5. **Acceder vía ngrok**:
   ```
   https://new-random-url.ngrok-free.dev
   ```

6. **Verificar CORS** en consola del navegador (F12):
   ```
   🔐 Inicializando SSO...
   📡 API URL: http://localhost:5000
   ```

### Cambiar de ngrok a Producción

1. **SSH al servidor**:
   ```bash
   ssh root@167.71.63.108
   ```

2. **Actualizar .env**:
   ```bash
   cd /var/www/ai-firefighter
   nano API/.env
   ```

3. **Modificar**:
   ```bash
   PRODUCTION_URL=http://167.71.63.108
   NGROK_URL=  # Dejar vacío o eliminar línea
   ```

4. **Reiniciar servicios**:
   ```bash
   sudo systemctl restart onfire-api
   sudo systemctl restart onfire-frontend
   ```

5. **Verificar** en `http://167.71.63.108:8000`

---

## 🐛 Troubleshooting

### Error: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Causa**: El origen no está en la lista de CORS permitidos.

**Solución**:

1. Verifica el archivo `.env`:
   ```bash
   cat API/.env | grep -E "PRODUCTION_URL|NGROK_URL"
   ```

2. Si usas ngrok, asegúrate de que `NGROK_URL` está configurado:
   ```bash
   NGROK_URL=https://tu-url-actual.ngrok-free.dev
   ```

3. Reinicia el API:
   ```bash
   cd API
   python api.py
   ```

4. Verifica en los logs del API que aparece tu URL:
   ```
   CORS permitido desde: [..., 'https://tu-url-actual.ngrok-free.dev']
   ```

### Error: "API URL apunta a localhost pero estoy en producción"

**Causa**: El frontend no detecta correctamente el entorno.

**Solución**:

1. Abre consola del navegador (F12) en la página de login

2. Verifica qué API URL detectó:
   ```javascript
   console.log(API_BASE_URL);
   ```

3. Si es incorrecto, verifica la URL del navegador:
   - ✅ Correcto: `http://167.71.63.108:8000/login`
   - ❌ Incorrecto: `http://localhost:8000/login`

### ngrok cambia de URL cada vez

**Esto es normal con ngrok gratuito**. Cada vez que reinicias ngrok, obtienes una nueva URL.

**Soluciones**:

1. **Desarrollo**: Actualiza `NGROK_URL` en `.env` cada vez
2. **Testing prolongado**: Usa ngrok de pago para URL fija
3. **Producción**: Usa un dominio real

---

## ✅ Checklist de Despliegue

### Desarrollo Local
- [ ] `.env` tiene `NGROK_URL` vacío
- [ ] API corriendo en `localhost:5000`
- [ ] Frontend corriendo en `localhost:8000`
- [ ] BackOffice corriendo en `localhost:8080`
- [ ] Login funciona sin errores CORS

### Desarrollo con ngrok
- [ ] ngrok iniciado: `ngrok http 8000`
- [ ] `NGROK_URL` actualizado en `API/.env`
- [ ] API reiniciado
- [ ] Google OAuth configurado con ngrok URL
- [ ] SSO funciona vía HTTPS

### Producción
- [ ] `PRODUCTION_URL` configurado en `API/.env`
- [ ] `NGROK_URL` vacío o eliminado
- [ ] Servicios systemd configurados
- [ ] Firewall permite puertos 5000, 8000, 8080
- [ ] Google OAuth configurado con IP/dominio de producción
- [ ] SSL/TLS configurado (si usas dominio)

---

## 📚 Referencias

- **Variables de entorno**: [.env.example](.env.example)
- **Configuración SSO**: [QUICK_SSO_SETUP.md](QUICK_SSO_SETUP.md)
- **Despliegue producción**: [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)

---

**Última actualización**: 1 de Diciembre 2025
**Versión**: 2.0 - Completamente Portable
