const CACHE_NAME = 'screenshot-organizer-v2';
const DYNAMIC_CACHE_NAME = 'site-dynamic-v2';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  'https://cdn.tailwindcss.com?plugins=forms,container-queries',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
  'https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap'
];

self.addEventListener('install', (evt) => {
  evt.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('Pre-caching offline pages');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (evt) => {
  evt.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (key !== CACHE_NAME && key !== DYNAMIC_CACHE_NAME) {
          console.log('Removing old cache', key);
          return caches.delete(key);
        }
      }));
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (evt) => {
  const url = new URL(evt.request.url);

  // 1. Dynamic Content (API & Images) - Network First, then Cache
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/images/')) {
    evt.respondWith(
      fetch(evt.request)
        .then((fetchRes) => {
          return caches.open(DYNAMIC_CACHE_NAME).then((cache) => {
            cache.put(evt.request.url, fetchRes.clone());
            return fetchRes;
          });
        })
        .catch(() => {
          // If offline, check cache
          return caches.match(evt.request).then((cachedRes) => {
            if (cachedRes) {
              return cachedRes;
            }
            // Fallback for API could go here (e.g. return empty JSON)
            if (url.pathname.startsWith('/api/stats')) {
               // Return a basic fallback stats object so the dashboard doesn't crash
               return new Response(JSON.stringify({
                   total_photos: '?', storage_usage: 'Offline', categories: [], insights: []
               }), { headers: { 'Content-Type': 'application/json' }});
            }
          });
        })
    );
    return;
  }

  // 2. Static Assets - Cache First, then Network
  evt.respondWith(
    caches.match(evt.request).then((cacheRes) => {
      return cacheRes || fetch(evt.request).then((fetchRes) => {
        return caches.open(DYNAMIC_CACHE_NAME).then((cache) => {
          cache.put(evt.request.url, fetchRes.clone());
          return fetchRes;
        });
      });
    })
  );
});
