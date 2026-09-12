function detectApiBase() {
  const runtime = window.CATALOGO_CONFIG?.apiBase;
  if (runtime) return String(runtime).replace(/\/$/, '');

  const custom = localStorage.getItem('catalogo_api_base');
  if (custom) return custom.replace(/\/$/, '');

  // Desenvolvimento local/LAN: usa o mesmo host do frontend e troca apenas a porta.
  // Ex.: http://192.168.0.15:5500 -> http://192.168.0.15:8000
  const { protocol, hostname, port, origin } = window.location;
  if (protocol === 'file:') return 'http://127.0.0.1:8000';
  if (port === '5500' || port === '8080' || hostname === 'localhost' || hostname === '127.0.0.1' || /^\d{1,3}(\.\d{1,3}){3}$/.test(hostname)) {
    return `${protocol}//${hostname}:8000`;
  }

  // Produção: frontend e API podem ficar atrás do mesmo domínio/reverse proxy.
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
  const current = sessionStorage.getItem('catalogo_token');
  if (current) return current;
  const legacy = localStorage.getItem('catalogo_token');
  if (legacy) {
    sessionStorage.setItem('catalogo_token', legacy);
    localStorage.removeItem('catalogo_token');
    return legacy;
  }
  return null;
}

function clearAuthToken() {
  sessionStorage.removeItem('catalogo_token');
  localStorage.removeItem('catalogo_token');
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const token = getAuthToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);

  let response;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 90000);
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers, cache: 'no-store', signal: options.signal || controller.signal });
  } catch (error) {
    if (error?.name === 'AbortError') throw new Error('A API demorou mais de 90 segundos para responder. Tente novamente.');
    throw new Error(`Não foi possível conectar à API (${API_BASE}). Verifique se o backend está disponível.`);
  } finally {
    clearTimeout(timeout);
  }

  const text = await response.text();
  let data = null;
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }
  if (!response.ok) {
    if (response.status === 401 && token) {
      clearAuthToken();
    }
    const message = data?.detail || data?.message || `Erro HTTP ${response.status}`;
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
  }
  return data;
}

async function uploadImage(file, kind) {
  if (!file) throw new Error('Selecione uma imagem.');
  const allowed = ['image/jpeg', 'image/png', 'image/webp'];
  if (!allowed.includes(file.type)) throw new Error('Use uma imagem JPG, PNG ou WebP.');
  if (file.size > 8 * 1024 * 1024) throw new Error('A imagem deve ter no máximo 8 MB.');

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
  return String(value).replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
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
