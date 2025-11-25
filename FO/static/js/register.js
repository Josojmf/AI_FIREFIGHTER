document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const form = document.getElementById('registerForm');
  const step1 = document.getElementById('step1');
  const step2 = document.getElementById('step2');
  const nextBtn = document.getElementById('nextStep');
  const prevBtn = document.getElementById('prevStep');
  const submitBtn = document.getElementById('submitForm');

  const progressSteps = document.querySelectorAll('.progress-step');
  const progressFill = document.getElementById('progressFill');

  const usernameInput = document.getElementById('username');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const confirmPasswordInput = document.getElementById('confirmPassword');
  const togglePassword = document.getElementById('togglePassword');

  const usernameValidation = document.getElementById('usernameValidation');
  const emailValidation = document.getElementById('emailValidation');
  const confirmValidation = document.getElementById('confirmValidation');

  const summaryUsername = document.getElementById('summaryUsername');
  const summaryEmail = document.getElementById('summaryEmail');

  const strengthFill = document.getElementById('strengthFill');
  const requirements = document.querySelectorAll('.requirement');

  let currentStep = 1;

  // Helpers
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function updateStep(step) {
    progressSteps.forEach((el, idx) => {
      if (idx + 1 <= step) el.classList.add('active'); else el.classList.remove('active');
    });
    progressFill.style.width = (step === 1 ? 0 : 100) + '%';

    if (step === 1) {
      step1.classList.add('active');
      step2.classList.remove('active');
    } else {
      step1.classList.remove('active');
      step2.classList.add('active');
      // Summary
      summaryUsername.textContent = usernameInput.value || '-';
      summaryEmail.textContent = emailInput.value || '-';
    }
    currentStep = step;
  }

// En register.js, añade esta función de validación para el token
function validateToken() {
    const tokenInput = document.getElementById('access_token');
    const tokenValue = tokenInput.value.trim();
    const nextButton = document.getElementById('nextStep');
    
    if (!tokenValue) {
        // Deshabilitar botón si el token está vacío
        nextButton.disabled = true;
        nextButton.style.opacity = '0.6';
        nextButton.style.cursor = 'not-allowed';
        return false;
    } else {
        // Habilitar botón si hay token
        nextButton.disabled = false;
        nextButton.style.opacity = '1';
        nextButton.style.cursor = 'pointer';
        return true;
    }
}

// Y añade este event listener al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    const tokenInput = document.getElementById('access_token');
    if (tokenInput) {
        tokenInput.addEventListener('input', validateToken);
        // Validar inicialmente
        validateToken();
    }
});

  function validateStep1() {
    const u = (usernameInput.value || '').trim();
    const e = (emailInput.value || '').trim();
    const p = passwordInput.value || '';
    const c = confirmPasswordInput.value || '';

    const userOk = /^[a-zA-Z0-9]{3,24}$/.test(u);
    const emailOk = emailRegex.test(e);
    const passOk = p.length >= 8 && /[A-Z]/.test(p) && /\d/.test(p) && /[!@#$%^&*(),.?":{}|<>]/.test(p);
    const confirmOk = c.length > 0 && c === p;

    return userOk && emailOk && passOk && confirmOk;
  }

  function updateNextButton() {
    if (nextBtn) nextBtn.disabled = !validateStep1();
  }

  // Password toggle
  if (togglePassword && passwordInput) {
    togglePassword.addEventListener('click', () => {
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);
      const icon = togglePassword.querySelector('.toggle-icon');
      if (icon) icon.textContent = (type === 'password') ? '👁️' : '🙈';
    });
  }

  // Username validation
  if (usernameInput) {
    usernameInput.addEventListener('input', () => {
      const v = usernameInput.value.trim();
      const ok = /^[a-zA-Z0-9]{3,24}$/.test(v);
      usernameInput.classList.toggle('valid', ok);
      usernameInput.classList.toggle('invalid', v.length > 0 && !ok);
      if (usernameValidation) {
        usernameValidation.textContent = v.length === 0 ? '' : (ok ? '✓' : '✗');
        usernameValidation.className = 'input-validation ' + (ok ? 'valid' : 'invalid');
        if (v.length === 0) usernameValidation.className = 'input-validation';
      }
      updateNextButton();
    });
  }

  // Email validation
  if (emailInput) {
    emailInput.addEventListener('input', () => {
      const v = emailInput.value.trim();
      const ok = emailRegex.test(v);
      emailInput.classList.toggle('valid', ok);
      emailInput.classList.toggle('invalid', v.length > 0 && !ok);
      if (emailValidation) {
        emailValidation.textContent = v.length === 0 ? '' : (ok ? '✓' : '✗');
        emailValidation.className = 'input-validation ' + (ok ? 'valid' : 'invalid');
        if (v.length === 0) emailValidation.className = 'input-validation';
      }
      updateNextButton();
    });
  }

  // Password strength
  if (passwordInput && strengthFill && requirements) {
    passwordInput.addEventListener('input', () => {
      const v = passwordInput.value;
      const checks = {
        length: v.length >= 8,
        uppercase: /[A-Z]/.test(v),
        number: /\d/.test(v),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(v)
      };
      let score = 0;
      requirements.forEach(req => {
        const k = req.getAttribute('data-req');
        const met = !!checks[k];
        req.classList.toggle('met', met);
        const icon = req.querySelector('.req-icon');
        if (icon) icon.textContent = met ? '●' : '○';
        score += met ? 1 : 0;
      });
      const pct = (score / 4) * 100;
      strengthFill.style.width = pct + '%';
      if (score === 4) {
        strengthFill.style.background = '#22c55e';
        passwordInput.classList.add('valid'); passwordInput.classList.remove('invalid');
      } else if (score >= 2) {
        strengthFill.style.background = '#f59e0b';
        passwordInput.classList.remove('valid','invalid');
      } else {
        strengthFill.style.background = '#ef4444';
        passwordInput.classList.add('invalid'); passwordInput.classList.remove('valid');
      }
      updateNextButton();
    });
  }

  // Confirm password
  if (confirmPasswordInput && confirmValidation && passwordInput) {
    confirmPasswordInput.addEventListener('input', () => {
      const ok = confirmPasswordInput.value.length > 0 && confirmPasswordInput.value === passwordInput.value;
      confirmPasswordInput.classList.toggle('valid', ok);
      confirmPasswordInput.classList.toggle('invalid', !ok && confirmPasswordInput.value.length > 0);
      confirmValidation.textContent = confirmPasswordInput.value.length === 0 ? '' : (ok ? '✓' : '✗');
      confirmValidation.className = 'input-validation ' + (ok ? 'valid' : 'invalid');
      if (confirmPasswordInput.value.length === 0) confirmValidation.className = 'input-validation';
      updateNextButton();
    });
  }

  // Next step
  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      if (validateStep1()) {
        updateStep(2);
      } else {
        // Shake invalids
        const invalids = document.querySelectorAll('.form-input.invalid, .form-input:not(.valid)');
        invalids.forEach(el => {
          el.style.animation = 'shake 0.5s ease-in-out';
          setTimeout(() => el.style.animation = '', 500);
        });
      }
    });
    updateNextButton();
  }

  // Previous step
  if (prevBtn) {
    prevBtn.addEventListener('click', () => updateStep(1));
  }

  // Terms enable/disable submit
  const termsCheckbox = document.querySelector('input[name="terms"]');
  if (termsCheckbox && submitBtn) {
    submitBtn.disabled = !termsCheckbox.checked;
    termsCheckbox.addEventListener('change', () => {
      submitBtn.disabled = !termsCheckbox.checked;
    });
  }

  // Submit loading state (deja que el form haga POST normal al backend)
  if (form && submitBtn) {
    form.addEventListener('submit', () => {
      const btnContent = submitBtn.querySelector('.btn-content');
      const btnLoading = document.getElementById('btnLoading');
      if (btnContent && btnLoading) {
        btnContent.style.display = 'none';
        btnLoading.style.display = 'flex';
        submitBtn.disabled = true;
      }
    });
  }

  // Notifs close + autohide
  document.querySelectorAll('.notification-close').forEach(btn => {
    btn.addEventListener('click', function(){
      const n = this.parentElement;
      n.style.opacity = '0';
      n.style.transform = 'translateX(100%)';
      setTimeout(() => n.remove(), 300);
    });
  });
  setTimeout(() => {
    document.querySelectorAll('.notification').forEach(n => {
      n.style.opacity = '0';
      n.style.transform = 'translateX(100%)';
      setTimeout(() => n.remove(), 300);
    });
  }, 5000);
});