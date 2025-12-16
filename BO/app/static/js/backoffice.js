// backoffice.js (UI-only) — SAFE & CLEAN VERSION

document.addEventListener('DOMContentLoaded', function () {
  initializeLayout();
  setupGlobalHandlers();

  // 🔥 SOLO inicializar dashboard si existe
  if (document.querySelector('.dashboard')) {
    initializeDashboard();
  }
});

// ================= CONFIG =================

// API base inyectada desde HTML (Jinja)
const API_BASE_URL =
  document.body.dataset.apiBaseUrl ||
  window.API_BASE_URL ||
  '';

// ================= API =================

async function apiFetch(endpoint, options = {}) {
  if (!API_BASE_URL) {
    console.error('❌ API_BASE_URL no definido');
    throw new Error('API_BASE_URL no definido');
  }

  const url = `${API_BASE_URL}${endpoint}`;
  console.log('📡 API:', url);

  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      ...options,
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    return await res.json();
  } catch (err) {
    console.error('❌ API ERROR:', err);
    showNotification('Error conectando con la API', 'error');
    throw err;
  }
}

// ================= DASHBOARD =================

function initializeDashboard() {
  console.log('📊 Dashboard init');
  loadDashboard();
}

async function loadDashboard() {
  try {
    const stats = await apiFetch('/api/dashboard/stats');
    updateStats(stats);

    const system = await apiFetch('/api/dashboard/system-info');
    updateSystem(system);

    const health = await apiFetch('/api/dashboard/health');
    updateHealth(health);
  } catch (e) {
    console.warn('⚠️ Dashboard fallback');
    showFallback();
  }
}

function updateStats(data) {
  setText('totalUsers', data.total_users);
  setText('activeUsers', data.active_users);
  setText('totalCards', data.total_cards);
}

function updateSystem(data) {
  setText('dbUsersCount', data.db_users_count);
  setText(
    'dbStatus',
    data.db_status === 'connected' ? 'Conectada' : 'Desconectada'
  );
}

function updateHealth(data) {
  setText('apiStatusText', data.ok ? 'Online' : 'Offline');
}

function showFallback() {
  setText('apiStatusText', 'Offline');
}

// ================= HELPERS =================

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value ?? '-';
}

// ================= UI =================

function initializeLayout() {
  initializeSidebar();
  initializeMobileMenu();
  initializeUserMenu();
  initializeFlashMessages();
  setupKeyboardShortcuts();
  setupOfflineHandler();
}

function initializeSidebar() {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');

  if (!toggle || !sidebar) return;

  toggle.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    localStorage.setItem(
      'sidebarCollapsed',
      sidebar.classList.contains('collapsed')
    );
  });

  if (localStorage.getItem('sidebarCollapsed') === 'true') {
    sidebar.classList.add('collapsed');
  }
}

function initializeMobileMenu() {
  const toggle = document.getElementById('mobileMenuToggle');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('mobileOverlay');

  if (!toggle || !sidebar) return;

  toggle.addEventListener('click', () => {
    sidebar.classList.add('mobile-open');
    overlay?.classList.add('active');
    document.body.style.overflow = 'hidden';
  });
}

function closeMobileMenu() {
  document.getElementById('sidebar')?.classList.remove('mobile-open');
  document.getElementById('mobileOverlay')?.classList.remove('active');
  document.body.style.overflow = '';
}

function initializeUserMenu() {
  const toggle = document.querySelector('.user-menu-toggle');
  if (!toggle) return;

  toggle.addEventListener('click', () => {
    document.getElementById('userMenuDropdown')?.classList.toggle('show');
  });
}

function initializeFlashMessages() {
  document.querySelectorAll('[data-flash]').forEach((f) =>
    setTimeout(() => f.remove(), 5000)
  );
}

function showNotification(message, type = 'info') {
  const el = document.createElement('div');
  el.className = `flash flash-${type}`;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function setupKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeMobileMenu();
  });
}

function setupOfflineHandler() {
  window.addEventListener('offline', () =>
    showNotification('Sin conexión', 'warning')
  );
  window.addEventListener('online', () =>
    showNotification('Conexión restaurada', 'success')
  );
}

function setupGlobalHandlers() {
  window.addEventListener('error', () =>
    showNotification('Error inesperado', 'error')
  );
}
