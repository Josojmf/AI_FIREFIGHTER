// === LAYOUT.JS - Funcionalidad base del layout ===

document.addEventListener('DOMContentLoaded', function() {
  console.log('🔥 FirefighterAI BackOffice Layout - Initialized');
  
  initializeSidebar();
  initializeMobileMenu();
  initializeUserMenu();
  initializeFlashMessages();
  setupKeyboardShortcuts();
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
}

// === USER MENU ===
function initializeUserMenu() {
  // Cerrar dropdowns al hacer click fuera
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.user-menu')) {
      const userMenu = document.getElementById('userMenuDropdown');
      const menuContainer = document.querySelector('.user-menu');
      
      if (userMenu && menuContainer) {
        userMenu.classList.remove('show');
        menuContainer.classList.remove('active');
      }
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
  // Auto-hide flash messages después de 5 segundos
  const flashMessages = document.querySelectorAll('[data-flash]');
  flashMessages.forEach(flash => {
    setTimeout(() => {
      flash.style.opacity = '0';
      flash.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (flash.parentNode) {
          flash.remove();
        }
      }, 300);
    }, 5000);
  });
}

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
  
  // Insertar al inicio de flash-messages o page-content
  let container = document.querySelector('.flash-messages');
  if (!container) {
    container = document.createElement('div');
    container.className = 'flash-messages';
    const pageContent = document.querySelector('.page-content');
    if (pageContent) {
      pageContent.insertBefore(container, pageContent.firstChild);
    }
  }
  
  if (container) {
    container.insertBefore(notification, container.firstChild);
    
    // Auto-remove después de 5 segundos
    setTimeout(() => {
      notification.style.opacity = '0';
      notification.style.transform = 'translateX(100%)';
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove();
        }
      }, 300);
    }, 5000);
  }
}

// === UTILIDADES ===
function refreshData() {
  console.log('🔄 Refreshing data...');
  
  // Mostrar indicador de carga
  const refreshBtn = document.querySelector('[onclick="refreshData()"]');
  if (refreshBtn) {
    const icon = refreshBtn.querySelector('.btn-icon');
    if (icon) {
      icon.textContent = '⏳';
      refreshBtn.disabled = true;
    }
  }
  
  // Simular refresh (cada página puede sobrescribir esta función)
  setTimeout(() => {
    showNotification('Datos actualizados', 'success');
    
    // Restaurar botón
    if (refreshBtn) {
      const icon = refreshBtn.querySelector('.btn-icon');
      if (icon) {
        icon.textContent = '🔄';
        refreshBtn.disabled = false;
      }
    }
  }, 1000);
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
    
    // Escape para cerrar menús
    if (e.key === 'Escape') {
      closeMobileMenu();
      
      const userMenu = document.getElementById('userMenuDropdown');
      const menuContainer = document.querySelector('.user-menu');
      if (userMenu && menuContainer) {
        userMenu.classList.remove('show');
        menuContainer.classList.remove('active');
      }
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

// === ERROR HANDLING ===
window.addEventListener('error', function(e) {
  console.error('Layout JavaScript Error:', e.error);
});

window.addEventListener('unhandledrejection', function(e) {
  console.error('Layout Promise Rejection:', e.reason);
});

// === FUNCIONES GLOBALES PARA USAR EN TEMPLATES ===
window.FirefighterLayout = {
  toggleUserMenu,
  closeMobileMenu,
  showNotification,
  refreshData
};

// También hacer las funciones disponibles globalmente para onclick en HTML
window.toggleUserMenu = toggleUserMenu;
window.closeMobileMenu = closeMobileMenu;
window.refreshData = refreshData;

console.log('✅ Layout JavaScript loaded successfully');