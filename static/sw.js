// PWA Service Worker (Cache & Offline Support for Study Planner)
const CACHE_NAME = 'study-planner-cache-v2';
const STATIC_ASSETS = [
  '/',
  '/static/css/style.css?v=20261005_lib_v4',
  '/static/js/app.js?v=20261005_lib_v4',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/icon.svg'
];

// 1. 설치 (Install): 핵심 정적 에셋 캐싱
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// 2. 활성화 (Activate): 이전 버전 캐시 정리
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// 3. 네트워크 요청 처리 (Fetch)
self.addEventListener('fetch', (event) => {
  // 플랜 생성 POST 요청(/generate)은 항상 실시간 네트워크로 전송
  if (event.request.method !== 'GET' || event.request.url.includes('/generate')) {
    return;
  }

  // 네트워크 우선(Network-First), 오프라인 시 캐시 폴백
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response && response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        return caches.match(event.request);
      })
  );
});
