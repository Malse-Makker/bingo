// Minimal service worker: makes the app installable and keeps the static shell
// available offline. Pages themselves are always fetched from the network, so
// the game state is never stale.

var CACHE = "bingo-v1";
var SHELL = [
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/js/spel.js",
  "/static/img/icon-192.png",
  "/static/img/icon-512.png",
  "/static/fontawesome/css/fontawesome.min.css",
  "/static/fontawesome/css/solid.min.css",
  "/static/fontawesome/webfonts/fa-solid-900.woff2",
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (cache) {
      return cache.addAll(SHELL);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (namen) {
      return Promise.all(
        namen.map(function (naam) {
          return naam === CACHE ? null : caches.delete(naam);
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", function (event) {
  var request = event.request;
  if (request.method !== "GET") return;

  var url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Static assets: cache first. Everything else: straight to the network.
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(request).then(function (hit) {
        return hit || fetch(request);
      })
    );
  }
});
