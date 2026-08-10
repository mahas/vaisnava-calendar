const CACHE_NAME = "vaisnava-calendar-v18";
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

// Fetch network request: Network-first for code/HTML, network-only/fallback for API, cache-first for assets
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

  // Network-first for core JS and HTML files to ensure instant updates
  if (url.includes("js/app.js") || url.endsWith("/index.html") || url.endsWith("/vaisnavacalendar/")) {
    e.respondWith(
      fetch(e.request).then(networkResponse => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(e.request, responseToCache));
        }
        return networkResponse;
      }).catch(() => caches.match(e.request))
    );
    return;
  }

  // Cache-first for other static assets (styles, icons, manifest)
  e.respondWith(
    caches.match(e.request).then(cachedResponse => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(e.request).then(networkResponse => {
        if (!networkResponse || networkResponse.status !== 200) {
          return networkResponse;
        }

        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then(cache => {
          cache.put(e.request, responseToCache);
        });
        return networkResponse;
      });
    })
  );
});
