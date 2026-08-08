import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'icons.svg'],
      manifest: {
        name: 'English Book · 上海中考词汇',
        short_name: 'English Book',
        description: '上海中考英文词汇 PWA · SM-2 间隔重复 · 完全离线',
        theme_color: '#1d1d1f',
        background_color: '#f5f5f7',
        display: 'standalone',
        orientation: 'portrait',
        lang: 'zh-CN',
        start_url: '/',
        scope: '/',
        icons: [
          {
            src: '/icons/pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: '/icons/pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any',
          },
          {
            src: '/icons/pwa-maskable-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable',
          },
        ],
      },
      workbox: {
        // 预缓存: 整个 app shell (HTML/JS/CSS/字体/icons/audio 列表)
        globPatterns: ['**/*.{js,css,html,svg,png,ico,webp,woff,woff2,ttf,eot,mp3}'],
        // 提升单文件上限: loading.png 866KB + audio 单文件 5-9KB, 给 5MB 留 buffer
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
        // 音频文件大 (5-9KB × 1716 ≈ 12MB), 但用 cache-first 离线播放必需
        runtimeCaching: [
          {
            urlPattern: /\/audio\/.*\.(mp3|wav)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'audio-cache',
              expiration: { maxEntries: 2000, maxAgeSeconds: 60 * 60 * 24 * 365 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
      devOptions: {
        enabled: true,  // dev 也能测 PWA (但 service worker 需 reload)
        type: 'module',
      },
    }),
  ],
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
})
