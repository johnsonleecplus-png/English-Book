import type { Card, Grade, Settings } from './types'
import { getDB } from './db'
import { schedule } from './scheduler'

const SETTINGS_KEY = 'main'

/** Fisher-Yates 原地洗牌 (返回新数组, 不改原数组顺序) */
function shuffle<T>(arr: T[]): T[] {
  const a = arr.slice()
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

/** 读 settings, 没有就用默认. 兼容老字段 dailyTarget. */
export async function getSettings(): Promise<Settings> {
  const db = await getDB()
  const s = await db.get('settings', SETTINGS_KEY)
  if (s) {
    // 老字段迁移: dailyTarget -> dailyNewTarget
    if ((s as unknown as Record<string, unknown>).dailyNewTarget === undefined) {
      const oldTarget = (s as unknown as Record<string, unknown>).dailyTarget as number | undefined
      const migrated: Settings = {
        ...s,
        dailyNewTarget: oldTarget ?? 15,
        newRatio: s.newRatio ?? 0.5,
      }
      delete (migrated as unknown as Record<string, unknown>).dailyTarget
      await db.put('settings', migrated)
      return migrated
    }
    return s
  }
  const fresh: Settings = {
    key: SETTINGS_KEY,
    dailyNewTarget: 15,
    newRatio: 0.5,
    seededAt: 0,
  }
  await db.put('settings', fresh)
  return fresh
}

/** 改每日新词目标 (用户在 confirm 屏确认后调用) */
export async function setDailyNewTarget(n: number): Promise<void> {
  const db = await getDB()
  const s = await getSettings()
  await db.put('settings', { ...s, dailyNewTarget: n })
}

export interface QueueEntry {
  card: Card
  isNew: boolean
}

/**
 * 构造今日 queue.
 * - 复习: ALL due cards (无上限, 想学多少学多少)
 * - 新词: 最多 dailyNewTarget 个 (避免一天引入太多)
 * - 总 queue 长度 = 全部复习 + 限额新词
 *
 * 参数 extraNew: 手动追加新词数 (用户点「再多 X 个新词」按钮)
 */
export async function buildTodayQueue(
  now: number = Date.now(),
  extraNew: number = 0,
): Promise<QueueEntry[]> {
  const db = await getDB()
  const settings = await getSettings()
  const newCap = Math.max(0, settings.dailyNewTarget + extraNew)

  // 复习: due <= now 且 reps > 0 (学过的卡)
  // 优先 Leech 词 (isLeech=true, 每天强制复习), 然后普通 due
  const dueCards = await db.getAllFromIndex('cards', 'by-due', IDBKeyRange.upperBound(now))
  const allReviews = dueCards.filter(c => c.reps > 0)
  const leechReviews = shuffle(allReviews.filter(c => c.isLeech))
  const normalReviews = shuffle(allReviews.filter(c => !c.isLeech))
  // Leech 词排在最前 (确保今日 queue 一开始就出, 给娃更多机会反复打)
  const reviews = [...leechReviews, ...normalReviews]

  // 新词: firstSeen === 0, 随机顺序
  const newCards = await db.getAllFromIndex('cards', 'by-firstSeen', IDBKeyRange.only(0))
  const news = shuffle(newCards).slice(0, newCap)

  return [
    ...reviews.map(card => ({ card, isNew: false } as QueueEntry)),
    ...news.map(card => ({ card, isNew: true } as QueueEntry)),
  ]
}

/**
 * 应用一次评分: 更新 card + 写 reviews 行.
 * 返回新 card, 调用方负责更新本地缓存.
 */
export async function applyGrade(
  card: Card,
  grade: Grade,
  sessionId: string,
  now: number = Date.now(),
): Promise<Card> {
  const db = await getDB()
  const prev = { ef: card.ef, interval: card.interval, reps: card.reps }
  const r = schedule(card, grade, now)
  const updated: Card = {
    ...card,
    ef: r.ef,
    interval: r.interval,
    reps: r.reps,
    due: r.due,
    firstSeen: card.firstSeen || now,
  }

  const tx = db.transaction(['cards', 'reviews'], 'readwrite')
  await tx.objectStore('cards').put(updated)
  await tx.objectStore('reviews').add({
    cardId: card.id,
    sessionId,
    grade,
    prevEf: prev.ef,
    prevInterval: prev.interval,
    prevReps: prev.reps,
    reviewedAt: now,
  })
  await tx.done

  return updated
}
