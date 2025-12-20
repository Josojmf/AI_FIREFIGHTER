(() => {
  const pass = document.getElementById('password');
  const toggle = document.getElementById('toggle-pass');
  const form = document.getElementById('login-form');
  const btn = document.getElementById('submit-login');

  toggle?.addEventListener('click', () => {
    const t = pass.type === 'password' ? 'text' : 'password';
    pass.type = t;
    toggle.textContent = t === 'password' ? '👁️' : '🙈';
  });

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();

    btn.classList.add('loading');
    btn.setAttribute('disabled', 'disabled');

    const formData = new FormData(form);
    const payload = {
      username: formData.get('username'),
      password: formData.get('password'),
      mfa_token: ''
    };

    try {
      const base = window.API_BASE_URL || 'http://backend:5000';
      const res = await fetch(`${base}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Credenciales incorrectas');
        return;
      }

      const data = await res.json();
      window.location.href = '/';
    } catch (err) {
      alert('Error de conexión con la API');
    } finally {
      btn.classList.remove('loading');
      btn.removeAttribute('disabled');
    }
  });
})();
