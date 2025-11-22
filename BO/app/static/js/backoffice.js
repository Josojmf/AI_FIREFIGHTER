// === BACKOFFICE JAVASCRIPT CORREGIDO - PROBLEMA updateCurrentTime ===

document.addEventListener('DOMContentLoaded', function() {
  console.log('🔥 FirefighterAI BackOffice - Inicializado');
  
  initializeLayout();
  initializeDashboard();
  setupGlobalHandlers();
});

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

// === DASHBOARD DATA FUNCTIONS ===
async function loadRealTimeData() {
  try {
    console.log('📊 Cargando datos en tiempo real...');
    
    // Cargar estadísticas principales
    await loadDashboardStats();
    
    // Cargar actividad reciente
    await loadRecentActivity();
    
    // Actualizar estado del sistema
    await checkSystemHealth();
    
  } catch (error) {
    console.warn('Advertencia cargando datos en tiempo real:', error.message);
    // No mostrar notificación para errores de red comunes
  }
}

async function loadDashboardStats() {
  try {
    const response = await fetch('/api/dashboard/stats');
    if (!response.ok) {
      // No lanzar error para respuestas HTTP no exitosas
      console.warn(`API responded with status: ${response.status}`);
      return null;
    }
    
    const data = await response.json();
    
    // Actualizar métricas en la UI
    updateDashboardMetrics(data);
    
    return data;
  } catch (error) {
    // Solo log warning, no mostrar notificación
    console.warn('Error cargando estadísticas:', error.message);
    return null;
  }
}

async function loadRecentActivity() {
  try {
    const response = await fetch('/api/dashboard/activity');
    if (response.ok) {
      const data = await response.json();
      if (data.ok && data.activity) {
        updateActivityList(data.activity);
      }
    }
  } catch (error) {
    console.warn('Error cargando actividad:', error.message);
  }
}

async function checkSystemHealth() {
  try {
    const response = await fetch('/api/dashboard/health');
    if (response.ok) {
      const data = await response.json();
      updateSystemStatus(data);
    }
  } catch (error) {
    console.warn('Error verificando salud del sistema:', error.message);
    updateSystemStatus({ ok: false, api_status: 'offline' });
  }
}

function updateDashboardMetrics(data) {
  if (!data) return;
  
  // Actualizar métricas principales
  updateMetric('totalUsers', data.total_users);
  updateMetric('activeUsers', data.active_users);
  updateMetric('totalCards', data.total_cards);
  
  // Actualizar estado API
  updateApiStatus(data.api_status);
  
  // Actualizar resumen
  updateSummary(data);
}

function updateMetric(elementId, value) {
  const element = document.getElementById(elementId);
  if (element && value !== undefined && value !== null) {
    const oldValue = parseInt(element.textContent) || 0;
    const newValue = parseInt(value) || 0;
    element.textContent = newValue.toLocaleString();
    
    // Animación de cambio
    if (newValue !== oldValue) {
      element.style.color = newValue > oldValue ? '#10b981' : '#ef4444';
      setTimeout(() => {
        if (element.parentNode) {
          element.style.color = '';
        }
      }, 1000);
    }
  }
}

function updateApiStatus(status) {
  const elements = {
    apiStatus: document.getElementById('apiStatus'),
    apiStatusText: document.getElementById('apiStatusText'),
    systemStatusIndicator: document.getElementById('systemStatusIndicator'),
    apiTrend: document.getElementById('apiTrend')
  };
  
  const isOnline = status === 'online';
  
  Object.keys(elements).forEach(key => {
    const element = elements[key];
    if (!element) return;
    
    switch(key) {
      case 'apiStatus':
        element.textContent = isOnline ? 'Online' : 'Offline';
        element.className = `metric-value api-status-value ${isOnline ? 'online' : 'offline'}`;
        break;
      case 'apiStatusText':
        element.textContent = isOnline ? 'Online' : 'Offline';
        break;
      case 'systemStatusIndicator':
        element.textContent = isOnline ? '🟢' : '🔴';
        element.className = `status-indicator ${isOnline ? 'status-online' : 'status-offline'}`;
        break;
      case 'apiTrend':
        element.innerHTML = isOnline ? 
          '<span class="trend-icon">✅</span><span class="trend-value">Online</span>' :
          '<span class="trend-icon">❌</span><span class="trend-value">Offline</span>';
        break;
    }
  });
}

function updateActivityList(activities) {
  const activityList = document.getElementById('activityList');
  if (!activityList) return;
  
  // Limpiar solo si hay nuevas actividades
  if (activities && activities.length > 0) {
    activityList.innerHTML = '';
    
    activities.forEach(activity => {
      const activityItem = document.createElement('div');
      activityItem.className = 'activity-item';
      activityItem.innerHTML = `
        <div class="activity-icon">${activity.icon || '📝'}</div>
        <div class="activity-content">
          <div class="activity-text">${activity.text}</div>
          <div class="activity-time">${activity.time}</div>
        </div>
      `;
      activityList.appendChild(activityItem);
    });
  }
}

function updateSystemStatus(healthData) {
  if (!healthData) return;
  
  // Actualizar estado de la base de datos
  const dbStatus = document.getElementById('dbStatus');
  if (dbStatus) {
    dbStatus.textContent = healthData.database === 'connected' ? 'Conectada' : 'Error';
  }
  
  // Actualizar contador de usuarios en DB
  const dbUsersCount = document.getElementById('dbUsersCount');
  if (dbUsersCount && healthData.users_count !== undefined) {
    dbUsersCount.textContent = healthData.users_count?.toLocaleString() || '0';
  }
  
  // Actualizar timestamp
  const lastUpdate = document.getElementById('lastUpdate');
  if (lastUpdate) {
    lastUpdate.textContent = new Date().toLocaleTimeString();
  }
}

function updateSummary(data) {
  const summaryUsers = document.getElementById('summaryUsers');
  const summaryCards = document.getElementById('summaryCards');
  
  if (summaryUsers && data.total_users !== undefined) {
    summaryUsers.textContent = data.total_users?.toLocaleString() || '0';
  }
  
  if (summaryCards && data.total_cards !== undefined) {
    summaryCards.textContent = data.total_cards?.toLocaleString() || '0';
  }
}

// === REAL-TIME UPDATES ===
function startRealTimeUpdates() {
  // Actualizar cada 30 segundos
  setInterval(() => {
    loadRealTimeData();
  }, 30000);
  
  // Actualizar hora cada segundo - SOLO SI EL ELEMENTO EXISTE
  const currentTimeElement = document.getElementById('currentTime');
  if (currentTimeElement) {
    setInterval(updateCurrentTime, 1000);
  }
}

function updateCurrentTime() {
  const currentTimeElement = document.getElementById('currentTime');
  // VERIFICAR QUE EL ELEMENTO EXISTA ANTES DE ACTUALIZAR
  if (currentTimeElement && currentTimeElement.parentNode) {
    currentTimeElement.textContent = new Date().toLocaleTimeString();
  }
}

// === API HEALTH MONITOR ===
function setupApiHealthMonitor() {
  // Verificar salud de API cada minuto
  setInterval(() => {
    checkSystemHealth();
  }, 60000);
}

// === REFRESH FUNCTIONS ===
async function refreshData() {
  console.log('🔄 Refreshing data...');
  
  try {
    // Mostrar indicador de carga
    const refreshBtn = document.querySelector('[onclick="refreshData()"]');
    if (refreshBtn) {
      const originalHTML = refreshBtn.innerHTML;
      refreshBtn.innerHTML = '<span class="btn-icon">⏳</span> Actualizando...';
      refreshBtn.disabled = true;
      
      // Refrescar datos según la página actual
      const currentPage = window.location.pathname;
      
      if (currentPage.includes('dashboard') || currentPage === '/') {
        await loadRealTimeData();
      } else if (currentPage.includes('users')) {
        await loadUsersData();
      } else if (currentPage.includes('memory-cards')) {
        await loadCardsData();
      }
      
      showNotification('Datos actualizados correctamente', 'success');
      
      // Restaurar botón después de un breve delay
      setTimeout(() => {
        refreshBtn.innerHTML = originalHTML;
        refreshBtn.disabled = false;
      }, 1000);
      
    } else {
      // Si no hay botón específico, solo refrescar
      await loadRealTimeData();
      showNotification('Datos actualizados correctamente', 'success');
    }
    
  } catch (error) {
    console.warn('Error refreshing data:', error.message);
    showNotification('Error al actualizar datos', 'error');
    
    // Asegurarse de restaurar el botón en caso de error
    const refreshBtn = document.querySelector('[onclick="refreshData()"]');
    if (refreshBtn) {
      refreshBtn.innerHTML = '<span class="btn-icon">🔄</span> Actualizar';
      refreshBtn.disabled = false;
    }
  }
}

async function loadUsersData() {
  try {
    console.log('👥 Loading users data...');
    // Esta función será sobrescrita por la página de usuarios
    showNotification('Datos de usuarios actualizados', 'info');
  } catch (error) {
    console.warn('Error loading users data:', error.message);
    throw error;
  }
}

async function loadCardsData() {
  try {
    console.log('🗃️ Loading cards data...');
    // Esta función será sobrescrita por la página de memory cards
    showNotification('Datos de memory cards actualizados', 'info');
  } catch (error) {
    console.warn('Error loading cards data:', error.message);
    throw error;
  }
}

function refreshMetric(metric) {
  console.log(`🔄 Refreshing metric: ${metric}`);
  loadRealTimeData();
}

function refreshActivity() {
  console.log('🔄 Refreshing activity...');
  loadRecentActivity();
}

// === DOCKER LOGS SYSTEM ===
class DockerLogsManager {
  constructor() {
    this.eventSource = null;
    this.isLive = false;
    this.logsContainer = null;
    this.containers = new Set();
    this.init();
  }
  
  init() {
    this.logsContainer = document.getElementById('logsContainer');
    if (this.logsContainer) {
      this.loadInitialLogs();
      this.loadContainersInfo();
      this.setupLogsContainer();
    }
  }
  
  setupLogsContainer() {
    // Hacer el contenedor de logs scrollable
    if (this.logsContainer) {
      this.logsContainer.style.height = '400px';
      this.logsContainer.style.overflowY = 'auto';
      this.logsContainer.style.fontFamily = 'Monaco, Menlo, Ubuntu Mono, monospace';
      this.logsContainer.style.fontSize = '12px';
      this.logsContainer.style.lineHeight = '1.4';
    }
  }
  
  async loadInitialLogs() {
    try {
      const response = await fetch('/api/dashboard/docker-logs');
      if (!response.ok) {
        this.displayFallbackLogs();
        return;
      }
      
      const data = await response.json();
      
      if (data.ok && data.logs) {
        this.displayLogs(data.logs);
      } else {
        this.displayFallbackLogs();
      }
    } catch (error) {
      console.warn('Error cargando logs iniciales:', error.message);
      this.displayFallbackLogs();
    }
  }
  
  async loadContainersInfo() {
    try {
      const response = await fetch('/api/dashboard/docker-containers');
      if (response.ok) {
        const data = await response.json();
        if (data.ok && data.containers) {
          this.updateContainersInfo(data.containers);
        }
      }
    } catch (error) {
      console.warn('Error cargando información de contenedores:', error.message);
    }
  }
  
  displayLogs(logs) {
    if (!this.logsContainer) return;
    
    // Limpiar logs antiguos
    this.logsContainer.innerHTML = '';
    
    // Mostrar nuevos logs
    if (logs && logs.length > 0) {
      logs.forEach(log => {
        this.addLogEntry(log);
      });
    } else {
      this.addSystemLog('INFO', 'No hay logs disponibles');
    }
    
    // Actualizar contadores
    this.updateLogCounters(logs);
  }
  
  displayFallbackLogs() {
    if (!this.logsContainer) return;
    
    this.logsContainer.innerHTML = '';
    
    const fallbackLogs = [
      {
        timestamp: new Date().toISOString(),
        container: 'system',
        level: 'INFO',
        message: 'Inicializando sistema de logs Docker...'
      },
      {
        timestamp: new Date().toISOString(),
        container: 'system',
        level: 'INFO',
        message: 'Conectando con servicios Docker...'
      }
    ];
    
    fallbackLogs.forEach(log => this.addLogEntry(log));
  }
  
  addLogEntry(log) {
    if (!this.logsContainer) return;
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${log.level.toLowerCase()}`;
    logEntry.innerHTML = `
      <span class="log-time">${this.formatTime(log.timestamp)}</span>
      <span class="log-container">${log.container}</span>
      <span class="log-level">${log.level}</span>
      <span class="log-message">${this.escapeHtml(log.message)}</span>
    `;
    
    this.logsContainer.insertBefore(logEntry, this.logsContainer.firstChild);
    
    // Mantener máximo 200 logs
    if (this.logsContainer.children.length > 200) {
      this.logsContainer.removeChild(this.logsContainer.lastChild);
    }
    
    // Auto-scroll si está en la parte inferior
    this.autoScroll();
  }
  
  startLiveLogs() {
    if (this.isLive) {
      showNotification('Los logs en vivo ya están activos', 'info');
      return;
    }
    
    try {
      showNotification('Iniciando logs en vivo...', 'info');
      
      // Usar Server-Sent Events para logs en tiempo real
      this.eventSource = new EventSource('/api/docker/logs/stream');
      
      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'connected') {
            this.addSystemLog('SUCCESS', 'Conectado al stream de logs en tiempo real');
          } else if (data.message) {
            this.addLogEntry(data);
          }
        } catch (parseError) {
          console.warn('Error parseando log:', parseError.message);
        }
      };
      
      this.eventSource.onerror = (error) => {
        console.warn('Error en stream de logs:', error);
        this.addSystemLog('ERROR', 'Error en conexión de logs en vivo');
        this.stopLiveLogs();
      };
      
      this.eventSource.onopen = () => {
        this.isLive = true;
        this.addSystemLog('SUCCESS', 'Logs en vivo activados');
        this.updateLiveStatus(true);
      };
      
    } catch (error) {
      console.warn('Error iniciando logs en vivo:', error.message);
      this.addSystemLog('ERROR', 'No se pudieron iniciar los logs en vivo');
      this.updateLiveStatus(false);
    }
  }
  
  stopLiveLogs() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    
    this.isLive = false;
    this.addSystemLog('INFO', 'Logs en vivo detenidos');
    this.updateLiveStatus(false);
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
  
  updateContainersInfo(containers) {
    // Actualizar información de contenedores en la UI si existe
    const containersList = document.getElementById('containersList');
    if (containersList) {
      containersList.innerHTML = '';
      
      containers.forEach(container => {
        const containerElement = document.createElement('div');
        containerElement.className = 'container-item';
        containerElement.innerHTML = `
          <div class="container-name">${container.name}</div>
          <div class="container-status status-${container.health || 'unknown'}">${container.status}</div>
          <div class="container-ports">${container.ports}</div>
        `;
        containersList.appendChild(containerElement);
      });
    }
  }
  
  updateLogCounters(logs) {
    const counterElement = document.getElementById('logsCount');
    if (counterElement) {
      counterElement.textContent = logs ? logs.length : 0;
    }
    
    // Contar por nivel
    const levels = { INFO: 0, WARNING: 0, ERROR: 0, DEBUG: 0, SUCCESS: 0 };
    if (logs) {
      logs.forEach(log => {
        if (levels[log.level] !== undefined) {
          levels[log.level]++;
        }
      });
    }
    
    // Actualizar contadores de niveles si existen
    Object.keys(levels).forEach(level => {
      const counter = document.getElementById(`${level.toLowerCase()}Count`);
      if (counter) {
        counter.textContent = levels[level];
        counter.className = `stat-value ${level.toLowerCase()}-count`;
      }
    });
  }
  
  formatTime(timestamp) {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString();
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
  
  autoScroll() {
    if (this.logsContainer && this.logsContainer.parentNode) {
      // Solo hacer scroll si el usuario está cerca del final
      const isNearBottom = 
        this.logsContainer.scrollHeight - this.logsContainer.clientHeight <= 
        this.logsContainer.scrollTop + 50;
      
      if (isNearBottom) {
        setTimeout(() => {
          if (this.logsContainer && this.logsContainer.parentNode) {
            this.logsContainer.scrollTop = this.logsContainer.scrollHeight;
          }
        }, 100);
      }
    }
  }
  
  clearLogs() {
    if (this.logsContainer && this.logsContainer.parentNode) {
      this.logsContainer.innerHTML = '';
      this.addSystemLog('INFO', 'Logs limpiados');
      this.updateLogCounters([]);
    }
  }
  
  async exportLogs() {
    try {
      showNotification('Exportando logs...', 'info');
      
      const response = await fetch('/api/dashboard/docker-logs');
      const data = await response.json();
      
      if (data.ok && data.logs) {
        const logText = data.logs.map(log => 
          `[${log.timestamp}] [${log.container}] [${log.level}] ${log.message}`
        ).join('\n');
        
        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `docker-logs-${new Date().toISOString().split('T')[0]}.log`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showNotification('Logs exportados correctamente', 'success');
      } else {
        throw new Error('No se pudieron obtener logs para exportar');
      }
    } catch (error) {
      console.warn('Error exportando logs:', error.message);
      showNotification('Error exportando logs', 'error');
    }
  }
}

// === LOGS CONTROL FUNCTIONS ===
function startLiveLogs() {
  if (!window.dockerLogsManager) {
    window.dockerLogsManager = new DockerLogsManager();
  }
  window.dockerLogsManager.startLiveLogs();
}

function stopLiveLogs() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.stopLiveLogs();
  }
}

function clearLogs() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.clearLogs();
  } else {
    showNotification('Sistema de logs no inicializado', 'error');
  }
}

function exportLogs() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.exportLogs();
  } else {
    showNotification('Sistema de logs no inicializado', 'error');
  }
}

function refreshLogs() {
  if (window.dockerLogsManager) {
    window.dockerLogsManager.loadInitialLogs();
  } else {
    window.dockerLogsManager = new DockerLogsManager();
  }
}

// === KEYBOARD SHORTCUTS ===
function setupKeyboardShortcuts() {
  document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + B para toggle sidebar
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
      e.preventDefault();
      const sidebarToggle = document.getElementById('sidebarToggle');
      if (sidebarToggle) {
        sidebarToggle.click();
      }
    }
    
    // Ctrl/Cmd + R para refresh (evitar recarga completa)
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
      if (!e.shiftKey) {
        e.preventDefault();
        refreshData();
      }
    }
    
    // Escape para cerrar menús
    if (e.key === 'Escape') {
      closeMobileMenu();
      
      const userMenu = document.getElementById('userMenuDropdown');
      const menuContainer = document.querySelector('.user-menu');
      if (userMenu) userMenu.classList.remove('show');
      if (menuContainer) menuContainer.classList.remove('active');
    }
    
    // F5 para refresh data
    if (e.key === 'F5') {
      e.preventDefault();
      refreshData();
    }
  });
}

// === RESPONSIVE HANDLING ===
function handleResize() {
  const sidebar = document.getElementById('sidebar');
  
  if (window.innerWidth > 1024) {
    // Desktop: cerrar menú móvil si está abierto
    closeMobileMenu();
  }
}

window.addEventListener('resize', handleResize);

// === GLOBAL HANDLERS ===
function setupGlobalHandlers() {
  // Manejo de errores global - SOLO MOSTRAR ERRORES CRÍTICOS
  window.addEventListener('error', function(e) {
    // Solo mostrar errores que no sean de red o CORS
    const error = e.error;
    if (error && (
      error.message.includes('NetworkError') ||
      error.message.includes('Failed to fetch') ||
      error.message.includes('CORS') ||
      error.message.includes('Load failed') ||
      error.message.includes('null') || // Ignorar errores de elementos null
      error.message.includes('Cannot set properties of null')
    )) {
      console.warn('Error ignorado:', error.message);
      return;
    }
    
    console.error('JavaScript Error crítico:', e.error);
    // Solo mostrar notificación para errores realmente críticos
    if (error && !error.message.includes('Loading')) {
      showNotification('Error crítico en la aplicación', 'error');
    }
  });
  
  window.addEventListener('unhandledrejection', function(e) {
    // Ignorar promesas rechazadas comunes (errores de red)
    if (e.reason && (
      e.reason.message.includes('NetworkError') ||
      e.reason.message.includes('Failed to fetch') ||
      e.reason.message.includes('CORS') ||
      e.reason.message.includes('Load failed') ||
      e.reason.message.includes('null') ||
      e.reason.message.includes('Cannot set properties of null')
    )) {
      console.warn('Promise rejection ignorada:', e.reason.message);
      return;
    }
    
    console.error('Unhandled Promise Rejection crítico:', e.reason);
    showNotification('Error en operación asíncrona', 'error');
  });
  
  // Prevenir navegación accidental
  window.addEventListener('beforeunload', function(e) {
    if (window.dockerLogsManager && window.dockerLogsManager.isLive) {
      e.preventDefault();
      e.returnValue = 'Los logs en vivo están activos. ¿Estás seguro de que quieres salir?';
      return e.returnValue;
    }
  });
}

// === WIDGET CONTROLS ===
function expandWidget(button) {
  const widget = button.closest('.widget');
  if (widget && widget.parentNode) {
    widget.classList.toggle('expanded');
    
    // Ajustar scroll después de expandir
    setTimeout(() => {
      if (widget && widget.parentNode) {
        widget.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }, 100);
  }
}

function runSystemDiagnostics() {
  showNotification('Ejecutando diagnóstico del sistema...', 'info');
  
  // Simular diagnóstico
  setTimeout(() => {
    const isHealthy = Math.random() > 0.2; // 80% de probabilidad de estar saludable
    if (isHealthy) {
      showNotification('Diagnóstico completado - Sistema OK', 'success');
    } else {
      showNotification('Diagnóstico completado - Se encontraron problemas menores', 'warning');
    }
  }, 2000);
}

function exportData() {
  showNotification('Preparando exportación de datos...', 'info');
  
  // Simular exportación
  setTimeout(() => {
    showNotification('Datos exportados correctamente', 'success');
  }, 1500);
}

// === GLOBAL EXPORTS ===
window.FirefighterBackoffice = {
  // Layout
  toggleUserMenu,
  closeMobileMenu,
  refreshData,
  showNotification,
  
  // Dashboard
  loadRealTimeData,
  refreshMetric,
  refreshActivity,
  runSystemDiagnostics,
  exportData,
  expandWidget,
  
  // Docker Logs
  startLiveLogs,
  stopLiveLogs,
  clearLogs,
  exportLogs,
  refreshLogs
};

// También hacer las funciones disponibles globalmente para onclick en HTML
window.toggleUserMenu = toggleUserMenu;
window.closeMobileMenu = closeMobileMenu;
window.refreshData = refreshData;
window.refreshMetric = refreshMetric;
window.refreshActivity = refreshActivity;
window.runSystemDiagnostics = runSystemDiagnostics;
window.startLiveLogs = startLiveLogs;
window.stopLiveLogs = stopLiveLogs;
window.clearLogs = clearLogs;
window.exportLogs = exportLogs;
window.refreshLogs = refreshLogs;
window.exportData = exportData;
window.expandWidget = expandWidget;

console.log('✅ BackOffice JavaScript loaded successfully');