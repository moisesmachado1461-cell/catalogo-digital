const API_REQUEST_TIMEOUT_MS = 90_000;
const MAX_IMAGE_UPLOAD_BYTES = 8 * 1024 * 1024;
const ALLOWED_IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);

function detectApiBase() {
  const runtimeBase = window.CATALOGO_CONFIG?.apiBase;
  if (runtimeBase) return String(runtimeBase).replace(/\/$/, '');

  const customBase = localStorage.getItem('catalogo_api_base');
  if (customBase) return customBase.replace(/\/$/, '');

  const { protocol, hostname, port, origin } = window.location;
  if (protocol === 'file:') return 'http://127.0.0.1:8000';

  const isLocalHost = hostname === 'localhost' || hostname === '127.0.0.1';
  const isLanAddress = /^\d{1,3}(\.\d{1,3}){3}$/.test(hostname);
  const isLocalFrontendPort = port === '5500' || port === '8080';
  if (isLocalFrontendPort || isLocalHost || isLanAddress) {
    return `${protocol}//${hostname}:8000`;
  }

  return origin;
}

const API_BASE = detectApiBase();

function assetUrl(value) {
  const url = String(value || '').trim();
  if (!url) return '';
  if (/^https?:\/\//i.test(url) || url.startsWith('data:') || url.startsWith('blob:')) return url;
  if (url.startsWith('/')) return `${API_BASE}${url}`;
  return url;
}

function getAuthToken() {
  const currentToken = sessionStorage.getItem('catalogo_token');
  if (currentToken) return currentToken;

  const legacyToken = localStorage.getItem('catalogo_token');
  if (!legacyToken) return null;

  sessionStorage.setItem('catalogo_token', legacyToken);
  localStorage.removeItem('catalogo_token');
  return legacyToken;
}

function clearAuthToken() {
  sessionStorage.removeItem('catalogo_token');
  localStorage.removeItem('catalogo_token');
}

function buildApiHeaders(options, token) {
  const headers = new Headers(options.headers || {});
  const hasJsonBody = options.body && !(options.body instanceof FormData);
  if (hasJsonBody && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  return headers;
}

async function parseApiResponse(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function apiErrorMessage(data, status) {
  const message = data?.detail || data?.message || `Erro HTTP ${status}`;
  return typeof message === 'string' ? message : JSON.stringify(message);
}

async function api(path, options = {}) {
  const token = getAuthToken();
  const headers = buildApiHeaders(options, token);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_REQUEST_TIMEOUT_MS);

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      cache: 'no-store',
      signal: options.signal || controller.signal,
    });
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new Error('A API demorou mais de 90 segundos para responder. Tente novamente.');
    }
    throw new Error(`Não foi possível conectar à API (${API_BASE}). Verifique se o backend está disponível.`);
  } finally {
    clearTimeout(timeoutId);
  }

  const data = await parseApiResponse(response);
  if (!response.ok) {
    if (response.status === 401 && token) clearAuthToken();
    throw new Error(apiErrorMessage(data, response.status));
  }
  return data;
}

async function uploadImage(file, kind) {
  if (!file) throw new Error('Selecione uma imagem.');
  if (!ALLOWED_IMAGE_TYPES.has(file.type)) throw new Error('Use uma imagem JPG, PNG ou WebP.');
  if (file.size > MAX_IMAGE_UPLOAD_BYTES) throw new Error('A imagem deve ter no máximo 8 MB.');

  const form = new FormData();
  form.append('kind', kind);
  form.append('file', file);
  return api('/api/admin/uploads/images', { method: 'POST', body: form });
}

function money(value) {
  const number = Number(value || 0);
  return number.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function escapeHtml(value = '') {
  const replacements = { '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' };
  return String(value).replace(/[&<>'"]/g, character => replacements[character]);
}

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('visible'));
  setTimeout(() => {
    toast.classList.remove('visible');
    setTimeout(() => toast.remove(), 250);
  }, 3200);
}
