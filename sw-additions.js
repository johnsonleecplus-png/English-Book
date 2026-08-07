// 手动加 skipWaiting + clientsClaim, 因为 vite-plugin-pwa v1.3.0 不支持 workbox.skipWaiting
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));
