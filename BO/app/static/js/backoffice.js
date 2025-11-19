// === BACKOFFICE JAVASCRIPT ===
document.addEventListener('DOMContentLoaded', function() {
  console.log('🔥 FirefighterAI BackOffice iniciado');
  
  initializeSidebar();
  initializeNotifications();
  initializeUserMenu();
  initializeFlashMessages();
  initializeMobileMenu();
  loadDashboardData();
});

// === SIDEBAR FUNCTIONALITY ===
function initializeSidebar() {
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  
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
    });
  }
}

function closeMobileMenu() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('mobileOverlay');
  
  if (sidebar) sidebar.classList.remove('mobile-open');
  if (overlay) overlay.classList.remove('active');
}

// === NOTIFICATIONS ===
function initializeNotifications() {
  // Auto-hide flash messages after 5 seconds
  const flashMessages = document.querySelectorAll('[data-flash]');
  flashMessages.forEach(flash => {
    setTimeout(() => {
      flash.style.opacity = '0';
      flash.style.transform = 'translateX(100%)';
      setTimeout(() => flash.remove(), 300);
    }, 5000);
  });
}

function toggleNotifications() {
  const panel = document.getElementById('notificationPanel');
  if (panel) {
    panel.classList.toggle('show');
    console.log('Notifications toggled');
  }
}

function markAllRead() {
  console.log('Marking all notifications as read');
  // TODO: Implementar cuando tengamos API de notificaciones
}

// === USER MENU ===
function initializeUserMenu() {
  // Cerrar dropdowns al hacer click fuera
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.notification-dropdown')) {
      const notificationPanel = document.getElementById('notificationPanel');
      if (notificationPanel) notificationPanel.classList.remove('show');
    }
    
    if (!e.target.closest('.user-menu')) {
      const userMenu = document.getElementById('userMenuDropdown');
      if (userMenu) userMenu.classList.remove('show');
    }
  });
}

function toggleUserMenu() {
  const dropdown = document.getElementById('userMenuDropdown');
  const menu = dropdown?.closest('.user-menu');
  
  if (dropdown && menu) {
    dropdown.classList.toggle('show');
    menu.classList.toggle('active');
    console.log('User menu toggled');
  }
}

// === FLASH MESSAGES ===
function initializeFlashMessages() {
  // Las flash messages ya se inicializan en initializeNotifications
  console.log('Flash messages initialized');
}

// === API FUNCTIONS ===
async function refreshData() {
  console.log('🔄 Refreshing data...');
  
  try {
    // Mostrar indicador de carga
    const refreshBtn = document.querySelector('[onclick="refreshData()"]');
    if (refreshBtn) {
      refreshBtn.innerHTML = '<span class="btn-icon">⏳</span>';
      refreshBtn.disabled = true;
    }
    
    // Refrescar datos específicos de la página actual
    const currentPage = window.location.pathname;
    
    if (currentPage.includes('dashboard')) {
      await loadDashboardData();
    } else if (currentPage.includes('users')) {
      await loadUsersData();
    }
    
    showNotification('Datos actualizados', 'success');
    
  } catch (error) {
    console.error('Error refreshing data:', error);
    showNotification('Error al actualizar datos', 'error');
  } finally {
    // Restaurar botón
    const refreshBtn = document.querySelector('[onclick="refreshData()"] .btn-icon');
    if (refreshBtn) {
      refreshBtn.textContent = '🔄';
      refreshBtn.parentElement.disabled = false;
    }
  }
}

async function loadDashboardData() {
  try {
    console.log('📊 Loading dashboard data...');
    
    // Aquí harías las llamadas a la API
    // const response = await fetch('/api/dashboard/stats');
    // const data = await response.json();
    
    // Por ahora simulamos datos
    updateApiStatus();
    
  } catch (error) {
    console.error('Error loading dashboard data:', error);
  }
}

async function loadUsersData() {
  try {
    console.log('👥 Loading users data...');
    // TODO: Implementar cuando tengamos la página de usuarios
  } catch (error) {
    console.error('Error loading users data:', error);
  }
}

// === API STATUS ===
function updateApiStatus() {
  const indicator = document.getElementById('apiStatusIndicator');
  if (!indicator) return;
  
  // Simular check de API
  fetch('/api/health')
    .then(response => response.json())
    .then(data => {
      const statusDot = indicator.querySelector('.status-dot');
      if (statusDot) {
        statusDot.className = 'status-dot status-online';
        console.log('✅ API Status: Online');
      }
    })
    .catch(() => {
      const statusDot = indicator.querySelector('.status-dot');
      if (statusDot) {
        statusDot.className = 'status-dot status-offline';
        console.log('❌ API Status: Offline');
      }
    });
}

function showApiStatus() {
  updateApiStatus();
  showNotification('Estado de API actualizado', 'info');
}

// === UTILITIES ===
function showNotification(message, type = 'info') {
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
  
  // Insertar al inicio del contenido
  const flashContainer = document.querySelector('.flash-messages') || 
                        document.querySelector('.page-content');
  
  if (flashContainer) {
    flashContainer.insertBefore(notification, flashContainer.firstChild);
    
    // Auto-remove después de 5 segundos
    setTimeout(() => {
      notification.style.opacity = '0';
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => notification.remove(), 300);
    }, 5000);
  }
}

function toggleTheme() {
  console.log('🌙 Theme toggle - TODO: Implementar');
  showNotification('Función de tema en desarrollo', 'info');
}

// === KEYBOARD SHORTCUTS ===
document.addEventListener('keydown', function(e) {
  // Ctrl/Cmd + K para búsqueda rápida
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    console.log('Quick search shortcut');
    showNotification('Búsqueda rápida en desarrollo', 'info');
  }
  
  // Ctrl/Cmd + B para toggle sidebar
  if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
    e.preventDefault();
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) sidebarToggle.click();
  }
});

// === PERIODIC TASKS ===
setInterval(() => {
  updateApiStatus();
}, 30000); // Cada 30 segundos

// === ERROR HANDLING ===
window.addEventListener('error', function(e) {
  console.error('JavaScript Error:', e.error);
});

window.addEventListener('unhandledrejection', function(e) {
  console.error('Unhandled Promise Rejection:', e.reason);
});

// === EXPORT FUNCTIONS FOR GLOBAL ACCESS ===
window.FirefighterBackoffice = {
  refreshData,
  toggleNotifications,
  toggleUserMenu,
  showApiStatus,
  toggleTheme,
  showNotification,
  closeMobileMenu,
  markAllRead
};