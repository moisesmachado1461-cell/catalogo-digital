(() => {
  'use strict';

  document.documentElement.classList.add('ui-v20');

  function ensureToastRegion() {
    let region = document.querySelector('.ds-toast-region');
    if (region) return region;
    region = document.createElement('div');
    region.className = 'ds-toast-region';
    region.setAttribute('aria-live', 'polite');
    region.setAttribute('aria-atomic', 'false');
    document.body.appendChild(region);
    return region;
  }

  function toast(message, type = 'info', title = '') {
    if (!message) return;
    const region = ensureToastRegion();
    const item = document.createElement('div');
    item.className = `ds-toast ${type}`;
    item.setAttribute('role', type === 'error' ? 'alert' : 'status');

    const strong = document.createElement('strong');
    strong.textContent = title || ({success:'Tudo certo', error:'Não foi possível concluir', warning:'Atenção'}[type] || 'Catálogo Digital');
    const span = document.createElement('span');
    span.textContent = String(message);
    item.append(strong, span);
    region.appendChild(item);

    requestAnimationFrame(() => item.classList.add('show'));
    const lifetime = Math.max(3200, Math.min(6500, String(message).length * 55));
    window.setTimeout(() => {
      item.classList.remove('show');
      window.setTimeout(() => item.remove(), 260);
    }, lifetime);
  }

  function updateTopbar() {
    document.querySelectorAll('.topbar').forEach(bar => {
      bar.classList.toggle('is-scrolled', window.scrollY > 8);
    });
  }

  function revealExisting() {
    const candidates = document.querySelectorAll('main > .section, .admin-section.active > .panel, .admin-section.active > .stats, .billing-command-hero, .billing-admin-hero');
    candidates.forEach((el, index) => {
      if (el.classList.contains('ds-visible')) return;
      el.classList.add('ds-reveal');
      window.setTimeout(() => el.classList.add('ds-visible'), Math.min(index * 55, 260));
    });
  }

  function setupMutationObserver() {
    if (!('MutationObserver' in window)) return;
    const observer = new MutationObserver(mutations => {
      let shouldReveal = false;
      for (const mutation of mutations) {
        if (mutation.addedNodes && mutation.addedNodes.length) {
          shouldReveal = true;
          break;
        }
      }
      if (shouldReveal) requestAnimationFrame(revealExisting);
    });
    observer.observe(document.body, {childList:true, subtree:true});
  }

  function ready() {
    document.body.classList.add('ui-ready');
    updateTopbar();
    revealExisting();
    setupMutationObserver();

    window.addEventListener('scroll', updateTopbar, {passive:true});
    window.addEventListener('online', () => toast('Conexão restabelecida.', 'success'));
    window.addEventListener('offline', () => toast('Você está sem conexão. Algumas ações podem ficar indisponíveis.', 'warning'));
  }

  window.CDUI = Object.freeze({toast});

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ready, {once:true});
  } else {
    ready();
  }
})();
