const CACHE_NAME = 'catalogo-digital-v24-7-5';
const APP_SHELL = [
  './', './index.html', './loja.html', './admin.html', './super-admin.html',
  './agendamento.html', './cliente.html', './acompanhar.html', './privacidade.html', './termos.html',
  './css/style.css', './css/design-system.css', './css/premium-polish.css', './css/store-premium.css', './css/admin-premium.css', './css/super-admin-premium.css', './css/customer-portal.css', './js/ui-system.js', './js/runtime-config.js', './js/shared/dom-utils.js', './js/api.js', './js/loja.js', './js/admin.js', './js/super-admin.js', './js/agendamento.js', './js/cliente.js', './js/acompanhamento.js',
  './manifest.webmanifest', './icons/app-icon.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return;
  event.respondWith(fetch(request).then(response => {
    const copy = response.clone();
    caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
    return response;
  }).catch(() => caches.match(request).then(hit => hit || caches.match('./index.html'))));
});
