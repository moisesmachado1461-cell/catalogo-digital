(() => {
  'use strict';

  const query = (selector, root = document) => root.querySelector(selector);
  const queryAll = (selector, root = document) => [...root.querySelectorAll(selector)];

  function initials(value = '', fallback = 'CD') {
    const parts = String(value || '').trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return fallback;
    return parts.slice(0, 2).map(part => part[0]).join('').toUpperCase();
  }

  function nullable(value) {
    const text = String(value ?? '').trim();
    return text === '' ? null : text;
  }

  const checked = value => (value ? 'checked' : '');
  const optionSelected = (current, expected) => (String(current ?? '') === String(expected ?? '') ? 'selected' : '');

  function toDateTimeLocal(value) {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
    return local.toISOString().slice(0, 16);
  }

  window.CatalogoUtils = Object.freeze({
    query,
    queryAll,
    initials,
    nullable,
    checked,
    optionSelected,
    toDateTimeLocal,
  });
})();
