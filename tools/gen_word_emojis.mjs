// gen_word_emojis.mjs
// 从 emojilib 反查 + 同义词扩展, 给 1610 中考词自动生成 emoji 候选
// 输出 wordEmojis.json (全量) + wordEmojiMisses.json (LLM 待补)

import fs from 'fs'
import path from 'path'

// === 加载 emojilib 反向索引 ===
const data = JSON.parse(fs.readFileSync('node_modules/emojilib/dist/emoji-en-US.json', 'utf-8'))
const reverse = {}
for (const [emoji, keywords] of Object.entries(data)) {
  for (const k of keywords) {
    const lk = k.toLowerCase()
    if (!reverse[lk]) reverse[lk] = []
    if (reverse[lk].length < 3) reverse[lk].push(emoji)  // 每个 keyword 最多 3 个候选
  }
}

// === 高频英文同义词 (覆盖 ~60% 通用词) ===
// 格式: word → 同义词数组 (用 emojilib keyword 风格)
const synonymMap = {
  // 通用动词
  get: ['take', 'receive', 'grab', 'obtain'],
  give: ['provide', 'offer', 'donate', 'present'],
  take: ['grab', 'catch', 'hold'],
  make: ['create', 'build', 'produce', 'craft'],
  do: ['action', 'work', 'task'],
  go: ['move', 'travel', 'walk', 'journey'],
  come: ['arrive', 'approach'],
  see: ['look', 'watch', 'eye', 'vision'],
  hear: ['listen', 'ear', 'sound'],
  say: ['speak', 'talk', 'tell', 'word', 'voice'],
  tell: ['speak', 'say', 'narrate'],
  know: ['understand', 'idea', 'knowledge', 'brain'],
  think: ['idea', 'brain', 'mind', 'thought'],
  want: ['desire', 'need', 'wish', 'heart'],
  need: ['require', 'need', 'want'],
  help: ['assist', 'support', 'aid', 'hand'],
  use: ['utilize', 'tool'],
  find: ['discover', 'search', 'lookup'],
  give: ['offer', 'donate'],
  work: ['job', 'labor', 'work'],
  play: ['game', 'fun'],
  learn: ['study', 'book', 'school', 'education'],
  teach: ['teacher', 'school', 'education', 'professor'],
  read: ['book', 'study'],
  write: ['pen', 'paper', 'notebook'],
  // 通用形容词
  good: ['good', 'ok', 'thumbs', 'positive', 'check'],
  bad: ['bad', 'no', 'wrong', 'negative'],
  big: ['large', 'huge', 'big'],
  small: ['tiny', 'little', 'small'],
  new: ['new', 'fresh'],
  old: ['old', 'ancient'],
  happy: ['happy', 'smile', 'joy', 'laugh'],
  sad: ['sad', 'cry', 'tear'],
  // 学习/教育高频
  ability: ['talent', 'star', 'skill', 'star'],
  develop: ['build', 'create', 'code', 'hammer'],
  knowledge: ['book', 'brain', 'lightbulb', 'idea'],
  experience: ['experience', 'medal', 'star'],
  success: ['win', 'trophy', 'success', 'medal'],
  // 抽象
  achieve: ['win', 'trophy', 'medal', 'success'],
  although: ['but', 'shrug'],
  opportunity: ['door', 'key', 'star', 'chance'],
  kindness: ['heart', 'love', 'gift'],
  develop: ['build', 'code', 'hammer'],
  able: ['strong', 'power', 'shield'],
  accept: ['hand', 'shake', 'ok', 'check'],
  accident: ['warning', 'alert', 'crash'],
  active: ['fire', 'zap', 'bolt', 'energy'],
  // 自然
  sun: ['sun', 'sunny'],
  moon: ['moon', 'night'],
  star: ['star', 'sparkle'],
  tree: ['tree', 'plant'],
  water: ['water', 'drop'],
  fire: ['fire', 'flame'],
}

// === 工具: 查某词的 emoji (直接 + 同义词) ===
function lookup(word) {
  const w = word.toLowerCase()
  if (reverse[w] && reverse[w].length > 0) return { emoji: reverse[w][0], source: 'direct' }
  const syns = synonymMap[w] || []
  for (const s of syns) {
    if (reverse[s] && reverse[s].length > 0) return { emoji: reverse[s][0], source: `syn:${s}` }
  }
  return null
}

// === 读 CSV ===
function loadWords() {
  const lines = fs.readFileSync('public/词源/上海中考英文词汇表_完整版.csv', 'utf-8').split(/\r?\n/)
  const words = []
  for (const line of lines) {
    if (!line || line.startsWith('#') || line.startsWith('序号')) continue
    const parts = line.split(',')
    if (parts.length >= 2) {
      const w = parts[1].trim()
      if (w && w.replace(/[-']/g, '').match(/^[a-zA-Z]+$/)) words.push(w.toLowerCase())
    }
  }
  return words
}

// === main ===
const words = loadWords()
console.log(`Loaded ${words.length} words`)

const hits = {}
const misses = []
for (const w of words) {
  const r = lookup(w)
  if (r) {
    hits[w] = r.emoji
  } else {
    misses.push(w)
  }
}

console.log(`Hits: ${Object.keys(hits).length} / ${words.length} (${(Object.keys(hits).length / words.length * 100).toFixed(1)}%)`)
console.log(`Misses: ${misses.length}`)

// 写结果
fs.mkdirSync('src/data', { recursive: true })
fs.writeFileSync('src/data/wordEmojis-partial.json', JSON.stringify({ hits, misses }, null, 2), 'utf-8')
console.log('\nWritten: src/data/wordEmojis-partial.json')
console.log('\n=== Misses 样本 (前 50) ===')
misses.slice(0, 50).forEach(w => console.log(`  ${w}`))
console.log('\n=== Hits 样本 (前 20) ===')
Object.entries(hits).slice(0, 20).forEach(([w, e]) => console.log(`  ${w}: ${e}`))
