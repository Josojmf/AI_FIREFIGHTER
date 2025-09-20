// Modern App JavaScript - FirefighterAI Platform
class FirefighterApp {
  constructor() {
    this.init();
  }

  init() {
    this.setupNavbar();
    this.setupMobileMenu();
    this.setupUserDropdown();
    this.setupScrollEffects();
    this.setupPageTransitions();
    this.setupFlashMessages();
    this.setupKeyboardNavigation();
    this.setupPerformanceOptimizations();
  }

  // Navbar functionality
  setupNavbar() {
    const navbar = document.getElementById('navbar');
    const pageProgress = document.getElementById('page-progress');
    let lastScrollY = window.scrollY;
    let ticking = false;

    const updateNavbar = () => {
      const scrollY = window.scrollY;
      const scrollProgress = Math.min(scrollY / (document.documentElement.scrollHeight - window.innerHeight), 1);
      
      // Add scrolled class
      navbar.classList.toggle('scrolled', scrollY > 50);
      
      // Update progress bar
      if (pageProgress) {
        pageProgress.style.width = `${scrollProgress * 100}%`;
      }

      // Hide/show navbar on scroll direction (optional)
      if (scrollY > lastScrollY && scrollY > 100) {
        navbar.style.transform = 'translateY(-100%)';
      } else {
        navbar.style.transform = 'translateY(0)';
      }
      
      lastScrollY = scrollY;
      ticking = false;
    };

    const onScroll = () => {
      if (!ticking) {
        requestAnimationFrame(updateNavbar);
        ticking = true;
      }
    };

    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // Mobile menu functionality
  setupMobileMenu() {
    const mobileToggle = document.getElementById('mobile-menu-toggle');
    const mobileOverlay = document.getElementById('mobile-menu-overlay');
    const mobileClose = document.getElementById('mobile-close');
    const mobileLinks = document.querySelectorAll('.mobile-nav-link');

    if (!mobileToggle || !mobileOverlay) return;

    const openMobileMenu = () => {
      mobileToggle.classList.add('active');
      mobileOverlay.classList.add('active');
      document.body.style.overflow = 'hidden';
      
      // Focus management
      mobileClose?.focus();
      
      // Animate links
      const links = document.querySelectorAll('.mobile-nav-links li');
      links.forEach((link, index) => {
        link.style.animationDelay = `${(index + 1) * 0.1}s`;
      });
    };

    const closeMobileMenu = () => {
      mobileToggle.classList.remove('active');
      mobileOverlay.classList.remove('active');
      document.body.style.overflow = '';
      
      // Return focus to toggle button
      mobileToggle.focus();
    };

    // Event listeners
    mobileToggle.addEventListener('click', openMobileMenu);
    mobileClose?.addEventListener('click', closeMobileMenu);
    
    // Close on overlay click
    mobileOverlay.addEventListener('click', (e) => {
      if (e.target === mobileOverlay) {
        closeMobileMenu();
      }
    });

    // Close on link click
    mobileLinks.forEach(link => {
      link.addEventListener('click', closeMobileMenu);
    });

    // Close on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && mobileOverlay.classList.contains('active')) {
        closeMobileMenu();
      }
    });
  }

  // User dropdown functionality
  setupUserDropdown() {
    const userDropdown = document.getElementById('user-dropdown');
    const userButton = userDropdown?.querySelector('.user-button');
    const dropdownMenu = userDropdown?.querySelector('.dropdown-menu');

    if (!userDropdown || !userButton) return;

    let isOpen = false;

    const openDropdown = () => {
      isOpen = true;
      userDropdown.setAttribute('aria-expanded', 'true');
      userButton.setAttribute('aria-expanded', 'true');
      
      // Focus first item
      const firstItem = dropdownMenu?.querySelector('.dropdown-item');
      firstItem?.focus();
    };

    const closeDropdown = () => {
      isOpen = false;
      userDropdown.setAttribute('aria-expanded', 'false');
      userButton.setAttribute('aria-expanded', 'false');
    };

    const toggleDropdown = () => {
      isOpen ? closeDropdown() : openDropdown();
    };

    // Event listeners
    userButton.addEventListener('click', toggleDropdown);
    
    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!userDropdown.contains(e.target)) {
        closeDropdown();
      }
    });

    // Keyboard navigation
    userDropdown.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeDropdown();
        userButton.focus();
      }
    });
  }

  // Scroll effects
  setupScrollEffects() {
    // Scroll to top button
    const scrollTopBtn = document.getElementById('scroll-to-top');
    
    if (scrollTopBtn) {
      const toggleScrollTopBtn = () => {
        const shouldShow = window.scrollY > 500;
        scrollTopBtn.classList.toggle('visible', shouldShow);
      };

      window.addEventListener('scroll', toggleScrollTopBtn, { passive: true });
      
      scrollTopBtn.addEventListener('click', () => {
        window.scrollTo({
          top: 0,
          behavior: 'smooth'
        });
      });
    }

    // Intersection Observer for animations
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade-in');
        }
      });
    }, observerOptions);

    // Observe elements that should animate on scroll
    document.querySelectorAll('.animate-on-scroll').forEach(el => {
      observer.observe(el);
    });
  }

  // Page transitions
  setupPageTransitions() {
    const links = document.querySelectorAll('a[href^="/"]');
    
    links.forEach(link => {
      link.addEventListener('click', (e) => {
        // Skip if it's an external link or has special attributes
        if (link.getAttribute('target') === '_blank' || 
            link.getAttribute('download') || 
            link.getAttribute('data-no-transition')) {
          return;
        }

        e.preventDefault();
        const href = link.getAttribute('href');
        
        // Add page transition effect
        document.body.style.opacity = '0.8';
        document.body.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
          window.location.href = href;
        }, 150);
      });
    });
  }

  // Flash messages
  setupFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach((message, index) => {
      // Animate in
      setTimeout(() => {
        message.style.animation = 'slide-in-right 0.5s ease-out';
      }, index * 100);

      // Auto-dismiss after 5 seconds
      setTimeout(() => {
        this.dismissFlashMessage(message);
      }, 5000 + (index * 100));

      // Handle close button
      const closeBtn = message.querySelector('.flash-close');
      closeBtn?.addEventListener('click', () => {
        this.dismissFlashMessage(message);
      });
    });
  }

  dismissFlashMessage(message) {
    message.style.animation = 'slide-out-right 0.3s ease-in';
    setTimeout(() => {
      message.remove();
    }, 300);
  }

  // Keyboard navigation
  setupKeyboardNavigation() {
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      // Alt + M for mobile menu
      if (e.altKey && e.key === 'm') {
        e.preventDefault();
        const mobileToggle = document.getElementById('mobile-menu-toggle');
        mobileToggle?.click();
      }
      
      // Alt + S for search (if exists)
      if (e.altKey && e.key === 's') {
        e.preventDefault();
        const searchInput = document.querySelector('input[type="search"]');
        searchInput?.focus();
      }
      
      // Alt + H for home
      if (e.altKey && e.key === 'h') {
        e.preventDefault();
        window.location.href = '/';
      }
    });

    // Skip links for accessibility
    this.createSkipLinks();
  }

  createSkipLinks() {
    const skipLinks = document.createElement('div');
    skipLinks.className = 'skip-links';
    skipLinks.innerHTML = `
      <a href="#main-content" class="skip-link">Saltar al contenido principal</a>
      <a href="#navigation" class="skip-link">Saltar a la navegación</a>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
      .skip-links {
        position: absolute;
        top: -100px;
        left: 0;
        z-index: 10000;
      }
      .skip-link {
        position: absolute;
        top: 0;
        left: 0;
        background: var(--primary-red);
        color: white;
        padding: 8px 16px;
        text-decoration: none;
        border-radius: 0 0 4px 0;
        font-weight: 600;
        transform: translateY(-100%);
        transition: transform 0.3s;
      }
      .skip-link:focus {
        transform: translateY(0);
      }
    `;
    
    document.head.appendChild(style);
    document.body.insertBefore(skipLinks, document.body.firstChild);
  }

  // Performance optimizations
  setupPerformanceOptimizations() {
    // Lazy load images
    this.setupLazyLoading();
    
    // Prefetch links on hover
    this.setupLinkPrefetching();
    
    // Debounce resize events
    this.setupResizeHandler();
  }

  setupLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.classList.remove('lazy');
            imageObserver.unobserve(img);
          }
        });
      });

      images.forEach(img => imageObserver.observe(img));
    } else {
      // Fallback for older browsers
      images.forEach(img => {
        img.src = img.dataset.src;
        img.classList.remove('lazy');
      });
    }
  }

  setupLinkPrefetching() {
    const links = document.querySelectorAll('a[href^="/"]');
    const prefetchedUrls = new Set();

    links.forEach(link => {
      link.addEventListener('mouseenter', () => {
        const href = link.getAttribute('href');
        if (!prefetchedUrls.has(href)) {
          const linkElement = document.createElement('link');
          linkElement.rel = 'prefetch';
          linkElement.href = href;
          document.head.appendChild(linkElement);
          prefetchedUrls.add(href);
        }
      }, { once: true });
    });
  }

  setupResizeHandler() {
    let resizeTimeout;
    const handleResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        // Handle responsive updates
        this.updateLayoutOnResize();
      }, 250);
    };

    window.addEventListener('resize', handleResize, { passive: true });
  }

  updateLayoutOnResize() {
    // Close mobile menu if screen becomes large
    if (window.innerWidth > 768) {
      const mobileOverlay = document.getElementById('mobile-menu-overlay');
      const mobileToggle = document.getElementById('mobile-menu-toggle');
      
      if (mobileOverlay?.classList.contains('active')) {
        mobileOverlay.classList.remove('active');
        mobileToggle?.classList.remove('active');
        document.body.style.overflow = '';
      }
    }

    // Update any dynamic heights or positions
    this.updateDynamicElements();
  }

  updateDynamicElements() {
    // Update any elements that need recalculation on resize
    const dynamicElements = document.querySelectorAll('[data-dynamic-height]');
    dynamicElements.forEach(element => {
      const targetHeight = window.innerHeight - element.getBoundingClientRect().top;
      element.style.height = `${targetHeight}px`;
    });
  }

  // Utility methods
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  // API utilities
  async fetchWithErrorHandling(url, options = {}) {
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Fetch error:', error);
      this.showNotification('Error de conexión. Por favor, inténtalo de nuevo.', 'error');
      throw error;
    }
  }

  // Notification system
  showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `flash-message flash-${type}`;
    notification.innerHTML = `
      <div class="flash-icon">
        ${type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}
      </div>
      <div class="flash-content">
        <p>${message}</p>
      </div>
      <button class="flash-close">✕</button>
    `;

    // Add to flash messages container or create one
    let container = document.getElementById('flash-messages');
    if (!container) {
      container = document.createElement('div');
      container.id = 'flash-messages';
      container.className = 'flash-messages';
      document.body.appendChild(container);
    }

    container.appendChild(notification);

    // Handle close button
    notification.querySelector('.flash-close').addEventListener('click', () => {
      this.dismissFlashMessage(notification);
    });

    // Auto-dismiss
    setTimeout(() => {
      if (notification.parentNode) {
        this.dismissFlashMessage(notification);
      }
    }, duration);
  }

  // Form utilities
  setupFormEnhancements() {
    const forms = document.querySelectorAll('form[data-enhance]');
    
    forms.forEach(form => {
      this.enhanceForm(form);
    });
  }

  enhanceForm(form) {
    // Add loading states
    form.addEventListener('submit', (e) => {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner"></span> Enviando...';
        
        // Re-enable after a timeout as fallback
        setTimeout(() => {
          submitBtn.disabled = false;
          submitBtn.innerHTML = submitBtn.dataset.originalText || 'Enviar';
        }, 30000);
      }
    });

    // Real-time validation
    const inputs = form.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
      input.addEventListener('blur', () => {
        this.validateField(input);
      });
    });
  }

  validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    let isValid = true;
    let errorMessage = '';

    // Basic validation
    if (field.required && !value) {
      isValid = false;
      errorMessage = 'Este campo es obligatorio';
    } else if (type === 'email' && value && !this.isValidEmail(value)) {
      isValid = false;
      errorMessage = 'Por favor, introduce un email válido';
    } else if (type === 'password' && value && value.length < 6) {
      isValid = false;
      errorMessage = 'La contraseña debe tener al menos 6 caracteres';
    }

    // Update field appearance
    field.classList.toggle('invalid', !isValid);
    field.classList.toggle('valid', isValid && value);

    // Show/hide error message
    this.updateFieldError(field, errorMessage);

    return isValid;
  }

  updateFieldError(field, errorMessage) {
    let errorElement = field.parentNode.querySelector('.field-error');
    
    if (errorMessage) {
      if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'field-error';
        field.parentNode.appendChild(errorElement);
      }
      errorElement.textContent = errorMessage;
    } else if (errorElement) {
      errorElement.remove();
    }
  }

  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  // Theme utilities
  setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;

    const currentTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);

    themeToggle.addEventListener('click', () => {
      const newTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
    });
  }

  // Analytics and tracking
  trackUserInteraction(action, category = 'general', label = '') {
    // Basic interaction tracking
    if (typeof gtag !== 'undefined') {
      gtag('event', action, {
        event_category: category,
        event_label: label
      });
    }

    // Custom analytics
    this.sendAnalytics({
      action,
      category,
      label,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent
    });
  }

  async sendAnalytics(data) {
    try {
      await fetch('/api/analytics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
    } catch (error) {
      // Silently fail analytics
      console.debug('Analytics error:', error);
    }
  }
}

// Chat functionality
class ChatInterface {
  constructor(container) {
    this.container = container;
    this.messageHistory = [];
    this.isTyping = false;
    this.init();
  }

  init() {
    this.setupChat();
    this.loadHistory();
  }

  setupChat() {
    const form = this.container.querySelector('#chat-form');
    const input = this.container.querySelector('#user-input');
    const chatBox = this.container.querySelector('#chat-box');

    if (!form || !input || !chatBox) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const message = input.value.trim();
      if (!message || this.isTyping) return;

      this.addMessage(message, 'user');
      input.value = '';
      
      await this.sendMessage(message);
    });

    // Auto-resize textarea
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = input.scrollHeight + 'px';
    });

    // Enter to send (Shift+Enter for new line)
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        form.dispatchEvent(new Event('submit'));
      }
    });
  }

  addMessage(content, sender) {
    const chatBox = this.container.querySelector('#chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-msg ${sender}-msg`;
    messageDiv.innerHTML = this.formatMessage(content, sender);
    
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    // Add to history
    this.messageHistory.push({ content, sender, timestamp: Date.now() });
    this.saveHistory();

    return messageDiv;
  }

  formatMessage(content, sender) {
    if (sender === 'bot') {
      // Format bot messages with syntax highlighting, etc.
      return `<div class="message-content">${this.parseMarkdown(content)}</div>`;
    } else {
      return `<div class="message-content">${this.escapeHtml(content)}</div>`;
    }
  }

  parseMarkdown(text) {
    // Basic markdown parsing
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  async sendMessage(message) {
    this.isTyping = true;
    const typingIndicator = this.addTypingIndicator();

    try {
      const response = await fetch('/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
      });

      const data = await response.json();
      
      // Remove typing indicator
      typingIndicator.remove();
      
      // Add bot response
      this.addMessage(data.response, 'bot');
      
    } catch (error) {
      typingIndicator.remove();
      this.addMessage('Lo siento, ha ocurrido un error. Por favor, inténtalo de nuevo.', 'bot');
      console.error('Chat error:', error);
    } finally {
      this.isTyping = false;
    }
  }

  addTypingIndicator() {
    const chatBox = this.container.querySelector('#chat-box');
    const indicator = document.createElement('div');
    indicator.className = 'chat-msg bot-msg typing-indicator';
    indicator.innerHTML = `
      <div class="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    `;
    
    chatBox.appendChild(indicator);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    return indicator;
  }

  loadHistory() {
    const saved = localStorage.getItem('chat-history');
    if (saved) {
      this.messageHistory = JSON.parse(saved);
      // Optionally restore recent messages to UI
    }
  }

  saveHistory() {
    // Keep only last 50 messages
    if (this.messageHistory.length > 50) {
      this.messageHistory = this.messageHistory.slice(-50);
    }
    localStorage.setItem('chat-history', JSON.stringify(this.messageHistory));
  }
}

// Study system
class StudySystem {
  constructor() {
    this.currentQuestion = 0;
    this.questions = [];
    this.userAnswers = {};
    this.init();
  }

  init() {
    this.setupQuestionNavigation();
    this.setupFormSubmission();
    this.loadProgress();
  }

  setupQuestionNavigation() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const questions = document.querySelectorAll('.question-block');

    if (!questions.length) return;

    this.questions = Array.from(questions);
    this.showQuestion(0);

    prevBtn?.addEventListener('click', () => {
      if (this.currentQuestion > 0) {
        this.showQuestion(this.currentQuestion - 1);
      }
    });

    nextBtn?.addEventListener('click', () => {
      if (this.currentQuestion < this.questions.length - 1) {
        this.showQuestion(this.currentQuestion + 1);
      }
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      
      if (e.key === 'ArrowLeft' && this.currentQuestion > 0) {
        this.showQuestion(this.currentQuestion - 1);
      } else if (e.key === 'ArrowRight' && this.currentQuestion < this.questions.length - 1) {
        this.showQuestion(this.currentQuestion + 1);
      }
    });
  }

  showQuestion(index) {
    this.questions.forEach((q, i) => {
      q.style.display = i === index ? 'block' : 'none';
    });

    this.currentQuestion = index;
    this.updateNavButtons();
    this.saveProgress();
  }

  updateNavButtons() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const submitBtn = document.querySelector('.send-btn');

    if (prevBtn) {
      prevBtn.disabled = this.currentQuestion === 0;
    }

    if (nextBtn) {
      nextBtn.style.display = this.currentQuestion === this.questions.length - 1 ? 'none' : 'block';
    }

    if (submitBtn) {
      submitBtn.style.display = this.currentQuestion === this.questions.length - 1 ? 'block' : 'none';
    }
  }

  setupFormSubmission() {
    const form = document.getElementById('test-form');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.processAnswers(new FormData(form));
    });
  }

  async processAnswers(formData) {
    const responseBox = document.getElementById('response-box');
    if (!responseBox) return;

    responseBox.innerHTML = '<div class="loading-msg">🧠 Evaluando respuestas...</div>';

    for (let [key, value] of formData.entries()) {
      if (key.startsWith('q') && !key.includes('_')) {
        const qid = key.replace('q', '');
        const correct = formData.get(`correct_${qid}`);
        const questionText = formData.get(`q${qid}_text`);

        try {
          const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_answer: value,
              correct_option: correct,
              question_text: questionText
            })
          });

          const data = await response.json();
          responseBox.innerHTML += `
            <div class='response-card animate-fade-in'>
              <strong>📝 Pregunta ${qid}</strong><br>
              <em>${questionText}</em><br>
              ${data.response}
            </div>
          `;
        } catch (error) {
          console.error('Error processing question:', qid, error);
        }
      }
    }
  }

  loadProgress() {
    const saved = localStorage.getItem('study-progress');
    if (saved) {
      const progress = JSON.parse(saved);
      this.currentQuestion = progress.currentQuestion || 0;
      this.userAnswers = progress.userAnswers || {};
    }
  }

  saveProgress() {
    localStorage.setItem('study-progress', JSON.stringify({
      currentQuestion: this.currentQuestion,
      userAnswers: this.userAnswers,
      timestamp: Date.now()
    }));
  }
}

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
  // Initialize main app
  window.firefighterApp = new FirefighterApp();

  // Initialize chat if on chat page
  const chatContainer = document.querySelector('.chat-container');
  if (chatContainer) {
    window.chatInterface = new ChatInterface(chatContainer);
  }

  // Initialize study system if on study page
  const testForm = document.getElementById('test-form');
  if (testForm) {
    window.studySystem = new StudySystem();
  }

  // Track page view
  window.firefighterApp?.trackUserInteraction('page_view', 'navigation', window.location.pathname);
});

// Service Worker registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js')
      .then(registration => {
        console.log('🔥 SW registered successfully');
      })
      .catch(registrationError => {
        console.log('SW registration failed: ', registrationError);
      });
  });
}