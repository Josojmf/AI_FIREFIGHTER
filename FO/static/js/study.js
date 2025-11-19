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
    emptyState: document.getElementById('emptyState'),
    dueTotal: document.getElementById('dueTotal')
  };

  let currentCard = null;

  // Funciones de utilidad
  function formatDate(dateString) {
    if (!dateString) return '—';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: '2-digit'
      });
    } catch {
      return '—';
    }
  }

  function setLoading(loading) {
    elements.btnNext.disabled = loading;
    const spinner = elements.btnNext.querySelector('.btn-spinner');
    const text = elements.btnNext.querySelector('.btn-text');
    if (spinner && text) {
      spinner.hidden = !loading;
      text.hidden = loading;
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

  // Funciones de API
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
      return null;
    }
  }

  async function loadNextCard() {
    setLoading(true);
    hideAnswer();
    elements.emptyState.hidden = true;
    enableAnswerButtons(false);
    
    const response = await fetchJSON('/api/leitner/next');
    
    setLoading(false);
    
    if (!response || !response.ok) {
      showEmptyState();
      return;
    }
    
    if (!response.card) {
      showEmptyState();
      return;
    }
    
    currentCard = response.card;
    elements.question.textContent = currentCard.question;
    elements.answer.textContent = currentCard.answer;
    elements.stateBox.textContent = `Caja ${currentCard.box}`;
    elements.stateNext.textContent = formatDate(response.state?.next_review_at);
    
    hideAnswer();
    enableAnswerButtons(true);
    elements.emptyState.hidden = true;
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
    
    const response = await fetchJSON('/api/leitner/answer', {
      method: 'POST',
      body: JSON.stringify({
        card_id: currentCard.id,
        correct: isCorrect
      })
    });
    
    if (response && response.ok) {
      await loadNextCard();
    } else {
      enableAnswerButtons(true);
    }
  }

  // Event listeners
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

  // Atajos de teclado
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
        elements.btnWrong.click();
        break;
      case 'c':
        elements.btnRight.click();
        break;
      case 'n':
        elements.btnNext.click();
        break;
    }
  });

  // Cargar primera tarjeta
  loadNextCard();
});