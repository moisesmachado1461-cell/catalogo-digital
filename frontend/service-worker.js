const CACHE_NAME = 'catalogo-digital-v18';
const APP_SHELL = [
  './', './index.html', './loja.html', './admin.html', './super-admin.html',
  './agendamento.html', './privacidade.html', './termos.html',
  './css/style.css', './js/runtime-config.js', './js/api.js', './js/loja.js', './js/admin.js', './js/super-admin.js', './js/agendamento.js',
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
