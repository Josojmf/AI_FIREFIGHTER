/* ========================================
   SSO Configuration Example
   ======================================== */

/*
 * INSTRUCCIONES:
 *
 * 1. Copia este archivo como referencia
 * 2. Edita sso-handler.js (líneas 11-23)
 * 3. Reemplaza los valores YOUR_* con tus credenciales reales
 * 4. Cambia enabled: false a enabled: true
 *
 * IMPORTANTE: NO subas tus credenciales reales a Git
 */

// ✅ EJEMPLO DE CONFIGURACIÓN CORRECTA
const SSO_CONFIG_EXAMPLE = {
  google: {
    // Obtén esto de: https://console.cloud.google.com/
    // Formato: 1234567890-abcdefgh.apps.googleusercontent.com
    clientId: '1234567890-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com',
    scopes: ['profile', 'email'],
    enabled: true, // ✅ Activo
  },
  facebook: {
    // Obtén esto de: https://developers.facebook.com/apps/
    // Formato: 1234567890123456 (solo números)
    appId: '1234567890123456',
    version: 'v18.0',
    enabled: true, // ✅ Activo
  }
};

// ❌ CONFIGURACIÓN INICIAL (NO FUNCIONAL)
const SSO_CONFIG_DISABLED = {
  google: {
    clientId: 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com', // ⚠️ Sin configurar
    scopes: ['profile', 'email'],
    enabled: false, // ❌ Deshabilitado
  },
  facebook: {
    appId: 'YOUR_FACEBOOK_APP_ID', // ⚠️ Sin configurar
    version: 'v18.0',
    enabled: false, // ❌ Deshabilitado
  }
};

/* ========================================
   PASOS PARA ACTIVAR
   ======================================== */

/*
 * GOOGLE:
 *
 * 1. Ve a: https://console.cloud.google.com/
 * 2. Crea un proyecto: "Onfire AI"
 * 3. Habilita "Google+ API"
 * 4. Crea OAuth 2.0 Client ID (Web application)
 * 5. Añade origen autorizado: http://localhost:8000
 * 6. Añade redirect URI: http://localhost:8000/login
 * 7. Copia el Client ID
 * 8. Pégalo en sso-handler.js línea 14
 * 9. Cambia enabled: true en línea 16
 */

/*
 * FACEBOOK:
 *
 * 1. Ve a: https://developers.facebook.com/
 * 2. Crea una app: "Onfire AI" (tipo: Consumer)
 * 3. Añade producto: Facebook Login
 * 4. En Settings > Basic, añade domain: localhost
 * 5. En Facebook Login > Settings, añade:
 *    Valid OAuth Redirect URIs: http://localhost:8000/login
 * 6. Copia el App ID
 * 7. Pégalo en sso-handler.js línea 19
 * 8. Cambia enabled: true en línea 21
 */

/* ========================================
   VERIFICACIÓN
   ======================================== */

/*
 * Después de configurar, verifica en consola (F12):
 *
 * ✅ Debería aparecer:
 *    🔐 Inicializando SSO...
 *    📡 API URL: http://localhost:5000
 *
 * ❌ NO debería aparecer:
 *    ⚠️ Google SSO deshabilitado
 *    ⚠️ Facebook SSO deshabilitado
 *
 * Si ves las advertencias, verifica:
 * - Que pegaste las credenciales correctamente
 * - Que cambiaste enabled: false a enabled: true
 * - Que guardaste el archivo sso-handler.js
 * - Que recargaste la página (Ctrl+Shift+R)
 */

/* ========================================
   SEGURIDAD
   ======================================== */

/*
 * DESARROLLO (localhost):
 * - OK usar credenciales hardcoded
 * - OK HTTP (no HTTPS)
 * - OK dominios localhost
 *
 * PRODUCCIÓN:
 * - ❌ NO hardcodear credenciales
 * - ✅ Usar variables de entorno
 * - ✅ Solo HTTPS
 * - ✅ Dominios específicos
 * - ✅ OAuth Consent en modo "Production"
 *
 * Ejemplo para producción:
 *
 * const SSO_CONFIG = {
 *   google: {
 *     clientId: import.meta.env.VITE_GOOGLE_CLIENT_ID,
 *     scopes: ['profile', 'email'],
 *     enabled: true,
 *   },
 *   facebook: {
 *     appId: import.meta.env.VITE_FACEBOOK_APP_ID,
 *     version: 'v18.0',
 *     enabled: true,
 *   }
 * };
 */
