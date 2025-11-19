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

  form?.addEventListener('submit', () => {
    btn.classList.add('loading');
    btn.setAttribute('disabled', 'disabled');
  });
})();