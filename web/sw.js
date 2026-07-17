const CACHE_NAME = "vaisnava-calendar-v1";
const ASSETS = [
  "./",
  "./index.html",
  "./css/styles.css",
  "./js/app.js",
  "./manifest.json",
  "https://mahasoftware.fr/vaisnavacalendar/favicon.png"
];

// Install service worker and cache assets
self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate and remove old caches
self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch network request: Cache-first for static assets, network-only/fallback for API
self.addEventListener("fetch", e => {
  const url = e.request.url;
  
  // Skip caching API requests
  if (url.includes("/calendar") || url.includes("/find-location") || url.includes("/search-event") || url.includes("/ping") || url.includes("/countries")) {
    e.respondWith(
      fetch(e.request).catch(err => {
        console.log("Network request failed for API: ", url);
        return new Response(JSON.stringify({ error: "Offline" }), {
          status: 503,
          headers: { "Content-Type": "application/json" }
        });
      })
    );
    return;
  }
  
  // Cache-first for static local files
  e.respondWith(
    caches.match(e.request).then(cachedResponse => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(e.request).then(networkResponse => {
        if (!networkResponse || networkResponse.status !== 200) {
          return networkResponse;
        }
        
        // Cache the cloned response
        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then(cache => {
          cache.put(e.request, responseToCache);
        });
        return networkResponse;
      });
    })
  );
});
