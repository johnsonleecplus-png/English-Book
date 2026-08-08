// 压缩 loading.png 到 1080x1920 JPEG-ish 质量, 让 PWA precache 能装下
import sharp from 'sharp'
import { readFileSync, writeFileSync } from 'node:fs'

const SRC = 'F:/26-English Book/tools/_loading_drafts/final-3-poster.png'
const DST = 'F:/26-English Book/public/loading.png'

const srcBuf = readFileSync(SRC)
const meta = await sharp(srcBuf).metadata()
console.log(`原图: ${meta.width}x${meta.height}  ${srcBuf.length} bytes`)

// 压缩策略: 1080x1920 宽屏, PNG palette 模式, 压缩级别 9
// PNG palette 适合黑白线稿, 可以从 2.18MB 压到 ~200KB
let img = sharp(srcBuf).resize({
  width: 1080,
  height: 1920,
  fit: 'cover',
})

// 用 png palette (适合纯黑白), 减少色板
const out = await img.png({
  compressionLevel: 9,
  palette: true,
  quality: 100,
  effort: 10,
}).toBuffer()

writeFileSync(DST, out)
console.log(`压缩后: ${out.length} bytes (${(out.length / 1024).toFixed(1)} KB)`)
console.log(`节省: ${((1 - out.length / srcBuf.length) * 100).toFixed(1)}%`)
