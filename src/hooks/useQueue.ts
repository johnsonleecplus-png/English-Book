import { useCallback, useEffect, useRef, useState } from 'react'
import type { Grade } from '../lib/types'
import { applyGrade, buildTodayQueue, type QueueEntry } from '../lib/queue'
import { ensureSeeded } from '../lib/seed'

// SM-2 session 内重复参数 (Johnson 决策 2026-08-04)
const AGAIN_INTERVAL = 5   // again 后, 隔 5 张再出
const HARD_INTERVAL = 10   // hard 后, 隔 10 张再出
// "直到 good 才放过" — 不设上限, 错了就一直重出

/** 一条待重出的卡 (在内存里维护, 不写 IDB) */
interface PendingReview {
  cardId: string
  entry: QueueEntry
  interval: number  // 倒计时, 每次 advance -1, 0 = 该出
  repeatCount: number  // 已重出次数 (用于未来扩展, 当前未设上限)
  lastGrade: 'again' | 'hard'
}

export interface UseQueueResult {
  loading: boolean
  entries: QueueEntry[]
  idx: number
  current: QueueEntry | null
  finished: boolean
  total: number
  completed: number
  pendingCount: number  // 当前 pending 数 (UI 显示 "还有 N 张会回来")
  /** 评分: 写库 + 更新 entry + 处理 pendingReviews */
  rate: (grade: Grade, sessionId: string) => Promise<void>
  /** 前进到下一张 (rate 之后 ~600ms 调). 会触发 pending 检查. */
  advance: () => void
  /** 重新拉 queue (用户点「再来 X 个新词」时用) */
  reload: (extraNew?: number) => Promise<void>
}

/** 管理今日 queue 的 hook. 首次挂载会 ensureSeeded + buildTodayQueue.
 *  加 pendingReviews 机制: again 后 5 张重出, hard 后 10 张重出, 错了就一直重出直到 good.
 *  pending 是内存态, 不写 IDB, 不影响 SM-2 due 字段 (SM-2 仍按天调度, pending 只是当天内强制重出).
 */
export function useQueue(): UseQueueResult {
  const [entries, setEntries] = useState<QueueEntry[]>([])
  const [idx, setIdx] = useState(0)
  const [pendingReviews, setPendingReviews] = useState<PendingReview[]>([])
  const [loading, setLoading] = useState(true)
  // ref guard: 阻止 React 19 strict mode 双调 useEffect 导致 queue 重复追加
  const initialLoadedRef = useRef(false)
  // pending 实时镜像 (避开 useCallback 闭包陷阱: CardView setTimeout 600ms 跑的是点击时的 advance,
  // 那时 pendingReviews 还没 push 进去。用 ref 同步最新值, advance 内读 ref)
  const pendingRef = useRef<PendingReview[]>([])
  // entries 实时镜像 (同样原因: advance 算 insertAt 用最新 entries)
  const entriesRef = useRef<QueueEntry[]>([])
  // idx 实时镜像
  const idxRef = useRef(0)

  const reload = useCallback(async (extraNew: number = 0) => {
    setLoading(true)
    setPendingReviews([])  // reload 时清 pending (新 session 开始)
    await ensureSeeded()
    const q = await buildTodayQueue(Date.now(), extraNew)
    setEntries(prev => {
      // 首次加载: prev=[] (或 stale), 直接替换
      if (prev.length === 0) return q
      // 后续 reload (用户点「再来 X 个新词」): 追加不在 prev 的新卡
      const seen = new Set(prev.map(e => e.card.id))
      const remaining = q.filter(e => !seen.has(e.card.id))
      return [...prev, ...remaining]
    })
    setLoading(false)
  }, [])

  useEffect(() => {
    if (initialLoadedRef.current) return
    initialLoadedRef.current = true
    void reload()
  }, [reload])

  // 同步 ref (advance 内部读 ref 避开闭包陷阱)
  useEffect(() => { pendingRef.current = pendingReviews }, [pendingReviews])
  useEffect(() => { entriesRef.current = entries }, [entries])
  useEffect(() => { idxRef.current = idx }, [idx])

  const rate = useCallback(
    async (grade: Grade, sessionId: string) => {
      const cur = entries[idx]
      if (!cur) return
      const updated = await applyGrade(cur.card, grade, sessionId)
      const updatedEntry: QueueEntry = { card: updated, isNew: cur.isNew }
      setEntries(prev => prev.map((e, i) => (i === idx ? updatedEntry : e)))

      // === Pending reviews 处理 ===
      if (grade === 'again') {
        setPendingReviews(prev => {
          // 移除旧的同 cardId (如果有), 推入新的 (重置 interval + repeatCount)
          const filtered = prev.filter(p => p.cardId !== updated.id)
          return [
            ...filtered,
            {
              cardId: updated.id,
              entry: { ...updatedEntry, isNew: false },  // 重出不再是新词
              interval: AGAIN_INTERVAL,
              repeatCount: 0,
              lastGrade: 'again',
            },
          ]
        })
      } else if (grade === 'hard') {
        setPendingReviews(prev => {
          const filtered = prev.filter(p => p.cardId !== updated.id)
          return [
            ...filtered,
            {
              cardId: updated.id,
              entry: { ...updatedEntry, isNew: false },
              interval: HARD_INTERVAL,
              repeatCount: 0,
              lastGrade: 'hard',
            },
          ]
        })
      } else {
        // good: 从 pending 彻底移除 (记住啦, 不再回来)
        setPendingReviews(prev => prev.filter(p => p.cardId !== updated.id))
      }
    },
    [entries, idx],
  )

  const advance = useCallback(() => {
    // === 触发 pending 检查 ===
    // 读 ref 拿最新值 (避开 useCallback 闭包陷阱)
    const currentPending = pendingRef.current
    const currentEntries = entriesRef.current
    const currentIdx = idxRef.current
    const remaining: PendingReview[] = []
    const due: PendingReview[] = []
    for (const p of currentPending) {
      const next = { ...p, interval: p.interval - 1, repeatCount: p.repeatCount + 1 }
      if (next.interval <= 0) due.push(next)
      else remaining.push(next)
    }
    if (due.length > 0) {
      const dueEntries = due.map(p => p.entry)
      const insertAt = Math.min(currentIdx + 1, currentEntries.length)
      setEntries([...currentEntries.slice(0, insertAt), ...dueEntries, ...currentEntries.slice(insertAt)])
    }
    setPendingReviews(remaining)
    setIdx(i => i + 1)
  }, [])  // 不依赖任何 state, 内部读 ref

  const finished = idx >= entries.length
  return {
    loading,
    entries,
    idx,
    current: finished ? null : entries[idx] ?? null,
    finished,
    total: entries.length,
    completed: idx,
    pendingCount: pendingReviews.length,
    rate,
    advance,
    reload,
  }
}
