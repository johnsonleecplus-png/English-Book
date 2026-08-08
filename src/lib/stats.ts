import { getDB } from './db'
import { getSettings } from './queue'
import { dateKey } from './session'
import type { Session } from './types'

export interface Stats {
  todayNewTarget: number  // 今日新词上限
  todayNewDone: number    // 今日新词已学 (session.newCount)
  todayReviewDone: number // 今日复习已学 (session.reviewsCount)
  todayTotalDone: number  // 今日总完成 (todayNewDone + todayReviewDone)
  totalLearned: number    // 累计至少评过 1 次的卡 (reps >= 1)
  streak: number          // 连续打卡天数
}

export interface HeatmapCell {
  date: string      // YYYY-MM-DD
  count: number     // 该日 completedCount 总和 (跨多个 session)
  isToday: boolean  // 是否今天
  isFuture: boolean // 未来日期 (尚未到)
}

export interface HeatmapWeek {
  days: (HeatmapCell | null)[]  // 7 个: 周一..周日 (null = 该格子不属于这个 grid, 比如最早列的"前面")
  weekIndex: number             // 0 = 最左, weeks-1 = 最右 (今天所在周)
}

export interface Heatmap {
  weeks: HeatmapWeek[]          // 7 周 = 49 天, 最后一格是今天
  maxCount: number              // 49 天里最大 count, 用于颜色强度归一化
  totalLast7: number            // 最近 7 天总完成 (不算今天)
  totalAll: number              // 49 天总完成
}

/** 取首页要展示的统计 */
export async function getStats(): Promise<Stats> {
  const db = await getDB()
  const settings = await getSettings()

  // 累计已学 (reps >= 1 表示至少评过一次)
  const allCards = await db.getAll('cards')
  const totalLearned = allCards.filter(c => c.reps >= 1).length

  // 今日统计 (合并所有今日 session)
  const today = dateKey()
  const todays = await db.getAllFromIndex('sessions', 'by-date', today)
  const todayNewDone = todays.reduce((sum, s) => sum + s.newCount, 0)
  const todayReviewDone = todays.reduce((sum, s) => sum + s.reviewsCount, 0)
  const todayTotalDone = todays.reduce((max, s) => Math.max(max, s.completedCount), 0)

  // 连续打卡: 从今天往前数, 有 completedCount>0 的天数
  const sessions = await db.getAll('sessions')
  const daysWithProgress = new Set(
    sessions.filter(s => s.completedCount > 0).map(s => s.date),
  )
  let streak = 0
  const d = new Date()
  // 今天还没有 progress 的话, streak 仍要从"昨天往前"算 (允许今天还没开始)
  if (!daysWithProgress.has(dateKey(d.getTime()))) {
    d.setDate(d.getDate() - 1)
  }
  while (daysWithProgress.has(dateKey(d.getTime()))) {
    streak += 1
    d.setDate(d.getDate() - 1)
  }

  return {
    todayNewTarget: settings.dailyNewTarget,
    todayNewDone,
    todayReviewDone,
    todayTotalDone,
    totalLearned,
    streak,
  }
}

/**
 * 7 周热力图 (49 天), 类似 GitHub contribution graph.
 * - 7 行 (周一..周日) x 7 列 (周)
 * - 今天 = 最右列的某一行
 * - 用 sessions 表的 completedCount 累加 (跨多个 session)
 *
 * 返回结构: weeks[7][7] (Cell | null)
 * - null = 越界 (最早一列的"前面"几天, 比如最左列如果对齐到周一, 周日就在 null 位置)
 *   实际: 我们用 getDay() = 0 (Sun) 转换: 周一=0, 周日=6
 *   起始日 = 今天 - 6*7 = 41 天前, 把它对齐到周一
 */
export async function getHeatmap(): Promise<Heatmap> {
  const db = await getDB()
  const todayStr = dateKey()
  const todayDate = new Date()

  // 起始日: 找到 41 天前那个周一
  // 今天 - 41 天 = 起点 (这周一), 然后回退到周一
  const startDate = new Date(todayDate)
  startDate.setDate(startDate.getDate() - 41)  // 42 天前
  // 把它对齐到周一
  const startDow = (startDate.getDay() + 6) % 7
  startDate.setDate(startDate.getDate() - startDow)

  // 取所有 49 天
  const days: HeatmapCell[] = []
  for (let i = 0; i < 49; i++) {
    const d = new Date(startDate)
    d.setDate(d.getDate() + i)
    const dk = dateKey(d.getTime())
    days.push({ date: dk, count: 0, isToday: dk === todayStr, isFuture: dk > todayStr })
  }

  // 一次拉所有 sessions, 走 by-date 索引
  // 但 by-date 是 single key index, 49 次 getAllFromIndex 较慢
  // 改: 一次性 getAll, 自己 group
  const allSessions = await db.getAll('sessions')
  const byDate = new Map<string, number>()
  for (const s of allSessions) {
    byDate.set(s.date, (byDate.get(s.date) ?? 0) + s.completedCount)
  }
  for (const cell of days) {
    cell.count = byDate.get(cell.date) ?? 0
  }

  // 转成 7 周 x 7 天的结构
  const weeks: HeatmapWeek[] = []
  for (let w = 0; w < 7; w++) {
    const weekDays: (HeatmapCell | null)[] = []
    for (let d = 0; d < 7; d++) {
      const idx = w * 7 + d
      weekDays.push(idx < days.length ? days[idx] : null)
    }
    weeks.push({ days: weekDays, weekIndex: w })
  }

  // maxCount (不算未来的)
  const pastDays = days.filter(c => !c.isFuture)
  const maxCount = pastDays.reduce((m, c) => Math.max(m, c.count), 0)

  // 最近 7 天总完成 (含今天, 跟用户体感一致)
  const totalLast7 = days.filter(c => !c.isFuture).slice(-7).reduce((sum, c) => sum + c.count, 0)
  // 49 天总完成
  const totalAll = days.filter(c => !c.isFuture).reduce((sum, c) => sum + c.count, 0)

  return { weeks, maxCount, totalLast7, totalAll }
}

export interface HistoryItem {
  session: Session
  goodCount: number   // 该 session 评分 good 的次数
  hardCount: number   // hard 次数
  againCount: number  // again 次数
  goodPct: number     // 0-100, good / (good+hard+again)
}

/**
 * 历史 sessions 列表, 按日期降序 (最近在前).
 * 从 reviews 表算每个 session 的 good/hard/again 分布.
 */
export async function getHistoryList(limit?: number): Promise<HistoryItem[]> {
  const db = await getDB()
  const allSessions = await db.getAll('sessions')
  // 排序: date 降序, 相同 date 按 startedAt 降序
  allSessions.sort((a, b) => {
    if (a.date !== b.date) return a.date < b.date ? 1 : -1
    return b.startedAt - a.startedAt
  })
  const sliced = limit ? allSessions.slice(0, limit) : allSessions
  if (sliced.length === 0) return []

  // 一次拉所有 reviews, 按 sessionId 索引
  const allReviews = await db.getAll('reviews')
  const reviewsBySession = new Map<string, { good: number; hard: number; again: number }>()
  for (const r of allReviews) {
    const s = reviewsBySession.get(r.sessionId) ?? { good: 0, hard: 0, again: 0 }
    s[r.grade] += 1
    reviewsBySession.set(r.sessionId, s)
  }

  return sliced.map(s => {
    const c = reviewsBySession.get(s.id) ?? { good: 0, hard: 0, again: 0 }
    const total = c.good + c.hard + c.again
    const goodPct = total === 0 ? 0 : Math.round((c.good / total) * 100)
    return {
      session: s,
      goodCount: c.good,
      hardCount: c.hard,
      againCount: c.again,
      goodPct,
    }
  })
}
