import type { Session } from './types'
import { getDB } from './db'

const RECOVER_WINDOW_MS = 24 * 60 * 60 * 1000  // 24h

/** YYYY-MM-DD 本地时区日期键 */
export function dateKey(now: number = Date.now()): string {
  const d = new Date(now)
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

/**
 * 取当前 active session.
 * 逻辑: 24h 内 startedAt 且 endedAt === null → 续.
 * 续上时把 date 字段更新到今天, id 也改成今天的 date key (旧行删除).
 *
 * 注意: 不再单独走"今天日期"快查路径, 因为单纯按 date === today 判断
 *       会把 25h 前的 session 误判为今天 active (只看 date, 不看时间).
 */
export async function getActiveSession(): Promise<Session | null> {
  const db = await getDB()
  const today = dateKey()
  const cutoff = Date.now() - RECOVER_WINDOW_MS

  const all = await db.getAll('sessions')
  const recoverable = all
    .filter(s => s.endedAt === null && s.startedAt >= cutoff)
    .sort((a, b) => b.startedAt - a.startedAt)

  if (recoverable.length === 0) return null

  // 续: 用今天的 date key 重建 (覆盖旧的 id)
  const old = recoverable[0]
  if (old.id === today) {
    return old  // 已经是今天的 id, 不用动
  }
  const renewed: Session = {
    ...old,
    id: today,
    date: today,
  }
  await db.put('sessions', renewed)
  // 旧的 id 行删掉, 避免同 startedAt 有两行 active
  await db.delete('sessions', old.id)
  return renewed
}

/** 开新 session (用今天日期做 id) */
export async function startSession(targetCount: number): Promise<Session> {
  const db = await getDB()
  const today = dateKey()
  const now = Date.now()

  const session: Session = {
    id: today,
    startedAt: now,
    endedAt: null,
    targetCount,
    completedCount: 0,
    reviewsCount: 0,
    newCount: 0,
    date: today,
  }
  await db.put('sessions', session)
  return session
}

/** 结束 session */
export async function endSession(sessionId: string): Promise<void> {
  const db = await getDB()
  const s = await db.get('sessions', sessionId)
  if (!s) return
  if (s.endedAt !== null) return  // 已结束
  s.endedAt = Date.now()
  await db.put('sessions', s)
}

/** 评分后 +1 session 计数 (内存也 +1) */
export async function bumpSessionStats(
  sessionId: string,
  isNew: boolean,
): Promise<Session | null> {
  const db = await getDB()
  const s = await db.get('sessions', sessionId)
  if (!s) return null
  s.completedCount += 1
  s.reviewsCount += 1
  if (isNew) s.newCount += 1
  await db.put('sessions', s)
  return s
}
