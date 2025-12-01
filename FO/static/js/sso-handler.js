/* ========================================
   SSO Handler - Google & Facebook Auth
   ======================================== */

// API Configuration
// Detectar automáticamente el entorno
const API_BASE_URL = (() => {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;

  // Desarrollo local
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:5000';
  }

  // ngrok - Túnel de desarrollo (HTTPS)
  if (hostname.includes('ngrok')) {
    // ngrok usa el mismo dominio para frontend y backend con puertos diferentes
    // Pero como ngrok solo expone un puerto, asumimos que apunta al frontend
    // y el API está en localhost:5000
    return 'http://localhost:5000';
  }

  // Producción - Detección automática basada en hostname
  // Asume que el API está en el mismo host pero puerto 5000
  const currentPort = window.location.port;

  // Si estamos en puerto 8000, 8080 o 3000, el API está en :5000
  if (currentPort === '8000' || currentPort === '8080' || currentPort === '3000') {
    return `${protocol}//${hostname}:5000`;
  }

  // Si no hay puerto específico (puerto 80), asume puerto 5000
  if (!currentPort || currentPort === '80') {
    return `${protocol}//${hostname}:5000`;
  }

  // Default: mismo host con puerto 5000
  return `${protocol}//${hostname}:5000`;
})();

// SSO Configuration
const SSO_CONFIG = {
  google: {
    clientId: '612151576890-uh7sug5ihbt5rhqb021ue5s4udoo01t8.apps.googleusercontent.com',
    scopes: ['profile', 'email'],
    enabled: true,
  },
  facebook: {
    appId: 'YOUR_FACEBOOK_APP_ID', // ⚠️ REEMPLAZAR con tu App ID
    version: 'v18.0',
    enabled: true, // Cambiar a true cuando configures el App ID
  }
};

/**
 * Initialize SSO handlers
 */
function initSSO() {
  console.log('🔐 Inicializando SSO...');
  console.log('📡 API URL:', API_BASE_URL);

  // Load Google SDK only if enabled
  if (SSO_CONFIG.google.enabled) {
    loadGoogleSDK();
  } else {
    console.warn('⚠️ Google SSO deshabilitado. Configura clientId en sso-handler.js');
  }

  // Load Facebook SDK only if enabled
  if (SSO_CONFIG.facebook.enabled) {
    loadFacebookSDK();
  } else {
    console.warn('⚠️ Facebook SSO deshabilitado. Configura appId en sso-handler.js');
  }

  // Setup event listeners
  setupSSOListeners();
}

/**
 * Load Google Identity Services SDK
 */
function loadGoogleSDK() {
  if (document.getElementById('google-sdk')) return;

  const script = document.createElement('script');
  script.id = 'google-sdk';
  script.src = 'https://accounts.google.com/gsi/client';
  script.async = true;
  script.defer = true;
  script.onload = initializeGoogleAuth;
  document.head.appendChild(script);
}

/**
 * Initialize Google Authentication
 */
function initializeGoogleAuth() {
  if (typeof google === 'undefined') return;

  google.accounts.id.initialize({
    client_id: SSO_CONFIG.google.clientId,
    callback: handleGoogleCallback,
    auto_select: false,
  });
}

/**
 * Load Facebook SDK
 */
function loadFacebookSDK() {
  if (document.getElementById('facebook-sdk')) return;

  window.fbAsyncInit = function() {
    FB.init({
      appId: SSO_CONFIG.facebook.appId,
      cookie: true,
      xfbml: true,
      version: SSO_CONFIG.facebook.version
    });
  };

  const script = document.createElement('script');
  script.id = 'facebook-sdk';
  script.src = 'https://connect.facebook.net/es_ES/sdk.js';
  script.async = true;
  script.defer = true;
  document.head.appendChild(script);
}

/**
 * Setup SSO button event listeners
 */
function setupSSOListeners() {
  // Google Login/Register Buttons
  const googleLoginBtn = document.getElementById('googleLoginBtn');
  const googleRegisterBtn = document.getElementById('googleRegisterBtn');

  if (googleLoginBtn) {
    googleLoginBtn.addEventListener('click', handleGoogleLogin);
  }

  if (googleRegisterBtn) {
    googleRegisterBtn.addEventListener('click', handleGoogleLogin);
  }

  // Facebook Login/Register Buttons
  const facebookLoginBtn = document.getElementById('facebookLoginBtn');
  const facebookRegisterBtn = document.getElementById('facebookRegisterBtn');

  if (facebookLoginBtn) {
    facebookLoginBtn.addEventListener('click', handleFacebookLogin);
  }

  if (facebookRegisterBtn) {
    facebookRegisterBtn.addEventListener('click', handleFacebookLogin);
  }
}

/**
 * Handle Google Login Button Click
 */
function handleGoogleLogin() {
  const button = event.currentTarget;

  // Check if Google SSO is enabled
  if (!SSO_CONFIG.google.enabled) {
    showNotification('Google SSO no está configurado. Por favor, configura las credenciales.', 'warning');
    button.classList.add('error');
    setTimeout(() => button.classList.remove('error'), 500);
    return;
  }

  setButtonLoading(button, true);

  try {
    if (typeof google === 'undefined' || !google.accounts) {
      throw new Error('Google SDK no cargado');
    }

    google.accounts.id.prompt((notification) => {
      if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
        // Fallback: Show one-tap dialog
        setButtonLoading(button, false);
        showNotification('Por favor, selecciona una cuenta de Google', 'warning');
      }
    });
  } catch (error) {
    console.error('Error iniciando Google Sign-In:', error);
    setButtonLoading(button, false);
    showNotification('Error al iniciar sesión con Google. Verifica la configuración.', 'error');
  }
}

/**
 * Handle Google Callback
 */
async function handleGoogleCallback(response) {
  const credential = response.credential;

  // Decode JWT to get user info
  const userInfo = parseJWT(credential);

  const ssoData = {
    provider: 'google',
    provider_id: userInfo.sub,
    email: userInfo.email,
    name: userInfo.name,
    photo: userInfo.picture,
    verified: userInfo.email_verified
  };

  await processSSOLogin(ssoData);
}

/**
 * Handle Facebook Login
 */
function handleFacebookLogin() {
  const button = event.currentTarget;

  // Check if Facebook SSO is enabled
  if (!SSO_CONFIG.facebook.enabled) {
    showNotification('Facebook SSO no está configurado. Por favor, configura las credenciales.', 'warning');
    button.classList.add('error');
    setTimeout(() => button.classList.remove('error'), 500);
    return;
  }

  setButtonLoading(button, true);

  if (typeof FB === 'undefined') {
    setButtonLoading(button, false);
    showNotification('Facebook SDK no cargado. Verifica la configuración.', 'error');
    return;
  }

  FB.login(function(response) {
    if (response.authResponse) {
      // User logged in successfully
      getFacebookUserInfo(response.authResponse);
    } else {
      // User cancelled login or didn't authorize
      setButtonLoading(button, false);
      showNotification('Inicio de sesión cancelado', 'info');
    }
  }, {
    scope: 'public_profile,email',
    return_scopes: true
  });
}

/**
 * Get Facebook User Information
 */
function getFacebookUserInfo(authResponse) {
  FB.api('/me', {
    fields: 'id,name,email,picture.type(large)'
  }, async function(response) {
    if (response && !response.error) {
      const ssoData = {
        provider: 'facebook',
        provider_id: response.id,
        email: response.email || '',
        name: response.name,
        photo: response.picture?.data?.url || '',
        verified: response.email ? true : false
      };

      await processSSOLogin(ssoData);
    } else {
      console.error('Error obteniendo info de Facebook:', response.error);
      showNotification('Error al obtener información de Facebook', 'error');
      resetAllButtons();
    }
  });
}

/**
 * Process SSO Login (send to backend)
 */
async function processSSOLogin(ssoData) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/sso-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(ssoData)
    });

    const data = await response.json();

    if (response.ok && data.success) {
      // Store token
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));

      // Show success message
      showNotification(
        data.is_new_user
          ? `¡Bienvenido ${data.user.username}! Cuenta creada exitosamente`
          : `¡Bienvenido de nuevo ${data.user.username}!`,
        'success'
      );

      // Redirect to home page
      setTimeout(() => {
        window.location.href = '/';
      }, 1500);

    } else {
      throw new Error(data.message || 'Error en autenticación SSO');
    }

  } catch (error) {
    console.error('Error en SSO login:', error);
    showNotification(error.message || 'Error al autenticar con SSO', 'error');
    resetAllButtons();
  }
}

/**
 * Set button loading state
 */
function setButtonLoading(button, isLoading) {
  if (!button) return;

  if (isLoading) {
    button.classList.add('loading');
    button.disabled = true;
  } else {
    button.classList.remove('loading');
    button.disabled = false;
  }
}

/**
 * Reset all SSO buttons
 */
function resetAllButtons() {
  const buttons = document.querySelectorAll('.sso-btn');
  buttons.forEach(btn => {
    btn.classList.remove('loading', 'success', 'error');
    btn.disabled = false;
  });
}

/**
 * Parse JWT Token
 */
function parseJWT(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Error parsing JWT:', error);
    return null;
  }
}

/**
 * Show notification to user
 */
function showNotification(message, type = 'info') {
  // Try to use existing notification system
  if (typeof window.showToast === 'function') {
    window.showToast(message, type);
    return;
  }

  // Fallback: Create simple notification
  const notification = document.createElement('div');
  notification.className = `sso-notification sso-notification-${type}`;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    background: ${type === 'success' ? '#34a853' : type === 'error' ? '#ea4335' : '#4285f4'};
    color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    z-index: 10000;
    animation: slideIn 0.3s ease;
    max-width: 400px;
  `;
  notification.textContent = message;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 4000);
}

// Add animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);

// Initialize SSO when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSSO);
} else {
  initSSO();
}

// Export functions for use in other scripts
window.SSOHandler = {
  initSSO,
  processSSOLogin,
  showNotification
};
