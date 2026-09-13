(function () {
  'use strict';

  const knowledge = window.CatalogoAssistantKnowledge;
  if (!knowledge || document.querySelector('[data-cd-assistant-root]')) return;

  const normalize = (value = '') => value
    .toString()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  const escapeHtml = (value = '') => value.toString().replace(/[&<>'"]/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
  }[char]));

  const stopWords = new Set(['a', 'o', 'as', 'os', 'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'no', 'na', 'nos', 'nas', 'para', 'por', 'com', 'como', 'que', 'um', 'uma', 'eu', 'me', 'meu', 'minha']);
  const tokens = (value) => normalize(value).split(' ').filter((token) => token.length > 1 && !stopWords.has(token));

  function detectArea() {
    const path = location.pathname.toLowerCase();
    if (path.includes('super-admin')) return 'super';
    if (path.includes('admin')) return 'admin';
    if (path.includes('cliente')) return 'customer';
    if (path.includes('loja') || path.includes('agendamento') || path.includes('acompanhar')) return 'store';
    return 'public';
  }

  function detectSection(area) {
    if (area === 'admin') return document.querySelector('.admin-section.active[id]')?.id || 'dashboard';
    if (area === 'super') return (document.querySelector('.admin-section.active[id]')?.id || 'super-dashboard').replace(/^super-/, '');
    if (area === 'customer') {
      if (!document.getElementById('customerPortalView')?.classList.contains('hidden')) {
        return document.querySelector('.customer-portal-tab.active')?.dataset.customerTab || 'orders';
      }
      return 'account';
    }
    if (location.pathname.toLowerCase().includes('acompanhar')) return 'tracking';
    if (location.pathname.toLowerCase().includes('agendamento')) return 'booking';
    if (area === 'store') {
      const target = document.querySelector('#storeTabs .tab-btn.active')?.dataset.target || '';
      const sectionMap = {
        catalogSection: 'catalog', servicesSection: 'services', couponsSection: 'catalog',
        reservationsSection: 'reservations', rentalsSection: 'rentals', contactSection: 'contact',
      };
      return sectionMap[target] || 'home';
    }
    return 'home';
  }

  function context() {
    const area = detectArea();
    const section = detectSection(area);
    return {
      area,
      section,
      areaLabel: knowledge.areaLabels[area] || 'Ajuda',
      sectionLabel: knowledge.sectionLabels[section] || 'Início',
    };
  }

  function entryText(item) {
    return normalize([item.title, item.answer, ...(item.keywords || [])].join(' '));
  }

  function rankKnowledge(query, ctx) {
    const normalizedQuery = normalize(query);
    const queryTokens = tokens(query);
    return knowledge.entries.map((item) => {
      let score = 0;
      const text = entryText(item);
      if (item.areas.includes(ctx.area)) score += 5;
      if (item.sections.includes(ctx.section)) score += 7;
      if (item.sections.includes('home')) score += 1;
      (item.keywords || []).forEach((keyword) => {
        const key = normalize(keyword);
        if (normalizedQuery.includes(key)) score += key.includes(' ') ? 8 : 5;
      });
      queryTokens.forEach((token) => {
        if (text.includes(token)) score += 2;
      });
      if (normalize(item.title) === normalizedQuery) score += 10;
      return { item, score };
    })
      .sort((a, b) => b.score - a.score);
  }

  function searchKnowledge(query, ctx) {
    const best = rankKnowledge(query, ctx)[0];
    return best?.score >= 5 ? best.item : null;
  }

  function contextualEntries(ctx, limit = 4) {
    const exact = knowledge.entries.filter((item) => item.areas.includes(ctx.area) && item.sections.includes(ctx.section));
    const areaEntries = knowledge.entries.filter((item) => item.areas.includes(ctx.area) && !exact.includes(item));
    return [...exact, ...areaEntries].slice(0, limit);
  }

  function knowledgeForAi(query, ctx, limit = 5) {
    const selected = [];
    const seen = new Set();
    const add = (item) => {
      if (!item || seen.has(item.id)) return;
      seen.add(item.id);
      selected.push(item);
    };

    rankKnowledge(query, ctx)
      .filter(({ score }) => score >= 3)
      .slice(0, limit)
      .forEach(({ item }) => add(item));
    contextualEntries(ctx, limit).forEach(add);

    return selected.slice(0, limit).map((item) => ({
      title: item.title,
      answer: item.answer,
      steps: (item.steps || []).slice(0, 4),
    }));
  }

  function resolveWhatsAppLink() {
    const links = [...document.querySelectorAll('a[href]')];
    const match = links.find((link) => /wa\.me|api\.whatsapp\.com|whatsapp\.com\/send/i.test(link.href));
    return match?.href || '';
  }

  const root = document.createElement('div');
  root.dataset.cdAssistantRoot = 'true';
  root.innerHTML = `
    <button class="cd-assistant-launcher" type="button" aria-label="Abrir assistente" aria-expanded="false">
      <span class="cd-assistant-launcher-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none"><path d="M7 18.2 3.8 20l.9-3.7A8.5 8.5 0 1 1 7 18.2Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M8.5 11.5h.01M12 11.5h.01M15.5 11.5h.01" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>
      </span>
      <span class="cd-assistant-launcher-copy"><b>Precisa de ajuda?</b><small>Assistente do Catálogo</small></span>
    </button>
    <section class="cd-assistant-panel" aria-hidden="true" aria-label="Assistente do Catálogo Digital">
      <header class="cd-assistant-header">
        <div class="cd-assistant-brandmark">CD</div>
        <div class="cd-assistant-heading"><strong>Assistente do Catálogo <em class="cd-assistant-ai-badge">IA</em></strong><span><i></i><span data-assistant-context>Ajuda contextual</span></span></div>
        <button class="cd-assistant-close" type="button" aria-label="Fechar assistente">×</button>
      </header>
      <div class="cd-assistant-messages" role="log" aria-live="polite"></div>
      <div class="cd-assistant-suggestions" aria-label="Sugestões de perguntas"></div>
      <div class="cd-assistant-whatsapp-wrap" hidden>
        <a class="cd-assistant-whatsapp" target="_blank" rel="noopener noreferrer">Continuar no WhatsApp <span aria-hidden="true">↗</span></a>
      </div>
      <form class="cd-assistant-form">
        <label class="sr-only" for="cdAssistantInput">Digite sua dúvida</label>
        <input id="cdAssistantInput" class="cd-assistant-input" autocomplete="off" maxlength="500" placeholder="Ex.: Como cadastro um produto?">
        <button class="cd-assistant-send" type="submit" aria-label="Enviar pergunta">
          <svg viewBox="0 0 24 24" fill="none"><path d="m4 4 16 8-16 8 3-8-3-8Zm3 8h13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
      </form>
      <footer class="cd-assistant-footer">IA contextual + base oficial central · respostas objetivas · sem acesso a senhas ou segredos</footer>
    </section>`;
  document.body.appendChild(root);

  const launcher = root.querySelector('.cd-assistant-launcher');
  const panel = root.querySelector('.cd-assistant-panel');
  const closeButton = root.querySelector('.cd-assistant-close');
  const messages = root.querySelector('.cd-assistant-messages');
  const suggestions = root.querySelector('.cd-assistant-suggestions');
  const form = root.querySelector('.cd-assistant-form');
  const input = root.querySelector('.cd-assistant-input');
  const sendButton = root.querySelector('.cd-assistant-send');
  const contextLabel = root.querySelector('[data-assistant-context]');
  const whatsappWrap = root.querySelector('.cd-assistant-whatsapp-wrap');
  const whatsappLink = root.querySelector('.cd-assistant-whatsapp');
  const conversationHistory = [];
  let greeted = false;
  let busy = false;

  function addMessage(kind, content, steps = []) {
    const item = document.createElement('div');
    item.className = `cd-assistant-message ${kind}`;
    const stepsHtml = steps.length
      ? `<ol>${steps.map((step) => `<li>${escapeHtml(step)}</li>`).join('')}</ol>`
      : '';
    item.innerHTML = `<div class="cd-assistant-bubble">${escapeHtml(content)}${stepsHtml}</div>`;
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
    return item;
  }

  function addTypingMessage() {
    const item = document.createElement('div');
    item.className = 'cd-assistant-message assistant cd-assistant-typing-message';
    item.innerHTML = '<div class="cd-assistant-bubble cd-assistant-typing" aria-label="Assistente digitando"><span></span><span></span><span></span></div>';
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
    return item;
  }

  function setBusy(value) {
    busy = value;
    input.disabled = value;
    sendButton.disabled = value;
    form.classList.toggle('is-busy', value);
  }

  function remember(role, content) {
    conversationHistory.push({ role, content: String(content).slice(0, 500) });
    if (conversationHistory.length > 8) conversationHistory.splice(0, conversationHistory.length - 8);
  }

  function renderSuggestions(ctx) {
    suggestions.innerHTML = '';
    contextualEntries(ctx).forEach((item) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'cd-assistant-chip';
      button.textContent = item.title;
      button.onclick = () => answerQuestion(item.title);
      suggestions.appendChild(button);
    });
  }

  function refreshContext() {
    const ctx = context();
    contextLabel.textContent = `${ctx.areaLabel} · ${ctx.sectionLabel}`;
    renderSuggestions(ctx);
    const whatsapp = resolveWhatsAppLink();
    if (whatsapp) {
      whatsappLink.href = whatsapp;
      whatsappWrap.hidden = false;
    } else {
      whatsappWrap.hidden = true;
    }
    return ctx;
  }

  function localFallback(question, ctx) {
    const generic = normalize(question);
    if (/o que posso fazer|me ajuda|ajuda nesta tela|como usar esta tela/.test(generic)) {
      const entries = contextualEntries(ctx, 3);
      return {
        answer: entries.length
          ? `Nesta área eu posso te orientar principalmente sobre ${entries.map((item) => item.title.toLowerCase()).join(', ')}.`
          : `Posso explicar as principais funções de ${ctx.areaLabel}.`,
        steps: [],
      };
    }
    const match = searchKnowledge(question, ctx);
    if (match) return { answer: match.answer, steps: match.steps || [] };
    return {
      answer: 'Ainda não encontrei uma resposta específica para essa pergunta. Tente citar o nome da função, como produto, pedido, estoque, cupom, agendamento, plano ou configuração.',
      steps: [],
    };
  }


  async function answerQuestion(question) {
    const cleaned = question.trim();
    if (!cleaned || busy) return;

    const priorHistory = conversationHistory.slice(-6);
    addMessage('user', cleaned);
    const ctx = refreshContext();
    setBusy(true);
    const typing = addTypingMessage();

    try {
      const payload = {
        question: cleaned,
        area: ctx.area,
        section: ctx.section,
        history: priorHistory,
      };
      const response = await api('/api/assistant/chat', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      typing.remove();
      const answer = response?.answer?.trim();
      if (!answer) throw new Error('Resposta vazia');
      addMessage('assistant', answer);
      remember('user', cleaned);
      remember('assistant', answer);
    } catch (error) {
      typing.remove();
      const fallback = localFallback(cleaned, ctx);
      addMessage('assistant', fallback.answer, fallback.steps);
      remember('user', cleaned);
      remember('assistant', fallback.answer);
    } finally {
      setBusy(false);
      input.focus();
    }
  }

  function openAssistant() {
    panel.classList.add('open');
    panel.setAttribute('aria-hidden', 'false');
    launcher.setAttribute('aria-expanded', 'true');
    const ctx = refreshContext();
    if (!greeted) {
      addMessage('assistant', `Olá! Sou a IA de ajuda do Catálogo Digital. Estou vendo que você está em “${ctx.sectionLabel}”. Pergunte o que quiser sobre o uso do sistema.`);
      greeted = true;
    }
    window.setTimeout(() => input.focus(), 80);
  }

  function closeAssistant() {
    panel.classList.remove('open');
    panel.setAttribute('aria-hidden', 'true');
    launcher.setAttribute('aria-expanded', 'false');
  }

  launcher.addEventListener('click', () => panel.classList.contains('open') ? closeAssistant() : openAssistant());
  closeButton.addEventListener('click', closeAssistant);
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const value = input.value;
    input.value = '';
    answerQuestion(value);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && panel.classList.contains('open')) closeAssistant();
  });
  document.addEventListener('click', (event) => {
    if (event.target.closest('[data-section], [data-super-section], #storeTabs .tab-btn, .customer-portal-tab')) {
      window.setTimeout(refreshContext, 80);
    }
  });

  refreshContext();
})();
