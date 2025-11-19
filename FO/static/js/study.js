// study_enhanced.js - Sistema Leitner mejorado

document.addEventListener('DOMContentLoaded', function() {
  const elements = {
    question: document.getElementById('question'),
    answer: document.getElementById('answer'),
    stateBox: document.getElementById('stateBox'),
    stateNext: document.getElementById('stateNext'),
    btnToggle: document.getElementById('btnToggle'),
    btnNext: document.getElementById('btnNext'),
    btnRight: document.getElementById('btnRight'),
    btnWrong: document.getElementById('btnWrong'),
    btnTryNew: document.getElementById('btnTryNew'),
    btnSync: document.getElementById('btnSync'),
    emptyState: document.getElementById('emptyState'),
    dueTotal: document.getElementById('dueTotal'),
    progressBar: document.getElementById('progressBar'),
    statsPanel: document.getElementById('statsPanel')
  };

  let currentCard = null;
  let sessionStats = {
    correct: 0,
    incorrect: 0,
    total: 0,
    startTime: Date.now()
  };

  // === UTILITY FUNCTIONS ===
  function formatDate(dateString) {
    if (!dateString) return '—';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return '—';
    }
  }

  function setLoading(elementOrButton, loading) {
    if (typeof elementOrButton === 'string') {
      elementOrButton = document.getElementById(elementOrButton);
    }
    
    elementOrButton.disabled = loading;
    const spinner = elementOrButton.querySelector('.btn-spinner') || elementOrButton.querySelector('.spinner');
    const text = elementOrButton.querySelector('.btn-text') || elementOrButton.querySelector('.text');
    
    if (spinner && text) {
      spinner.hidden = !loading;
      text.hidden = loading;
    }
  }

  function updateSessionStats() {
    const sessionTime = Math.floor((Date.now() - sessionStats.startTime) / 1000 / 60); // minutos
    const accuracy = sessionStats.total > 0 ? Math.round((sessionStats.correct / sessionStats.total) * 100) : 0;
    
    const statsHTML = `
      <div class="session-stats">
        <h3>📊 Estadísticas de Sesión</h3>
        <div class="stats-grid">
          <div class="stat">
            <span class="label">Correctas</span>
            <strong class="value correct">${sessionStats.correct}</strong>
          </div>
          <div class="stat">
            <span class="label">Incorrectas</span>
            <strong class="value incorrect">${sessionStats.incorrect}</strong>
          </div>
          <div class="stat">
            <span class="label">Precisión</span>
            <strong class="value">${accuracy}%</strong>
          </div>
          <div class="stat">
            <span class="label">Tiempo</span>
            <strong class="value">${sessionTime}min</strong>
          </div>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${accuracy}%"></div>
        </div>
      </div>
    `;
    
    if (elements.statsPanel) {
      elements.statsPanel.innerHTML = statsHTML;
    }
  }

  function hideAnswer() {
    elements.answer.classList.add('is-hidden');
    elements.btnToggle.innerHTML = '<span class="eye">👁️</span> Mostrar respuesta';
  }

  function showAnswer() {
    elements.answer.classList.remove('is-hidden');
    elements.btnToggle.innerHTML = '<span class="eye">🙈</span> Ocultar respuesta';
  }

  function enableAnswerButtons(enable) {
    elements.btnRight.disabled = !enable;
    elements.btnWrong.disabled = !enable;
  }

  function updateBoxCounters(data) {
    if (!data || !data.boxes) return;
    
    let totalDue = 0;
    data.boxes.forEach(box => {
      const boxId = box._id || box.id;
      const dueEl = document.getElementById(`due-${boxId}`);
      const totalEl = document.getElementById(`total-${boxId}`);
      
      if (dueEl) dueEl.textContent = box.due || 0;
      if (totalEl) totalEl.textContent = box.total || 0;
      
      totalDue += (box.due || 0);
      
      // Actualizar barra de progreso
      const boxTile = document.querySelector(`[data-box="${boxId}"]`);
      if (boxTile) {
        const bar = boxTile.querySelector('.fill');
        const total = box.total || 0;
        const due = box.due || 0;
        const percentage = total > 0 ? Math.round((due / total) * 100) : 0;
        
        if (bar) bar.style.width = `${percentage}%`;
        
        const pctText = boxTile.querySelector('.muted');
        if (pctText) pctText.textContent = `${percentage}% vencidas`;
      }
    });
    
    if (elements.dueTotal) {
      elements.dueTotal.textContent = totalDue;
    }
  }

  // === API FUNCTIONS ===
  async function fetchJSON(url, options = {}) {
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });
      
      if (response.status === 401) {
        window.location.href = '/login';
        return null;
      }
      
      return await response.json();
    } catch (error) {
      console.error('Fetch error:', error);
      showNotification('Error de conexión', 'error');
      return null;
    }
  }

  async function loadBoxSummary() {
    const response = await fetchJSON('/api/leitner/summary');
    if (response && response.ok) {
      updateBoxCounters(response);
    }
  }

  async function loadNextCard() {
    setLoading(elements.btnNext, true);
    hideAnswer();
    elements.emptyState.hidden = true;
    enableAnswerButtons(false);
    
    const response = await fetchJSON('/api/leitner/next');
    
    setLoading(elements.btnNext, false);
    
    if (!response || !response.ok) {
      showEmptyState();
      return;
    }
    
    if (!response.card) {
      showEmptyState();
      return;
    }
    
    currentCard = response.card;
    elements.question.textContent = currentCard.question || currentCard.front || 'Sin pregunta';
    elements.answer.textContent = currentCard.answer || currentCard.back || 'Sin respuesta';
    elements.stateBox.textContent = `Caja ${currentCard.box}`;
    elements.stateNext.textContent = formatDate(response.state?.next_review_at);
    
    hideAnswer();
    enableAnswerButtons(true);
    elements.emptyState.hidden = true;
    
    // Actualizar contadores
    await loadBoxSummary();
  }

  function showEmptyState() {
    elements.question.textContent = 'No hay tarjetas pendientes';
    elements.answer.textContent = '';
    elements.stateBox.textContent = '—';
    elements.stateNext.textContent = '—';
    enableAnswerButtons(false);
    elements.emptyState.hidden = false;
  }

  async function submitAnswer(isCorrect) {
    if (!currentCard) return;
    
    enableAnswerButtons(false);
    
    // Actualizar estadísticas de sesión
    sessionStats.total++;
    if (isCorrect) {
      sessionStats.correct++;
    } else {
      sessionStats.incorrect++;
    }
    updateSessionStats();
    
    const response = await fetchJSON('/api/leitner/answer', {
      method: 'POST',
      body: JSON.stringify({
        card_id: currentCard.id,
        correct: isCorrect
      })
    });
    
    if (response && response.ok) {
      // Mostrar feedback visual
      showAnswerFeedback(isCorrect);
      
      // Cargar siguiente tarjeta después de un breve delay
      setTimeout(() => {
        if (response.next && response.next.card) {
          // La API ya devuelve la siguiente tarjeta
          currentCard = response.next.card;
          elements.question.textContent = currentCard.question || currentCard.front || 'Sin pregunta';
          elements.answer.textContent = currentCard.answer || currentCard.back || 'Sin respuesta';
          elements.stateBox.textContent = `Caja ${currentCard.box}`;
          elements.stateNext.textContent = formatDate(response.next.state?.next_review_at);
          
          hideAnswer();
          enableAnswerButtons(true);
          elements.emptyState.hidden = true;
        } else {
          loadNextCard();
        }
      }, 1000);
    } else {
      enableAnswerButtons(true);
    }
  }

  function showAnswerFeedback(isCorrect) {
    const feedbackEl = document.createElement('div');
    feedbackEl.className = `answer-feedback ${isCorrect ? 'correct' : 'incorrect'}`;
    feedbackEl.innerHTML = isCorrect ? '✅ Correcto!' : '❌ Incorrecto';
    
    elements.question.parentNode.appendChild(feedbackEl);
    
    setTimeout(() => {
      feedbackEl.remove();
    }, 2000);
  }

  // === SYNC FUNCTION ===
  async function syncMemoryCards() {
    if (!elements.btnSync) return;
    
    setLoading(elements.btnSync, true);
    
    const response = await fetchJSON('/api/leitner/sync', {
      method: 'POST'
    });
    
    setLoading(elements.btnSync, false);
    
    if (response && response.ok) {
      showNotification(`✅ Sincronizadas ${response.synced} tarjetas`, 'success');
      await loadBoxSummary();
      await loadNextCard();
    } else {
      showNotification('❌ Error en sincronización', 'error');
    }
  }

  // === NOTIFICATION SYSTEM ===
  function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
      notification.classList.remove('show');
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  // === EVENT LISTENERS ===
  elements.btnToggle.addEventListener('click', function() {
    if (elements.answer.classList.contains('is-hidden')) {
      showAnswer();
    } else {
      hideAnswer();
    }
  });

  elements.btnNext.addEventListener('click', loadNextCard);
  elements.btnTryNew.addEventListener('click', loadNextCard);
  elements.btnRight.addEventListener('click', () => submitAnswer(true));
  elements.btnWrong.addEventListener('click', () => submitAnswer(false));

  if (elements.btnSync) {
    elements.btnSync.addEventListener('click', syncMemoryCards);
  }

  // === KEYBOARD SHORTCUTS ===
  document.addEventListener('keydown', function(event) {
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
      return;
    }
    
    switch (event.key.toLowerCase()) {
      case ' ':
        event.preventDefault();
        elements.btnToggle.click();
        break;
      case 'x':
        event.preventDefault();
        elements.btnWrong.click();
        break;
      case 'c':
        event.preventDefault();
        elements.btnRight.click();
        break;
      case 'n':
        event.preventDefault();
        elements.btnNext.click();
        break;
      case 's':
        if (event.ctrlKey && elements.btnSync) {
          event.preventDefault();
          elements.btnSync.click();
        }
        break;
    }
  });

  // === INITIALIZATION ===
  updateSessionStats();
  loadBoxSummary();
  loadNextCard();
  
  // Auto-refresh summary every 30 seconds
  setInterval(loadBoxSummary, 30000);
});