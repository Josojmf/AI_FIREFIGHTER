# 🚀 Guía Rápida - Configuración SSO

## ⚡ Setup en 5 Minutos

### Paso 1: Obtener Google Client ID

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto nuevo llamado "Onfire AI"
3. Ve a "APIs & Services" → "Credentials"
4. Click "Create Credentials" → "OAuth 2.0 Client ID"
5. Configura la pantalla de consentimiento (External):
   - App name: **Onfire AI**
   - User support email: tu-email@gmail.com
   - Developer contact: tu-email@gmail.com
6. Crea las credenciales:
   - Application type: **Web application**
   - Name: **Onfire AI Web**
   - Authorized JavaScript origins:
     ```
     http://localhost:8000
     http://127.0.0.1:8000
     http://167.71.63.108:8000
     http://167.71.63.108
     ```
   - Authorized redirect URIs:
     ```
     http://localhost:8000/login
     http://localhost:8000/register
     http://167.71.63.108:8000/login
     http://167.71.63.108:8000/register
     http://167.71.63.108/login
     http://167.71.63.108/register
     ```
7. **Copia el Client ID** (algo como: `123456789-abc.apps.googleusercontent.com`)

### Paso 2: Obtener Facebook App ID

1. Ve a [Facebook Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Tipo: **Consumer**
4. Nombre: **Onfire AI**
5. Añade el producto **Facebook Login**
6. Configuración básica:
   - App Domains: `localhost`, `167.71.63.108`
   - Privacy Policy URL: `http://167.71.63.108/privacy` (o tu URL)
7. Facebook Login Settings:
   - Valid OAuth Redirect URIs:
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
8. **Copia el App ID** desde "Settings" → "Basic"

### Paso 3: Actualizar Configuración

Edita el archivo: `FO/static/js/sso-handler.js`

Busca estas líneas (11-22) y reemplaza:

```javascript
const SSO_CONFIG = {
  google: {
    clientId: 'TU_CLIENT_ID_AQUI.apps.googleusercontent.com', // ⚠️ PEGA TU CLIENT ID
    scopes: ['profile', 'email'],
    enabled: true, // ⚠️ Cambia a true
  },
  facebook: {
    appId: 'TU_APP_ID_AQUI', // ⚠️ PEGA TU APP ID
    version: 'v18.0',
    enabled: true, // ⚠️ Cambia a true
  }
};
```

### Paso 4: Reiniciar Servidores

```bash
# Terminal 1 - API
cd C:\INFORMATICA\AI_Firefighter\API
python api.py

# Terminal 2 - Frontend
cd C:\INFORMATICA\AI_Firefighter\FO
python main.py
```

### Paso 5: Probar

1. Abre: http://localhost:8000/login
2. Click en "Continuar con Google" o "Continuar con Facebook"
3. Deberías ver el popup de autenticación
4. Al autenticarte, se creará tu usuario y serás redirigido a `/dashboard`

---

## ✅ Verificación

### Consola del Navegador (F12)

Deberías ver:
```
🔐 Inicializando SSO...
📡 API URL: http://localhost:5000
```

**NO** deberías ver:
```
⚠️ Google SSO deshabilitado
⚠️ Facebook SSO deshabilitado
```

### Logs del API

Al hacer login SSO, deberías ver:
```
🔥 Login SSO: google - usuario@gmail.com
✅ Usuario existente encontrado: usuario@gmail.com
🎉 Login SSO exitoso: usuario@gmail.com via google
```

---

## 🐛 Solución de Problemas

### Error: "Google SSO no está configurado"
**Causa**: `enabled: false` en SSO_CONFIG
**Solución**: Cambia a `enabled: true` después de pegar tu Client ID

### Error: "redirect_uri_mismatch"
**Causa**: URI no autorizada en Google Console
**Solución**: Verifica que `http://localhost:8000/login` esté en "Authorized redirect URIs"

### Error: "Can't Load URL" (Facebook)
**Causa**: Dominio no permitido
**Solución**: Añade `localhost` en "App Domains" de Facebook

### Error CORS en consola
**Causa**: API no permite requests desde frontend
**Solución**: Ya está solucionado en `api.py` líneas 60-72

---

## 🎯 Testing Rápido

### Google

1. Click botón Google
2. Selecciona tu cuenta Gmail
3. Permite acceso a perfil y email
4. ✅ Deberías ver: "¡Bienvenido [username]!"
5. ✅ Redirigido a dashboard

### Facebook

1. Click botón Facebook
2. Login con tu cuenta Facebook
3. Permite acceso a perfil y email
4. ✅ Deberías ver: "¡Bienvenido [username]!"
5. ✅ Redirigido a dashboard

---

## 📊 Verificar en MongoDB

Después del primer login, verifica que el usuario se creó:

```javascript
// En MongoDB Compass o Atlas
db.users.findOne({ "sso_providers.google": { $exists: true } })

// Deberías ver algo como:
{
  "_id": ObjectId("..."),
  "username": "google_12345678",
  "email": "tu-email@gmail.com",
  "password_hash": null,
  "sso_providers": {
    "google": {
      "provider_id": "1234567890",
      "connected_at": ISODate("..."),
      "photo_url": "https://..."
    }
  },
  "profile": {
    "full_name": "Tu Nombre",
    "photo_url": "https://...",
    "auth_method": "sso_google"
  },
  "leitner_data": { ... }
}
```

---

## 🔒 Seguridad

### Modo Desarrollo (Ahora)
- ✅ localhost permitido
- ✅ HTTP permitido
- ⚠️ Client secrets visibles en código

### Modo Producción (Futuro)
- ✅ Solo HTTPS
- ✅ Dominios específicos permitidos
- ✅ Variables de entorno para secrets
- ✅ OAuth Consent Screen en "Production"

---

## 📝 Notas Importantes

1. **No compartas tus credenciales** (Client ID, App ID) públicamente
2. **En producción**, usa variables de entorno
3. **Google** requiere verificación si excedes 100 usuarios
4. **Facebook** requiere App Review para apps públicas
5. Los usuarios SSO **no tienen contraseña** inicialmente
6. Pueden vincular múltiples proveedores (Google + Facebook)

---

## 🎉 ¡Listo!

Si seguiste todos los pasos, SSO debería estar funcionando.

Para soporte adicional, revisa:
- `FO/static/js/SSO_SETUP_INSTRUCTIONS.md` (guía detallada)
- `SSO_INTEGRATION_SUMMARY.md` (resumen técnico completo)
