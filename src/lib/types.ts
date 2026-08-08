// Core types for English Book (Phase 1: SM-2 + IndexedDB)

// 5 学习模式 (与 App.tsx 原有定义保持一致, 不引入 Phase 6 模式)
export type Mode = 'image' | 'en2cn' | 'cn2en' | 'listen' | 'mix'

// 3 档评分
export type Grade = 'again' | 'hard' | 'good'

// 单词卡 (idb cards 表一行)
export interface Card {
  id: string              // word.toLowerCase() — 词条唯一标识
  word: string
  pos: string             // 词性
  cn: string              // 中文释义
  example: string         // 例句
  // SM-2 状态
  ef: number              // easiness factor, 初始 2.5, 最低 1.3
  interval: number        // 下次复习间隔 (天), 0 = 新词尚未首评
  reps: number            // 连续答对次数
  due: number             // 下次 due 时间戳 (ms)
  firstSeen: number       // 首次见到时间, 0 = 还没背过
  createdAt: number       // 入库时间
  // Leech 检测 (层 3): 连续 again 太多 → 标记难词, 每天强制复习
  isLeech?: boolean       // 难词标记
  lapseStreak?: number    // 连续 again 次数, >= 5 标 leech
}

// 一次评分记录 (idb reviews 表一行)
export interface Review {
  id?: number             // auto-increment
  cardId: string
  sessionId: string
  grade: Grade
  prevEf: number
  prevInterval: number
  prevReps: number
  reviewedAt: number      // 时间戳 (ms)
}

// 单例 settings 表 (idb settings 表, keyPath='key', 主行 key='main')
export interface Settings {
  key: 'main'             // singleton
  dailyNewTarget: number  // 每日最多新词数, 默认 15 (新词引入节奏, SM-2 控复习)
  newRatio: number        // (deprecated, 保留兼容, 已不用) 新词占比 (0-1)
  seededAt: number        // seed 时间戳, 0 = 未 seed
}

// 一次学习 session (idb sessions 表, P1.5)
export interface Session {
  id: string              // 用 YYYY-MM-DD 当 key (一天一个 session)
  startedAt: number
  endedAt: number | null  // null = active
  targetCount: number
  completedCount: number
  reviewsCount: number
  newCount: number
  date: string            // YYYY-MM-DD (24h 续 session 时会被更新)
}
