// login.js - Gestión completa del formulario de login
(function() {
    'use strict';
    
    // Configuración
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
    
    /**
     * Inicializar formulario de login
     */
    function initLoginForm() {
        const loginForm = document.querySelector(".login-form");
        if (!loginForm) return;
        
        const usernameInput = document.getElementById("username");
        const passwordInput = document.getElementById("password");
        const submitButton = loginForm.querySelector('button[type="submit"]');
        
        // Validación en tiempo real
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
        
        // Manejar submit
        loginForm.addEventListener("submit", function(e) {
            if (!validateForm(usernameInput, passwordInput, submitButton)) {
                e.preventDefault();
                return false;
            }
            
            // Prevenir doble submit
            if (isSubmitting) {
                e.preventDefault();
                return false;
            }
            
            isSubmitting = true;
            showLoadingState(submitButton);
            
            // Reset después de timeout (por si falla el servidor)
            setTimeout(() => {
                isSubmitting = false;
                hideLoadingState(submitButton);
            }, CONFIG.submitTimeout);
        });
    }
    
    /**
     * Validar formulario antes de enviar
     */
    function validateForm(usernameInput, passwordInput, submitButton) {
        let isValid = true;
        
        // Validar username
        const username = usernameInput.value.trim();
        if (!username) {
            showFieldError(usernameInput, "El usuario es obligatorio");
            isValid = false;
        } else if (username.length < CONFIG.minUsernameLength) {
            showFieldError(usernameInput, `El usuario debe tener al menos ${CONFIG.minUsernameLength} caracteres`);
            isValid = false;
        }
        
        // Validar password
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
    
    /**
     * Mostrar error en campo específico
     */
    function showFieldError(input, message) {
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;
        
        // Remover error previo
        clearFieldError(input);
        
        // Añadir clase de error
        formGroup.classList.add('has-error');
        input.classList.add('is-invalid');
        
        // Crear mensaje de error
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        errorDiv.style.color = '#ef4444';
        errorDiv.style.fontSize = '0.875rem';
        errorDiv.style.marginTop = '0.25rem';
        
        formGroup.appendChild(errorDiv);
        
        // Focus en el campo con error
        input.focus();
    }
    
    /**
     * Limpiar error de campo
     */
    function clearFieldError(input) {
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;
        
        formGroup.classList.remove('has-error');
        input.classList.remove('is-invalid');
        
        const errorDiv = formGroup.querySelector('.field-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
    
    /**
     * Mostrar estado de carga en botón
     */
    function showLoadingState(button) {
        if (!button) return;
        
        button.disabled = true;
        button.classList.add('loading');
        
        const buttonText = button.querySelector('span:last-child');
        if (buttonText) {
            buttonText.dataset.originalText = buttonText.textContent;
            buttonText.textContent = 'Iniciando sesión...';
        }
        
        // Añadir spinner si existe el icono
        const btnIcon = button.querySelector('.btn-icon');
        if (btnIcon) {
            btnIcon.style.animation = 'spin 1s linear infinite';
        }
    }
    
    /**
     * Ocultar estado de carga
     */
    function hideLoadingState(button) {
        if (!button) return;
        
        button.disabled = false;
        button.classList.remove('loading');
        
        const buttonText = button.querySelector('span:last-child');
        if (buttonText && buttonText.dataset.originalText) {
            buttonText.textContent = buttonText.dataset.originalText;
        }
        
        const btnIcon = button.querySelector('.btn-icon');
        if (btnIcon) {
            btnIcon.style.animation = '';
        }
    }
    
    /**
     * Mostrar mensaje flash
     */
    function showFlashMessage(message, type = 'info') {
        const flashContainer = document.querySelector('.flash-messages');
        if (!flashContainer) return;
        
        const flashDiv = document.createElement('div');
        flashDiv.className = `flash ${type}`;
        flashDiv.textContent = message;
        flashDiv.style.animation = 'slideInDown 0.3s ease-out';
        
        flashContainer.appendChild(flashDiv);
        
        // Auto-remover después de 4 segundos
        setTimeout(() => {
            flashDiv.style.animation = 'slideOutUp 0.3s ease-out';
            setTimeout(() => flashDiv.remove(), 300);
        }, 4000);
    }
    
    /**
     * Inicializar auto-cierre de mensajes flash
     */
    function initFlashMessages() {
        const flashMessages = document.querySelectorAll('.flash-messages .flash');
        flashMessages.forEach(flash => {
            setTimeout(() => {
                flash.style.animation = 'slideOutUp 0.3s ease-out';
                setTimeout(() => flash.remove(), 300);
            }, 5000);
        });
    }
    
    /**
     * Atajos de teclado
     */
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Escape para limpiar formulario
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
