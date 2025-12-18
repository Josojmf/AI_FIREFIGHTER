// login.js - Gestión completa del formulario de login
(function() {
    'use strict';
    
    const CONFIG = {
        minUsernameLength: 3,
        minPasswordLength: 4,
        submitTimeout: 5000
    };
    
    let isSubmitting = false;
    
    document.addEventListener("DOMContentLoaded", function() {
        initLoginForm();
        initFlashMessages();
        setupKeyboardShortcuts();
    });
    
    function initLoginForm() {
        const loginForm = document.querySelector(".login-form");
        if (!loginForm) return;
        
        const usernameInput = document.getElementById("username");
        const passwordInput = document.getElementById("password");
        const submitButton = loginForm.querySelector('button[type="submit"]');
        
        if (usernameInput) {
            usernameInput.addEventListener("input", function() {
                clearFieldError(usernameInput);
            });
        }
        
        if (passwordInput) {
            passwordInput.addEventListener("input", function() {
                clearFieldError(passwordInput);
            });
        }
        
        loginForm.addEventListener("submit", function(e) {
            if (!validateForm(usernameInput, passwordInput, submitButton)) {
                e.preventDefault();
                return false;
            }
            
            if (isSubmitting) {
                e.preventDefault();
                return false;
            }
            
            isSubmitting = true;
            showLoadingState(submitButton);
            
            setTimeout(() => {
                isSubmitting = false;
                hideLoadingState(submitButton);
            }, CONFIG.submitTimeout);
        });
    }
    
    function validateForm(usernameInput, passwordInput, submitButton) {
        let isValid = true;
        
        const username = usernameInput.value.trim();
        if (!username) {
            showFieldError(usernameInput, "El usuario es obligatorio");
            isValid = false;
        } else if (username.length < CONFIG.minUsernameLength) {
            showFieldError(usernameInput, `El usuario debe tener al menos ${CONFIG.minUsernameLength} caracteres`);
            isValid = false;
        }
        
        const password = passwordInput.value;
        if (!password) {
            showFieldError(passwordInput, "La contraseña es obligatoria");
            isValid = false;
        } else if (password.length < CONFIG.minPasswordLength) {
            showFieldError(passwordInput, `La contraseña debe tener al menos ${CONFIG.minPasswordLength} caracteres`);
            isValid = false;
        }
        
        if (!isValid) {
            showFlashMessage("Por favor, corrige los errores del formulario", "error");
            submitButton.focus();
        }
        
        return isValid;
    }
    
    function showFieldError(input, message) {
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;
        
        clearFieldError(input);
        
        formGroup.classList.add('has-error');
        input.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        errorDiv.style.color = '#ef4444';
        errorDiv.style.fontSize = '0.875rem';
        errorDiv.style.marginTop = '0.25rem';
        
        formGroup.appendChild(errorDiv);
        input.focus();
    }
    
    function clearFieldError(input) {
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;
        
        formGroup.classList.remove('has-error');
        input.classList.remove('is-invalid');
        
        const errorDiv = formGroup.querySelector('.field-error');
        if (errorDiv) errorDiv.remove();
    }
    
    function showLoadingState(button) {
        if (!button) return;
        
        button.disabled = true;
        button.classList.add('loading');
        
        const buttonText = button.querySelector('span:last-child');
        if (buttonText) {
            buttonText.dataset.originalText = buttonText.textContent;
            buttonText.textContent = 'Iniciando sesión...';
        }
    }
    
    function hideLoadingState(button) {
        if (!button) return;
        
        button.disabled = false;
        button.classList.remove('loading');
        
        const buttonText = button.querySelector('span:last-child');
        if (buttonText && buttonText.dataset.originalText) {
            buttonText.textContent = buttonText.dataset.originalText;
        }
    }
    
    function showFlashMessage(message, type = 'info') {
        const flashContainer = document.querySelector('.flash-messages');
        if (!flashContainer) return;
        
        const flashDiv = document.createElement('div');
        flashDiv.className = "flash " + type;
        flashDiv.textContent = message;
        
        flashContainer.appendChild(flashDiv);
        
        setTimeout(() => {
            flashDiv.remove();
        }, 4000);
    }
    
    function initFlashMessages() {
        const flashMessages = document.querySelectorAll('.flash-messages .flash');
        flashMessages.forEach(flash => {
            setTimeout(() => flash.remove(), 5000);
        });
    }
    
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                const form = document.querySelector('.login-form');
                if (form && !isSubmitting) {
                    form.reset();
                    document.querySelectorAll('.field-error').forEach(err => err.remove());
                    document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
                }
            }
        });
    }
    
})();
