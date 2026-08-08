import type { Card } from './types'
// 词库进度: 4 档分类 + 剩余天数估算
// 复用 cards 表的 SM-2 字段, 不读 reviews 表 (一次 getAll 即可)

import { getDB } from './db'
import { getSettings } from './queue'

export interface Progress {
  /** 长期记忆稳定, reps>=3, ef>=2.5, interval>=21天 */
  mastered: number
  /** 还在 SM-2 收敛 (见过几次但 EF 还不高, 间隔中) */
  fuzzy: number
  /** 学过但 SM-2 还在拉锯 (EF 低或 头几次) */
  struggling: number
  /** 从未见过 (firstSeen=0) */
  unlearned: number
  /** 总卡数 = master + fuzzy + struggling + unlearned */
  total: number
  /** 按当前 dailyNewTarget 节奏, 走完 unlearned 需要的天数 (>=1) */
  daysLeft: number
}

/**
 * 4 档判定 (纯 cards 字段, 不读 reviews):
 * - 未学 (unlearned): firstSeen === 0
 * - 不会 (struggling): firstSeen > 0 && (reps < 3 || ef < 2.0)
 *   - "学过但还在挣扎": EF 很低, 或者还没拿到 3 次连击
 * - 模糊 (fuzzy): firstSeen > 0 && reps >= 3 && ef >= 2.0 && ef < 2.5
 *   - "见过几次, 间隔在 7-21 天, 还未稳定"
 * - 掌握 (mastered): firstSeen > 0 && reps >= 3 && ef >= 2.5
 *   - "EF >= 2.5, SM-2 视为稳定, 间隔 21+ 天"
 */
export async function getProgress(): Promise<Progress> {
  const db = await getDB()
  const all = await db.getAll('cards')
  const settings = await getSettings()

  let mastered = 0
  let fuzzy = 0
  let struggling = 0
  let unlearned = 0

  for (const c of all) {
    if (c.firstSeen === 0) {
      unlearned++
    } else if (c.reps < 3 || c.ef < 2.0) {
      struggling++
    } else if (c.ef < 2.5) {
      fuzzy++
    } else {
      mastered++
    }
  }

  const total = mastered + fuzzy + struggling + unlearned
  const dailyTarget = Math.max(1, settings.dailyNewTarget)
  const daysLeft = unlearned === 0 ? 0 : Math.ceil(unlearned / dailyTarget)

  return { mastered, fuzzy, struggling, unlearned, total, daysLeft }
}

/**
 * 获取需要复习的卡片 (fuzzy + struggling)
 * - 排除未学过的 (firstSeen === 0)
 * - 已掌握的不算 (reps >= 3 && ef >= 2.5)
 * - 用于设置页的"复习今日模糊/不会"按钮
 */
export async function getReviewableCards(): Promise<Card[]> {
  const db = await getDB()
  const all = await db.getAll('cards')
  return all.filter(c => {
    if (c.firstSeen === 0) return false  // 未学过, 不算复习
    return c.reps < 3 || c.ef < 2.5  // fuzzy (ef < 2.5) 或 struggling (reps < 3 || ef < 2.0)
  })
}