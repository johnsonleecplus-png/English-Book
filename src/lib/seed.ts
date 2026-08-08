import type { Card, Settings } from './types'
import { MOCK_WORDS } from './mockWords'
import { VOCAB } from '../data/vocabSeed'
import { getDB } from './db'

const SETTINGS_KEY = 'main'

const DEFAULT_SETTINGS: Omit<Settings, 'key'> = {
  dailyNewTarget: 15,
  newRatio: 0.5,  // deprecated, 保留兼容
  seededAt: 0,
}

/**
 * 首次启动把 MOCK_WORDS + VOCAB 灌进 IDB, 并写默认 settings.
 * 幂等: 如果 settings.seededAt > 0 AND cards count >= 100 就跳过.
 *
 * Phase 3 增强: 除了 MOCK 5 词, 还会从 vocabSeed.ts 灌入 1441 个真实词条.
 * 真实词条只在新卡场景下进入 queue, 每天 30 词 = 48 天首过.
 *
 * Phase 3.1 migration: 老用户 IDB 里有 dailyTarget 字段 (旧) + 只有 5 张 MOCK 卡, 需:
 *   1) settings 字段名迁移: dailyTarget -> dailyNewTarget
 *   2) backfill VOCAB 1441 (即使 seededAt > 0 也要做)
 *
 * Phase 3.2 扩展: VOCAB 扩到 1711 (43 缺词 + 227 词组). 始终遍历 VOCAB,
 *   已存在 (按 word.toLowerCase()) 则跳过 → 天然支持老用户 backfill, 不覆盖学习状态.
 *   无新用户 / 老用户都走这条路, seededAt 只标记"首次完成 seed"时间, 不再 short-circuit.
 */
export async function ensureSeeded(): Promise<void> {
  const db = await getDB()

  // 已有 settings 行则读出来
  let existing = await db.get('settings', SETTINGS_KEY)

  // Migration 1: 老字段名 dailyTarget -> dailyNewTarget
  if (existing && (existing as unknown as Record<string, unknown>).dailyNewTarget === undefined) {
    const oldTarget = (existing as unknown as Record<string, unknown>).dailyTarget as number | undefined
    const migrated: Settings = {
      ...existing,
      dailyNewTarget: oldTarget ?? 15,
      newRatio: existing.newRatio ?? 0.5,
    }
    // 删旧字段
    delete (migrated as unknown as Record<string, unknown>).dailyTarget
    await db.put('settings', migrated)
    existing = migrated
  }

  const cardCount = await db.count('cards')
  const isFreshUser = !existing || existing.seededAt === 0
  const isIncompleteSeed = cardCount < VOCAB.length + MOCK_WORDS.length

  // 否则: 1) 首次启动 OR 2) 老用户只 seed 了 MOCK 5 → 补 VOCAB
  const now = Date.now()
  const tx = db.transaction(['cards', 'settings'], 'readwrite')

  // 1) MOCK 5 词 (Phase 1 演示, 状态优先, 已存在则跳过)
  for (const w of MOCK_WORDS) {
    const card: Card = {
      id: w.word.toLowerCase(),
      word: w.word,
      pos: w.pos,
      cn: w.cn,
      example: w.example,
      ef: 2.5,
      interval: 0,
      reps: 0,
      due: now,
      firstSeen: 0,
      createdAt: now,
    }
    await tx.objectStore('cards').put(card)
  }

  // 2) 真实词表 1711 词 (Phase 3.2, 1441 单词 + 43 缺词 + 227 词组)
  // 始终遍历, 跳过已存在的 (MOCK 或老用户已 backfill 过的), 保留学习状态
  const cardsStore = tx.objectStore('cards')
  let realCount = 0
  for (const v of VOCAB) {
    const id = v.word.toLowerCase()
    // 已存在 (MOCK 或之前已灌) → 跳过, 保留学习状态
    const existingCard = await cardsStore.get(id)
    if (existingCard) continue

    const card: Card = {
      id,
      word: v.word,
      pos: v.pos,
      cn: v.cn,
      example: '',
      ef: 2.5,
      interval: 0,
      reps: 0,
      due: now,
      firstSeen: 0,
      createdAt: now,
    }
    await cardsStore.put(card)
    realCount++
  }

  // 写/补 settings
  const settings: Settings = existing
    ? { ...existing, seededAt: now }
    : { key: SETTINGS_KEY, ...DEFAULT_SETTINGS, seededAt: now }
  await tx.objectStore('settings').put(settings)

  await tx.done

  console.log(`[seed] MOCK ${MOCK_WORDS.length} + real ${realCount} = ${MOCK_WORDS.length + realCount} cards (was ${cardCount}, fresh=${isFreshUser}, incomplete=${isIncompleteSeed})`)
}

