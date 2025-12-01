# 🔐 Instrucciones de Configuración SSO

## Configuración de Google OAuth 2.0

### 1. Crear Proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita "Google+ API" en la biblioteca de APIs

### 2. Configurar OAuth Consent Screen

1. Ve a "APIs & Services" → "OAuth consent screen"
2. Selecciona "External" (o "Internal" si es para organización)
3. Completa la información básica:
   - **App name**: Onfire AI
   - **User support email**: tu-email@dominio.com
   - **Developer contact**: tu-email@dominio.com
4. Añade los siguientes scopes:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
5. Guarda y continúa

### 3. Crear Credenciales OAuth

1. Ve a "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Tipo de aplicación: **Web application**
4. Nombre: "Onfire AI Web Client"
5. **Authorized JavaScript origins**:
   ```
   http://localhost:3000
   http://localhost:5000
   https://tu-dominio.com
   ```
6. **Authorized redirect URIs**:
   ```
   http://localhost:3000/login
   http://localhost:3000/register
   https://tu-dominio.com/login
   https://tu-dominio.com/register
   ```
7. Click "Create"
8. **Copia el Client ID** que aparece

### 4. Actualizar Configuración

Edita el archivo `sso-handler.js` y reemplaza:

```javascript
const SSO_CONFIG = {
  google: {
    clientId: 'TU_GOOGLE_CLIENT_ID_AQUI.apps.googleusercontent.com',
    scopes: ['profile', 'email'],
  },
  // ...
};
```

---

## Configuración de Facebook Login

### 1. Crear Aplicación en Facebook Developers

1. Ve a [Facebook Developers](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Selecciona caso de uso: **Consumer**
4. Tipo de aplicación: **None**
5. Nombre de la app: **Onfire AI**
6. Email de contacto: tu-email@dominio.com
7. Click "Create App"

### 2. Configurar Facebook Login

1. En el dashboard de tu app, añade el producto **Facebook Login**
2. Selecciona plataforma: **Web**
3. URL del sitio: `http://localhost:3000` (o tu dominio)

### 3. Configurar Dominios Permitidos

1. Ve a "Settings" → "Basic"
2. Añade los dominios en **App Domains**:
   ```
   localhost
   tu-dominio.com
   ```
3. En **Privacy Policy URL**: añade tu URL de privacidad
4. En **Terms of Service URL**: añade tu URL de términos

### 4. Configurar Valid OAuth Redirect URIs

1. Ve a "Products" → "Facebook Login" → "Settings"
2. En **Valid OAuth Redirect URIs** añade:
   ```
   http://localhost:3000/
   http://localhost:3000/login
   http://localhost:3000/register
   https://tu-dominio.com/
   https://tu-dominio.com/login
   https://tu-dominio.com/register
   ```

### 5. Obtener App ID

1. Ve a "Settings" → "Basic"
2. **Copia el App ID**

### 6. Actualizar Configuración

Edita el archivo `sso-handler.js` y reemplaza:

```javascript
const SSO_CONFIG = {
  // ...
  facebook: {
    appId: 'TU_FACEBOOK_APP_ID_AQUI',
    version: 'v18.0',
  }
};
```

---

## Configuración del Backend API

Asegúrate de que tu API en `api.py` esté corriendo y accesible. Si usas un puerto diferente a 5000, actualiza en `sso-handler.js`:

```javascript
const API_BASE_URL = 'http://localhost:PUERTO'; // Cambia el puerto
```

Para producción:

```javascript
const API_BASE_URL = 'https://api.tu-dominio.com';
```

---

## Variables de Entorno (Opcional)

Para mayor seguridad, puedes usar variables de entorno:

1. Crea un archivo `.env` en la raíz del proyecto FO:

```env
VITE_GOOGLE_CLIENT_ID=tu_google_client_id
VITE_FACEBOOK_APP_ID=tu_facebook_app_id
VITE_API_BASE_URL=http://localhost:5000
```

2. Modifica `sso-handler.js` para usar variables de entorno:

```javascript
const SSO_CONFIG = {
  google: {
    clientId: import.meta.env.VITE_GOOGLE_CLIENT_ID,
    scopes: ['profile', 'email'],
  },
  facebook: {
    appId: import.meta.env.VITE_FACEBOOK_APP_ID,
    version: 'v18.0',
  }
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
```

---

## Testing en Desarrollo

### Google

1. Abre DevTools (F12)
2. Click en el botón "Continuar con Google"
3. Debería aparecer el popup de selección de cuenta
4. Selecciona tu cuenta
5. Verifica en Console que no hay errores
6. Deberías ser redirigido a `/dashboard`

### Facebook

1. Abre DevTools (F12)
2. Click en el botón "Continuar con Facebook"
3. Debería aparecer el popup de Facebook Login
4. Inicia sesión con tu cuenta de Facebook
5. Acepta los permisos solicitados
6. Verifica en Console que no hay errores
7. Deberías ser redirigido a `/dashboard`

---

## Troubleshooting

### Google

- **Error: redirect_uri_mismatch**
  - Verifica que las URIs autorizadas coincidan exactamente con tu URL actual
  - Incluye el protocolo (http:// o https://)
  - No uses trailing slashes

- **Error: invalid_client**
  - Verifica que el Client ID sea correcto
  - Asegúrate de no tener espacios extras al copiar/pegar

### Facebook

- **Error: Can't Load URL**
  - Verifica que el dominio esté en "App Domains"
  - Asegúrate de que la URL esté en "Valid OAuth Redirect URIs"

- **Error: App Not Setup**
  - Verifica que Facebook Login esté añadido como producto
  - Asegúrate de que el App ID sea correcto

### Backend

- **Error: CORS**
  - Verifica que CORS esté habilitado en tu API (`flask_cors`)
  - Añade el origen en la configuración de CORS

- **Error: 500 Internal Server Error**
  - Verifica los logs del servidor API
  - Asegúrate de que MongoDB esté conectado
  - Verifica que los endpoints SSO estén implementados

---

## Modo Producción

Antes de ir a producción:

1. ✅ Cambia el OAuth Consent Screen de "Testing" a "Production"
2. ✅ Añade dominios de producción a las URIs autorizadas
3. ✅ Usa HTTPS para todas las conexiones
4. ✅ Configura variables de entorno seguras
5. ✅ Revisa las políticas de privacidad y términos de servicio
6. ✅ Habilita rate limiting en el backend
7. ✅ Implementa logging de eventos SSO
8. ✅ Configura monitoreo de errores (Sentry, etc.)

---

## Soporte

Si tienes problemas con la configuración:

1. Revisa la consola del navegador (F12)
2. Revisa los logs del servidor API
3. Verifica las configuraciones en Google/Facebook Developers
4. Consulta la documentación oficial:
   - [Google Identity](https://developers.google.com/identity/gsi/web/guides/overview)
   - [Facebook Login](https://developers.facebook.com/docs/facebook-login/web)
