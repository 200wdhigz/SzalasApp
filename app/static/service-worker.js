const CACHE_NAME = 'szalas-app-cache-v1';
const OFFLINE_URL = '/';

// Pliki do cache'owania przy instalacji
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/static/assets/js/themeToggle.js'
];

// Instalacja Service Workera
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
      .catch((err) => {
        console.error('Cache installation failed:', err);
      })
  );
  self.skipWaiting();
});

// Aktywacja Service Workera
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch - strategia Network First (zawsze próbuj pobrać z sieci)
self.addEventListener('fetch', (event) => {
  // Ignoruj requesty poza GET
  if (event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Jeśli sukces, zaktualizuj cache
        if (response && response.status === 200) {
          const responseToCache = response.clone();
          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(event.request, responseToCache);
            });
        }
        return response;
      })
      .catch(() => {
        // Jeśli brak sieci, spróbuj zwrócić z cache
        return caches.match(event.request)
          .then((response) => {
            if (response) {
              return response;
            }
            // Dla nawigacji zwróć stronę offline
            if (event.request.mode === 'navigate') {
              return caches.match(OFFLINE_URL);
            }
          });
      })
  );
});

