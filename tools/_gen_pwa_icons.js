// gen-pwa-icons.mjs
// 把 public/favicon.svg 渲染成 192/512 PNG + maskable 图标 (用于 PWA manifest).
//
// maskable 要求核心内容在中心 80% 安全区, 所以用 padding (fit: contain + white bg).

import sharp from 'sharp'
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PUBLIC = join(__dirname, '..', 'public')
const svg = readFileSync(join(PUBLIC, 'favicon.svg'))
mkdirSync(join(PUBLIC, 'icons'), { recursive: true })

async function genPng(size, outName, opts = {}) {
  // opts.pad = true 时 (maskable), 加 padding 留安全区
  const target = opts.maskable ? Math.round(size * 0.8) : size
  const buf = await sharp(svg, { density: 384 })
    .resize(target, target, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .png()
    .toBuffer()
  const final = opts.maskable
    ? await sharp({ create: { width: size, height: size, channels: 4, background: { r: 255, g: 255, b: 255, alpha: 1 } } })
        .composite([{ input: buf, gravity: 'center' }])
        .png()
        .toBuffer()
    : buf
  const out = join(PUBLIC, 'icons', outName)
  writeFileSync(out, final)
  console.log(`  ${outName}  ${final.length} bytes`)
}

await genPng(192, 'pwa-192x192.png')
await genPng(512, 'pwa-512x512.png')
await genPng(512, 'pwa-maskable-512x512.png', { maskable: true })
await genPng(180, 'apple-touch-icon.png')  // iOS
console.log('done')
