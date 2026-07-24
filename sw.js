/**
 * sw.js — 成大榕園 PWA Service Worker
 * --------------------------------------------------
 * 策略：
 *  - App Shell（index.html、manifest、icons）：Cache First，離線可直接開啟
 *  - 外部 CDN 資源（Tailwind、Vue、字型、圖示庫、Unsplash 圖片）：
 *    Stale-While-Revalidate，先回快取加速顯示，同時背景更新快取
 *  - 找不到快取又離線時，導覽請求會回傳 index.html 作為離線備援頁面
 */

const CACHE_VERSION = "v1";
const APP_SHELL_CACHE = `ncku-banyan-shell-${CACHE_VERSION}`;
const RUNTIME_CACHE = `ncku-banyan-runtime-${CACHE_VERSION}`;

// 需要在安裝階段預先快取的核心檔案（App Shell）
const APP_SHELL_FILES = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icons/icon-72x72.png",
  "./icons/icon-96x96.png",
  "./icons/icon-128x128.png",
  "./icons/icon-144x144.png",
  "./icons/icon-152x152.png",
  "./icons/icon-192x192.png",
  "./icons/icon-384x384.png",
  "./icons/icon-512x512.png",
  "./icons/icon-maskable-512x512.png",
  "./icons/apple-touch-icon.png",
  "./icons/favicon-16x16.png",
  "./icons/favicon-32x32.png",
  "./icons/favicon.ico",
];

// ------------------------------
// install：預先快取 App Shell
// ------------------------------
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(APP_SHELL_CACHE)
      .then((cache) => cache.addAll(APP_SHELL_FILES))
      .then(() => self.skipWaiting())
  );
});

// ------------------------------
// activate：清除舊版本快取
// ------------------------------
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter(
              (key) => key !== APP_SHELL_CACHE && key !== RUNTIME_CACHE
            )
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

// ------------------------------
// fetch：依請求類型套用不同快取策略
// ------------------------------
self.addEventListener("fetch", (event) => {
  const { request } = event;

  // 僅處理 GET 請求
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  const isSameOrigin = url.origin === self.location.origin;

  // 導覽請求（使用者直接開啟頁面/重新整理）：Network First，離線時退回快取的 index.html
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(APP_SHELL_CACHE).then((cache) => cache.put("./index.html", copy));
          return response;
        })
        .catch(() =>
          caches.match("./index.html", { cacheName: APP_SHELL_CACHE })
        )
    );
    return;
  }

  if (isSameOrigin) {
    // 同源靜態資源（App Shell）：Cache First
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          const copy = response.clone();
          caches.open(APP_SHELL_CACHE).then((cache) => cache.put(request, copy));
          return response;
        });
      })
    );
  } else {
    // 外部 CDN 資源（Tailwind CDN、Vue CDN、Google Fonts、Font Awesome、Unsplash）：
    // Stale-While-Revalidate
    event.respondWith(
      caches.open(RUNTIME_CACHE).then((cache) =>
        cache.match(request).then((cached) => {
          const networkFetch = fetch(request)
            .then((response) => {
              if (response && response.status === 200) {
                cache.put(request, response.clone());
              }
              return response;
            })
            .catch(() => cached);
          return cached || networkFetch;
        })
      )
    );
  }
});
