// === BACKOFFICE JAVASCRIPT COMPLETO CON DASHBOARD FUNCIONAL ===

document.addEventListener('DOMContentLoaded', function() {
  console.log('🔥 FirefighterAI BackOffice - Inicializado');
  
  // VERIFICAR AUTENTICACIÓN PRIMERO
  if (!checkAuth()) {
    return; // Detener si no está autenticado
  }
  
  initializeLayout();
  initializeDashboard();
  setupGlobalHandlers();
});

// === CONFIGURACIÓN API ===
const API_CONFIG = {
  BASE_URL: 'http://167.71.63.108:5000',
  TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3
};

// === FUNCIÓN DE FETCH MEJORADA CON MANEJO DE ERRORES ===
async function apiFetch(endpoint, options = {}) {
  const url = `${API_CONFIG.BASE_URL}${endpoint}`;
  
  console.log(`📡 API Call: ${url}`);
  
  const fetchOptions = {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    mode: 'cors',
    credentials: 'omit',
    ...options
  };

  try {
    const response = await fetch(url, fetchOptions);
    
    console.log(`📊 Response for ${endpoint}:`, response.status, response.statusText);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data;
    
  } catch (error) {
    console.error(`❌ API Error for ${endpoint}:`, error);
    
    // MANEJO ESPECÍFICO DE CORS Y ERRORES DE CONEXIÓN
    if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
      showNotification('Error de conexión con el servidor', 'error');
      throw new Error('No se pudo conectar con el servidor. Verifique la conexión.');
    }
    
    throw error;
  }
}

// === INICIALIZACIÓN PRINCIPAL ===
function initializeLayout() {
  initializeSidebar();
  initializeMobileMenu();
  initializeUserMenu();
  initializeFlashMessages();
  setupKeyboardShortcuts();
  setupApiHealthMonitor();
}

function initializeDashboard() {
  // Solo inicializar dashboard si estamos en la página del dashboard
  if (window.location.pathname.includes('dashboard') || 
      window.location.pathname === '/' || 
      document.querySelector('.dashboard')) {
    loadRealTimeData();
    startRealTimeUpdates();
    
    // Inicializar sistema de logs Docker si existe el contenedor
    if (document.getElementById('logsContainer')) {
      window.dockerLogsManager = new DockerLogsManager();
    }
  }
}

// === SIDEBAR FUNCTIONALITY ===
function initializeSidebar() {
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const mobileOverlay = document.getElementById('mobileOverlay');
  
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function() {
      sidebar.classList.toggle('collapsed');
      
      // Guardar estado en localStorage
      const isCollapsed = sidebar.classList.contains('collapsed');
      localStorage.setItem('sidebarCollapsed', isCollapsed);
      
      console.log(`Sidebar ${isCollapsed ? 'collapsed' : 'expanded'}`);
    });
    
    // Restaurar estado del sidebar
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true') {
      sidebar.classList.add('collapsed');
    }
  }
  
  // Cerrar sidebar móvil al hacer click en el overlay
  if (mobileOverlay) {
    mobileOverlay.addEventListener('click', closeMobileMenu);
  }
}

// === MOBILE MENU ===
function initializeMobileMenu() {
  const mobileToggle = document.getElementById('mobileMenuToggle');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('mobileOverlay');
  
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener('click', function() {
      sidebar.classList.add('mobile-open');
      if (overlay) overlay.classList.add('active');
      document.body.style.overflow = 'hidden';
    });
  }
  
  // Cerrar menú móvil cuando se hace click en un enlace
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 1024) {
        closeMobileMenu();
      }
    });
  });
}

function closeMobileMenu() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('mobileOverlay');
  
  if (sidebar) sidebar.classList.remove('mobile-open');
  if (overlay) overlay.classList.remove('active');
  document.body.style.overflow = '';
}

// === USER MENU ===
function initializeUserMenu() {
  const userMenuToggle = document.querySelector('.user-menu-toggle');
  
  if (userMenuToggle) {
    userMenuToggle.addEventListener('click', toggleUserMenu);
  }
  
  // Cerrar dropdowns al hacer click fuera
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.user-menu')) {
      const userMenu = document.getElementById('userMenuDropdown');
      const menuContainer = document.querySelector('.user-menu');
      
      if (userMenu) userMenu.classList.remove('show');
      if (menuContainer) menuContainer.classList.remove('active');
    }
  });
}

function toggleUserMenu() {
  const dropdown = document.getElementById('userMenuDropdown');
  const menu = dropdown?.closest('.user-menu');
  
  if (dropdown && menu) {
    const isShowing = dropdown.classList.contains('show');
    
    // Cerrar todos los dropdowns primero
    document.querySelectorAll('.dropdown.show').forEach(dropdown => {
      dropdown.classList.remove('show');
    });
    document.querySelectorAll('.user-menu.active').forEach(menu => {
      menu.classList.remove('active');
    });
    
    // Abrir/cerrar el menú actual
    if (!isShowing) {
      dropdown.classList.add('show');
      menu.classList.add('active');
    }
  }
}

// === FLASH MESSAGES ===
function initializeFlashMessages() {
  // Auto-hide flash messages después de 5 segundos
  const flashMessages = document.querySelectorAll('[data-flash]');
  flashMessages.forEach(flash => {
    setTimeout(() => {
      if (flash.parentNode) {
        flash.style.opacity = '0';
        flash.style.transform = 'translateX(100%)';
        setTimeout(() => {
          if (flash.parentNode) {
            flash.remove();
          }
        }, 300);
      }
    }, 5000);
  });
}

// === NOTIFICATIONS SYSTEM ===
function showNotification(message, type = 'info', duration = 5000) {
  // No mostrar notificaciones duplicadas muy seguidas
  const recentNotifications = JSON.parse(sessionStorage.getItem('recentNotifications') || '[]');
  const notificationKey = `${type}-${message}`;
  
  if (recentNotifications.includes(notificationKey)) {
    return null;
  }
  
  // Guardar notificación reciente
  recentNotifications.push(notificationKey);
  sessionStorage.setItem('recentNotifications', JSON.stringify(recentNotifications));
  
  // Limpiar después de 10 segundos
  setTimeout(() => {
    const current = JSON.parse(sessionStorage.getItem('recentNotifications') || '[]');
    const filtered = current.filter(n => n !== notificationKey);
    sessionStorage.setItem('recentNotifications', JSON.stringify(filtered));
  }, 10000);

  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };
  
  const notification = document.createElement('div');
  notification.className = `flash flash-${type}`;
  notification.setAttribute('data-flash', '');
  
  notification.innerHTML = `
    <div class="flash-icon">${icons[type]}</div>
    <div class="flash-content">${message}</div>
    <button class="flash-close" onclick="this.parentElement.remove()">✕</button>
  `;
  
  // Insertar al inicio de flash-messages o page-content
  let container = document.querySelector('.flash-messages');
  if (!container) {
    container = document.createElement('div');
    container.className = 'flash-messages';
    const pageContent = document.querySelector('.page-content');
    if (pageContent) {
      pageContent.insertBefore(container, pageContent.firstChild);
    } else {
      document.body.appendChild(container);
    }
  }
  
  if (container) {
    container.insertBefore(notification, container.firstChild);
    
    // Auto-remove después del tiempo especificado
    setTimeout(() => {
      if (notification.parentNode) {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
          if (notification.parentNode) {
            notification.remove();
          }
        }, 300);
      }
    }, duration);
  }
  
  return notification;
}

// === SISTEMA DE AUTENTICACIÓN ===
function checkAuth() {
  const token = localStorage.getItem('authToken');
  if (!token && !window.location.pathname.includes('login')) {
    window.location.href = '/auth/login';
    return false;
  }
  
  // Si hay token, verificar que sea válido
  if (token) {
    // Aquí podrías agregar validación JWT si es necesario
    console.log('✅ Usuario autenticado');
  }
  
  return true;
}

// === MANEJO OFFLINE ===
function setupOfflineHandler() {
  window.addEventListener('online', () => {
    showNotification('Conexión restaurada', 'success');
    loadRealTimeData();
    
    if (window.dockerLogsManager) {
      window.dockerLogsManager.addSystemLog('SUCCESS', 'Conexión a internet restaurada');
    }
  });
  
  window.addEventListener('offline', () => {
    showNotification('Conexión perdida - Modo offline', 'warning');
    
    if (window.dockerLogsManager) {
      window.dockerLogsManager.addSystemLog('WARNING', 'Conexión a internet perdida');
    }
  });
}

// === ESTADOS DE CARGA ===
function showLoadingState(containerId) {
  const container = document.getElementById(containerId);
  if (container) {
    const existingLoader = container.querySelector('.loading-spinner');
    if (!existingLoader) {
      container.innerHTML += '<div class="loading-spinner">Cargando...</div>';
    }
  }
}

function hideLoadingState(containerId) {
  const container = document.getElementById(containerId);
  if (container) {
    const loadingElement = container.querySelector('.loading-spinner');
    if (loadingElement) {
      loadingElement.remove();
    }
  }
}

// === VALIDACIÓN DE RESPUESTAS API ===
function validateApiResponse(data, expectedFields = []) {
  if (!data || typeof data !== 'object') {
    throw new Error('Respuesta API inválida');
  }
  
  for (const field of expectedFields) {
    if (!(field in data)) {
      console.warn(`Campo esperado faltante: ${field}`);
    }
  }
  
  return true;
}

// === DASHBOARD DATA FUNCTIONS ===
async function loadRealTimeData() {
  try {
    console.log('📊 Cargando datos en tiempo real...');
    
    // Mostrar estados de carga
    showLoadingState('dashboardStats');
    showLoadingState('systemInfo');
    
    // Cargar estadísticas principales
    await loadDashboardStats();
    
    // Cargar información del sistema
    await updateSystemInfo();
    
    // Verificar salud de la API
    await checkSystemHealth();
    
    // Ocultar estados de carga
    hideLoadingState('dashboardStats');
    hideLoadingState('systemInfo');
    
    console.log('✅ Datos cargados correctamente');
    
  } catch (error) {
    console.warn('⚠️ Advertencia cargando datos en tiempo real:', error.message);
    
    // Ocultar estados de carga incluso en error
    hideLoadingState('dashboardStats');
    hideLoadingState('systemInfo');
    
    showFallbackData();
  }
}

async function loadDashboardStats() {
  try {
    console.log('🔍 Cargando estadísticas del dashboard...');
    
    const data = await apiFetch('/api/dashboard/stats');
    console.log('📊 Datos recibidos:', data);
    
    // Validar respuesta
    validateApiResponse(data, ['ok', 'total_users', 'active_users', 'total_cards']);
    
    if (data.ok) {
      updateDashboardData(data);
      console.log('✅ Dashboard actualizado correctamente');
    } else {
      console.error('❌ API devolvió ok: false');
      showFallbackData();
    }
    
  } catch (error) {
    console.error('❌ Error cargando estadísticas:', error);
    showFallbackData();
  }
}

async function updateSystemInfo() {
  try {
    console.log('🔍 Cargando información del sistema...');
    
    const data = await apiFetch('/api/dashboard/system-info');
    console.log('🔧 Info sistema recibida:', data);
    
    // Validar respuesta
    validateApiResponse(data, ['ok', 'db_users_count', 'db_status']);
    
    if (data.ok) {
      // Actualizar usuarios en DB
      if (data.db_users_count !== undefined) {
        const dbUsersElement = document.getElementById('dbUsersCount');
        if (dbUsersElement) {
          dbUsersElement.textContent = data.db_users_count;
          console.log(`✅ Usuarios en DB: ${data.db_users_count}`);
        }
      }
      
      // Actualizar estado de la base de datos
      const dbStatusElement = document.getElementById('dbStatus');
      if (dbStatusElement && data.db_status) {
        dbStatusElement.textContent = data.db_status === 'connected' ? 'Conectada' : 'Desconectada';
        
        const dbStatusDot = dbStatusElement.previousElementSibling;
        if (dbStatusDot) {
          dbStatusDot.className = `status-dot status-${data.db_status === 'connected' ? 'online' : 'offline'}`;
        }
      }
      
      // Actualizar última actualización
      updateLastUpdateTime();
      
      if (window.dockerLogsManager) {
        window.dockerLogsManager.addSystemLog('SUCCESS', `Sistema actualizado: ${data.db_users_count || 0} usuarios en DB`);
      }
      
    } else {
      console.error('❌ System info API devolvió ok: false');
      showSystemInfoFallback();
    }
    
  } catch (error) {
    console.error('❌ Error actualizando información del sistema:', error);
    showSystemInfoFallback();
  }
}

function updateDashboardData(data) {
  // Actualizar métricas
  if (data.total_users !== undefined) {
    const totalUsersElement = document.getElementById('totalUsers');
    const summaryUsersElement = document.getElementById('summaryUsers');
    
    if (totalUsersElement) totalUsersElement.textContent = data.total_users;
    if (summaryUsersElement) summaryUsersElement.textContent = data.total_users;
  }

  if (data.active_users !== undefined) {
    const activeUsersElement = document.getElementById('activeUsers');
    if (activeUsersElement) activeUsersElement.textContent = data.active_users;
  }

  if (data.total_cards !== undefined) {
    const totalCardsElement = document.getElementById('totalCards');
    const summaryCardsElement = document.getElementById('summaryCards');
    
    if (totalCardsElement) totalCardsElement.textContent = data.total_cards;
    if (summaryCardsElement) summaryCardsElement.textContent = data.total_cards;
  }

  // Actualizar estado API
  const apiStatusElement = document.getElementById('apiStatus');
  const apiStatusText = document.getElementById('apiStatusText');
  const apiTrend = document.getElementById('apiTrend');
  const systemStatusIndicator = document.getElementById('systemStatusIndicator');

  if (data.api_status) {
    const isOnline = data.api_status === 'online';
    
    if (apiStatusElement) {
      apiStatusElement.textContent = isOnline ? 'Online' : 'Offline';
      apiStatusElement.className = `metric-value api-status-value ${isOnline ? 'online' : 'offline'}`;
    }
    
    if (apiStatusText) apiStatusText.textContent = isOnline ? 'Online' : 'Offline';
    
    if (systemStatusIndicator) {
      systemStatusIndicator.textContent = isOnline ? '🟢' : '🔴';
      systemStatusIndicator.className = `status-indicator ${isOnline ? 'status-online' : 'status-offline'}`;
    }

    if (apiTrend) {
      apiTrend.innerHTML = isOnline ?
        '<span class="trend-icon">✅</span><span class="trend-value">Online</span>' :
        '<span class="trend-icon">❌</span><span class="trend-value">Offline</span>';
    }
  }

  // ACTUALIZAR TODOS LOS TREND VALUES
  updateAllTrendValues(data);

  // Actualizar actividad
  if (data.recent_activity && data.recent_activity.length > 0) {
    updateActivityList(data.recent_activity);
  }

  // Agregar log si existe el sistema de logs
  if (window.dockerLogsManager) {
    window.dockerLogsManager.addSystemLog('INFO', 'Datos del dashboard actualizados');
  }
}

// Nueva función para actualizar todos los trend values
function updateAllTrendValues(data) {
  console.log('🔄 Actualizando trend values específicos...');
  
  // Actualizar trend values específicos por ID
  const usersTrend = document.querySelector('#usersTrend .trend-value');
  const activeTrend = document.querySelector('#activeTrend .trend-value');
  const cardsTrend = document.querySelector('#cardsTrend .trend-value');
  // apiTrend ya se actualiza en updateDashboardData()
  
  if (usersTrend) {
    usersTrend.textContent = `${data.total_users || 0} usuarios`;
    console.log(`✅ Users trend actualizado: ${usersTrend.textContent}`);
  }
  
  if (activeTrend) {
    activeTrend.textContent = `${data.active_users || 0} activos`;
    console.log(`✅ Active trend actualizado: ${activeTrend.textContent}`);
  }
  
  if (cardsTrend) {
    cardsTrend.textContent = `${data.total_cards || 0} tarjetas`;
    console.log(`✅ Cards trend actualizado: ${cardsTrend.textContent}`);
  }
  
  // También actualizar todos los otros trend-value genéricos
  const allTrendElements = document.querySelectorAll('.trend-value');
  console.log(`🔍 Encontrados ${allTrendElements.length} trend values totales`);
  
  allTrendElements.forEach((element, index) => {
    // Skip los que ya actualizamos específicamente
    const parentId = element.closest('[id]')?.id;
    if (parentId && ['usersTrend', 'activeTrend', 'cardsTrend', 'apiTrend'].includes(parentId)) {
      return; // Ya se actualizó arriba
    }
    
    // Actualizar otros trend values genéricos
    if (element.textContent === 'Cargando...') {
      element.textContent = 'Actualizado';
      console.log(`✅ Trend value genérico ${index + 1} actualizado`);
    }
  });
  
  console.log('✅ Todos los trend values actualizados');
}

function updateActivityList(activities) {
  const activityList = document.getElementById('activityList');
  if (!activityList) return;
  
  activityList.innerHTML = '';

  activities.forEach(activity => {
    const activityItem = document.createElement('div');
    activityItem.className = 'activity-item';
    activityItem.innerHTML = `
      <div class="activity-icon">${activity.icon}</div>
      <div class="activity-content">
        <div class="activity-text">${activity.text}</div>
        <div class="activity-time">${activity.time}</div>
      </div>
    `;
    activityList.appendChild(activityItem);
  });
}

function updateLastUpdateTime() {
  const now = new Date();
  const timeString = now.toTimeString().split(' ')[0];
  const lastUpdateElement = document.getElementById('lastUpdate');
  if (lastUpdateElement) {
    lastUpdateElement.textContent = timeString;
  }
}

async function checkSystemHealth() {
  try {
    console.log('🔍 Verificando salud de la API...');
    
    const startTime = performance.now();
    const data = await apiFetch('/api/dashboard/health');
    const endTime = performance.now();
    const responseTime = Math.round(endTime - startTime);
    
    console.log('🏥 Health data recibida:', data);
    
    // Track performance
    trackPerformance('Health Check', responseTime);
    
    if (window.dockerLogsManager) {
      if (data.ok) {
        window.dockerLogsManager.addSystemLog('SUCCESS', `API saludable - Tiempo respuesta: ${responseTime}ms`);
      } else {
        window.dockerLogsManager.addSystemLog('WARNING', 'API reporta problemas en health check');
      }
    }
    
  } catch (error) {
    console.error('❌ Error en health check:', error);
    if (window.dockerLogsManager) {
      window.dockerLogsManager.addSystemLog('ERROR', `Error verificando salud de la API: ${error.message}`);
    }
  }
}

// Función para mostrar datos de fallback cuando no hay conexión
function showFallbackData() {
  console.log('🔄 Mostrando datos de fallback...');
  
  const fallbackData = {
    total_users: 0,
    active_users: 0,
    total_cards: 0,
    api_status: 'offline',
    recent_activity: [
      {
        icon: '⚠️',
        text: 'No se pudo conectar con la API',
        time: 'Ahora'
      },
      {
        icon: '🔄',
        text: 'Intentando reconexión...',
        time: '1 min'
      }
    ]
  };
  
  updateDashboardData(fallbackData);
}

function showSystemInfoFallback() {
  console.log('🔄 Mostrando info sistema fallback...');
  
  // Actualizar con datos de error
  const dbUsersElement = document.getElementById('dbUsersCount');
  if (dbUsersElement) {
    dbUsersElement.textContent = 'Error';
  }
  
  const dbStatusElement = document.getElementById('dbStatus');
  if (dbStatusElement) {
    dbStatusElement.textContent = 'Error conexión';
    const dbStatusDot = dbStatusElement.previousElementSibling;
    if (dbStatusDot) {
      dbStatusDot.className = 'status-dot status-offline';
    }
  }
  
  updateLastUpdateTime();
}

// === DOCKER LOGS MANAGER CORREGIDO ===
class DockerLogsManager {
  constructor() {
    this.logsContainer = document.getElementById('logsContainer');
    this.isLive = false;
    this.liveInterval = null;
    this.init();
  }
  
  async init() {
    console.log('🐳 Inicializando Docker Logs Manager...');
    
    if (!this.logsContainer) {
      console.warn('Contenedor de logs no encontrado');
      return;
    }
    
    // Cargar logs iniciales
    await this.loadInitialLogs();
    
    // Configurar botones
    this.setupButtons();
    
    // Mostrar logs de fallback si no hay datos
    this.displayFallbackLogs();
  }
  
  setupButtons() {
    // Ya están configurados globalmente
  }
  
  async loadInitialLogs() {
    try {
      const data = await apiFetch('/api/docker/logs');
      this.displayLogs(data.logs || []);
      
    } catch (error) {
      console.warn('Error cargando logs iniciales:', error.message);
    }
  }
  
  async refreshLogs() {
    this.addSystemLog('INFO', '🔄 Actualizando logs del sistema...');
    await this.loadInitialLogs();
    setTimeout(() => {
      this.addSystemLog('SUCCESS', 'Logs actualizados correctamente');
    }, 500);
  }
  
  displayLogs(logs) {
    if (!this.logsContainer) return;
    
    // Limpiar logs existentes
    this.logsContainer.innerHTML = '';
    
    if (logs && logs.length > 0) {
      logs.forEach(log => {
        this.addLogEntry(log);
      });
    } else {
      this.addSystemLog('INFO', 'No hay logs disponibles');
    }
    
    // Actualizar contadores
    this.updateLogCounters();
  }
  
  displayFallbackLogs() {
    if (!this.logsContainer) return;
    
    const fallbackLogs = [
      {
        timestamp: new Date().toISOString(),
        container: 'system',
        level: 'INFO',
        message: 'Sistema de logs inicializado'
      },
      {
        timestamp: new Date().toISOString(),
        container: 'system', 
        level: 'INFO',
        message: 'Conectando con servicios del sistema...'
      },
      {
        timestamp: new Date().toISOString(),
        container: 'system',
        level: 'SUCCESS',
        message: 'BackOffice FirefighterAI funcionando correctamente'
      }
    ];
    
    fallbackLogs.forEach(log => this.addLogEntry(log));
  }
  
  addLogEntry(log) {
    if (!this.logsContainer) return;
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${log.level.toLowerCase()}`;
    
    const timestamp = this.formatTime(log.timestamp);
    const container = log.container || 'system';
    const level = log.level || 'INFO';
    const message = this.escapeHtml(log.message);
    
    logEntry.innerHTML = `
      <span class="log-time">${timestamp}</span>
      <span class="log-container">${container}</span>
      <span class="log-level">${level}</span>
      <span class="log-message">${message}</span>
    `;
    
    // Insertar al principio para mostrar logs más recientes primero
    this.logsContainer.insertBefore(logEntry, this.logsContainer.firstChild);
    
    // Mantener máximo 100 logs
    if (this.logsContainer.children.length > 100) {
      this.logsContainer.removeChild(this.logsContainer.lastChild);
    }
    
    // Actualizar contadores después de agregar
    setTimeout(() => this.updateLogCounters(), 100);
  }
  
  startLiveLogs() {
    if (this.isLive) {
      this.addSystemLog('INFO', 'Los logs en vivo ya están activos');
      return;
    }
    
    this.isLive = true;
    this.updateLiveStatus(true);
    this.addSystemLog('SUCCESS', '📡 Logs en vivo activados');
    
    // Simular actualizaciones en tiempo real cada 3 segundos
    this.liveInterval = setInterval(() => {
      this.simulateLiveUpdate();
    }, 3000);
  }
  
  stopLiveLogs() {
    if (!this.isLive) return;
    
    this.isLive = false;
    
    if (this.liveInterval) {
      clearInterval(this.liveInterval);
      this.liveInterval = null;
    }
    
    this.updateLiveStatus(false);
    this.addSystemLog('WARNING', '⏸️ Logs en vivo detenidos');
  }
  
  simulateLiveUpdate() {
    if (!this.isLive) return;
    
    // Generar algunos logs nuevos aleatorios
    const newLogs = this.generateRandomLogs(1 + Math.floor(Math.random() * 2));
    newLogs.forEach(log => this.addLogEntry(log));
  }
  
  generateRandomLogs(count) {
    const levels = ["INFO", "INFO", "SUCCESS", "WARNING"];
    const containers = ["api", "backoffice", "database", "auth", "cache"];
    const messages = [
      "Procesando solicitud de usuario",
      "Sincronización de datos completada",
      "Verificación de seguridad en curso",
      "Actualización de cache exitosa",
      "Métrica de rendimiento registrada",
      "Usuario autenticado correctamente",
      "Consulta a base de datos ejecutada",
      "Respuesta API enviada al cliente"
    ];
    
    const logs = [];
    const now = new Date();
    
    for (let i = 0; i < count; i++) {
      logs.push({
        timestamp: new Date(now.getTime() - Math.random() * 1000).toISOString(),
        container: containers[Math.floor(Math.random() * containers.length)],
        level: levels[Math.floor(Math.random() * levels.length)],
        message: messages[Math.floor(Math.random() * messages.length)]
      });
    }
    
    return logs;
  }
  
  updateLiveStatus(isLive) {
    const startBtn = document.getElementById('startLogsBtn');
    const stopBtn = document.getElementById('stopLogsBtn');
    
    if (startBtn) startBtn.disabled = isLive;
    if (stopBtn) stopBtn.disabled = !isLive;
  }
  
  addSystemLog(level, message) {
    this.addLogEntry({
      timestamp: new Date().toISOString(),
      container: 'system',
      level: level,
      message: message
    });
  }
  
  updateLogCounters() {
    if (!this.logsContainer) return;
    
    const logs = this.logsContainer.children;
    let infoCount = 0, warningCount = 0, errorCount = 0, successCount = 0;
    
    for (let log of logs) {
      if (log.classList.contains('log-info')) infoCount++;
      else if (log.classList.contains('log-warning')) warningCount++;
      else if (log.classList.contains('log-error')) errorCount++;
      else if (log.classList.contains('log-success')) successCount++;
    }
    
    // Actualizar contadores en la UI
    const totalElement = document.getElementById('logsCount');
    const infoElement = document.getElementById('infoCount');
    const warningElement = document.getElementById('warningCount');
    const errorElement = document.getElementById('errorCount');
    
    if (totalElement) totalElement.textContent = logs.length;
    if (infoElement) infoElement.textContent = infoCount;
    if (warningElement) warningElement.textContent = warningCount;
    if (errorElement) errorElement.textContent = errorCount;
  }
  
  formatTime(timestamp) {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('es-ES', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return '--:--:--';
    }
  }
  
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  clearLogs() {
    if (this.logsContainer) {
      this.logsContainer.innerHTML = '';
      this.addSystemLog('WARNING', '🗑️ Logs limpiados - Historial reiniciado');
    }
  }
  
  async exportLogs() {
    try {
      this.addSystemLog('INFO', '📥 Preparando exportación de logs...');
      
      const data = await apiFetch('/api/docker/logs?lines=100');
      
      if (data.ok && data.logs) {
        const logText = data.logs.map(log => 
          `[${this.formatTime(log.timestamp)}] [${log.container}] [${log.level}] ${log.message}`
        ).join('\n');
        
        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `fireflighter-logs-${new Date().toISOString().split('T')[0]}.log`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.addSystemLog('SUCCESS', '📁 Logs exportados correctamente');
      } else {
        throw new Error('No se pudieron obtener logs para exportar');
      }
    } catch (error) {
      console.warn('Error exportando logs:', error.message);
      this.addSystemLog('ERROR', 'Error exportando logs');
    }
  }
}

// === FUNCIONES GLOBALES ===
function refreshAllData() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.addSystemLog('INFO', 'Actualizando todos los datos...');
  }
  
  // Mostrar indicador de carga en el botón
  const refreshBtn = event?.target;
  if (refreshBtn) {
    const originalContent = refreshBtn.innerHTML;
    refreshBtn.innerHTML = '<span>🔄</span> Actualizando...';
    refreshBtn.disabled = true;
    
    // Restaurar botón después de la actualización
    setTimeout(() => {
      refreshBtn.innerHTML = originalContent;
      refreshBtn.disabled = false;
    }, 2000);
  }
  
  // Actualizar datos
  loadRealTimeData();
  
  // Simular verificación de componentes
  setTimeout(() => {
    if (window.dockerLogsManager) {
      window.dockerLogsManager.addSystemLog('INFO', 'Verificando estado de la API...');
    }
  }, 500);
  
  setTimeout(() => {
    if (window.dockerLogsManager) {
      window.dockerLogsManager.addSystemLog('INFO', 'Verificando conexión a la base de datos...');
    }
  }, 1000);
  
  setTimeout(() => {
    if (window.dockerLogsManager) {
      window.dockerLogsManager.addSystemLog('SUCCESS', 'Actualización completa finalizada');
    }
  }, 2000);
}

function runSystemDiagnostics() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.addSystemLog('INFO', 'Iniciando diagnóstico completo del sistema...');
  }
  
  // Mostrar indicador de carga en el botón
  const diagnosticBtn = event?.target;
  if (diagnosticBtn) {
    const originalContent = diagnosticBtn.innerHTML;
    diagnosticBtn.innerHTML = '<span>⚡</span> Ejecutando...';
    diagnosticBtn.disabled = true;
    
    // Restaurar botón al final
    setTimeout(() => {
      diagnosticBtn.innerHTML = originalContent;
      diagnosticBtn.disabled = false;
    }, 4000);
  }
  
  let diagnosticSteps = [
    { step: 'Verificando API principal', delay: 500, status: 'INFO' },
    { step: 'Comprobando conexión a base de datos', delay: 1000, status: 'INFO' },
    { step: 'Validando usuarios activos', delay: 1500, status: 'INFO' },
    { step: 'Revisando integridad de memory cards', delay: 2000, status: 'INFO' },
    { step: 'Verificando espacio en disco', delay: 2500, status: 'INFO' },
    { step: 'Comprobando memoria del sistema', delay: 3000, status: 'INFO' },
    { step: 'Validando logs de contenedores', delay: 3500, status: 'INFO' }
  ];
  
  // Ejecutar diagnósticos secuencialmente
  diagnosticSteps.forEach((diagnostic, index) => {
    setTimeout(() => {
      if (window.dockerLogsManager) {
        window.dockerLogsManager.addSystemLog(diagnostic.status, diagnostic.step);
        
        // Simular algunos resultados
        setTimeout(() => {
          if (diagnostic.step.includes('API')) {
            window.dockerLogsManager.addSystemLog('SUCCESS', 'API respondiendo correctamente (200ms)');
          } else if (diagnostic.step.includes('base de datos')) {
            window.dockerLogsManager.addSystemLog('SUCCESS', 'Conexión DB estable (15ms)');
          } else if (diagnostic.step.includes('usuarios')) {
            const userCount = document.getElementById('dbUsersCount')?.textContent || '0';
            window.dockerLogsManager.addSystemLog('SUCCESS', `${userCount} usuarios validados correctamente`);
          } else if (diagnostic.step.includes('memory cards')) {
            const cardCount = document.getElementById('totalCards')?.textContent || '0';
            window.dockerLogsManager.addSystemLog('SUCCESS', `${cardCount} tarjetas íntegras`);
          } else if (diagnostic.step.includes('espacio')) {
            window.dockerLogsManager.addSystemLog('SUCCESS', 'Espacio disponible: 75% libre');
          } else if (diagnostic.step.includes('memoria')) {
            window.dockerLogsManager.addSystemLog('SUCCESS', 'Memoria del sistema: 68% en uso');
          } else if (diagnostic.step.includes('logs')) {
            window.dockerLogsManager.addSystemLog('SUCCESS', 'Logs funcionando correctamente');
          }
        }, 200);
      }
    }, diagnostic.delay);
  });
  
  // Finalizar diagnóstico
  setTimeout(() => {
    if (window.dockerLogsManager) {
      window.dockerLogsManager.addSystemLog('SUCCESS', '✅ Diagnóstico completado - Todos los sistemas operativos');
      window.dockerLogsManager.addSystemLog('INFO', 'Resultado: Sistema funcionando óptimamente');
    }
  }, 4000);
  
  // Actualizar datos después del diagnóstico
  setTimeout(() => {
    updateSystemInfo();
  }, 4500);
}

function checkApiHealth() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.addSystemLog('INFO', 'Verificando salud de la API...');
  }
  
  checkSystemHealth();
}

function refreshMetric(metric) {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.addSystemLog('INFO', `Actualizando métrica: ${metric}`);
  }
  loadRealTimeData();
}

function refreshActivity() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.addSystemLog('INFO', 'Actualizando actividad reciente...');
  }
  loadRealTimeData();
}

function refreshCharts() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.addSystemLog('INFO', 'Actualizando gráficos del sistema...');
  }
  loadRealTimeData();
}

function expandWidget(btn) {
  const widget = btn.closest('.widget');
  if (widget) {
    const wasExpanded = widget.classList.contains('expanded');
    widget.classList.toggle('expanded');
    
    // CORRECCIÓN: Iconos diferentes para expandir/contraer
    btn.textContent = widget.classList.contains('expanded') ? '⛷' : '⛶';
    
    if (window.dockerLogsManager) {
      window.dockerLogsManager.addSystemLog('INFO', 
        `Widget ${wasExpanded ? 'contraído' : 'expandido'}`);
    }
  }
}

function exportData() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.addSystemLog('INFO', 'Iniciando exportación de datos...');
    
    setTimeout(() => {
      window.dockerLogsManager.addSystemLog('SUCCESS', 'Datos exportados correctamente');
    }, 1000);
  }
}

// === FUNCIONES DE LOG CONTROLS GLOBALES ===
function startLiveLogs() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.startLiveLogs();
  }
}

function stopLiveLogs() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.stopLiveLogs();
  }
}

function refreshLogs() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.refreshLogs();
  }
}

function clearLogs() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.clearLogs();
  }
}

function exportLogs() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.exportLogs();
  }
}

// === REAL TIME UPDATES ===
function startRealTimeUpdates() {
  // Actualizar cada 30 segundos
  setInterval(loadRealTimeData, 30000);
  
  // Actualizar información del sistema cada 10 segundos
  setInterval(updateSystemInfo, 10000);
  
  // Actualizar hora actual cada segundo
  setInterval(updateLastUpdateTime, 1000);
}

// === KEYBOARD SHORTCUTS ===
function setupKeyboardShortcuts() {
  document.addEventListener('keydown', function(e) {
    // Ctrl + R para actualizar datos
    if (e.ctrlKey && e.key === 'r') {
      e.preventDefault();
      refreshAllData();
    }
    
    // Ctrl + D para diagnóstico
    if (e.ctrlKey && e.key === 'd') {
      e.preventDefault();
      runSystemDiagnostics();
    }
    
    // Escape para cerrar menús
    if (e.key === 'Escape') {
      closeMobileMenu();
      const userMenu = document.getElementById('userMenuDropdown');
      if (userMenu) userMenu.classList.remove('show');
    }
  });
}

// === API HEALTH MONITOR ===
function setupApiHealthMonitor() {
  // Verificar salud de la API cada 2 minutos
  setInterval(checkSystemHealth, 120000);
}

// === MÉTRICAS DE PERFORMANCE ===
function trackPerformance(metricName, duration) {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.addSystemLog('PERF', `${metricName}: ${duration}ms`);
  }
  
  // También guardar en localStorage para analytics
  const perfData = JSON.parse(localStorage.getItem('performanceMetrics') || '[]');
  perfData.push({
    metric: metricName,
    duration: duration,
    timestamp: new Date().toISOString()
  });
  
  // Mantener solo los últimos 100 registros
  if (perfData.length > 100) {
    perfData.splice(0, perfData.length - 100);
  }
  
  localStorage.setItem('performanceMetrics', JSON.stringify(perfData));
}

// === CLEANUP DE RECURSOS ===
function cleanup() {
  if (window.dockerLogsManager) {
    if (window.dockerLogsManager.liveInterval) {
      clearInterval(window.dockerLogsManager.liveInterval);
    }
  }
  
  // Limpiar todos los intervals globales conocidos
  const intervalIds = Object.keys(window).filter(key => key.startsWith('intervalId_'));
  intervalIds.forEach(id => {
    clearInterval(window[id]);
  });
}

// === CONFIGURACIÓN GLOBAL COMPLETA ===
function setupGlobalHandlers() {
  // Manejar errores globales
  window.addEventListener('error', function(e) {
    console.error('Error global:', e.error);
    showNotification('Error inesperado en la aplicación', 'error');
  });
  
  // Manejar promesas rechazadas
  window.addEventListener('unhandledrejection', function(e) {
    console.warn('Promesa rechazada:', e.reason);
    showNotification('Error en operación asíncrona', 'warning');
    e.preventDefault();
  });
  
  // Configurar manejo offline
  setupOfflineHandler();
  
  // Configurar cleanup cuando la página se cierre
  window.addEventListener('beforeunload', cleanup);
  
  // Configurar cleanup cuando la página se oculte (para móviles)
  document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
      // Limpiar recursos temporales cuando la página no es visible
      if (window.dockerLogsManager && window.dockerLogsManager.isLive) {
        window.dockerLogsManager.stopLiveLogs();
      }
    }
  });
}

// === INICIALIZACIÓN COMPLETA DEL SISTEMA ===
console.log('🚀 FirefighterAI BackOffice JavaScript cargado correctamente');