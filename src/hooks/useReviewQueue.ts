// 复习模式专用 hook (Johnson 决策 2026-08-08)
// - 初始队列: 所有需要复习的卡片 (fuzzy + struggling)
// - 评分 good → 标记完成, 不再循环
// - 评分 again/hard → 不规则刷新 (当前位置后 1-5 张位置)
// - 结束条件: 所有原始卡片都评过 good

import { useCallback, useEffect, useRef, useState } from 'react'
import type { Card, Grade } from '../lib/types'
import { applyGrade } from '../lib/queue'

export interface ReviewEntry {
  card: Card
}

export interface UseReviewQueueResult {
  loading: boolean
  entries: ReviewEntry[]
  idx: number
  current: ReviewEntry | null
  finished: boolean
  total: number               // 当前队列长度 (含复插的)
  initialCount: number        // 初始卡片数 (用于显示进度)
  completed: number           // 已标记 good 的卡片数
  rate: (grade: Grade) => Promise<void>
  advance: () => void
}

export function useReviewQueue(initialCards: Card[]): UseReviewQueueResult {
  const [entries, setEntries] = useState<ReviewEntry[]>([])
  const [idx, setIdx] = useState(0)
  const [loading, setLoading] = useState(true)
  const [completedCount, setCompletedCount] = useState(0)
  // 已掌握的卡片 ID 集合
  const [doneIds, setDoneIds] = useState<Set<string>>(new Set())

  // refs: 绕过 useCallback 闭包陷阱 (advance 在 rate 完成后被调用, 需读最新 entries/idx)
  const entriesRef = useRef<ReviewEntry[]>([])
  const idxRef = useRef(0)

  // 初始卡片 ID 集合 (用于判断是否全部完成)
  const initialIdsRef = useRef<Set<string>>(new Set())

  // 初始化
  useEffect(() => {
    const initial = initialCards.map(c => ({ card: c }))
    setEntries(initial)
    setIdx(0)
    setCompletedCount(0)
    setDoneIds(new Set())
    initialIdsRef.current = new Set(initialCards.map(c => c.id))
    setLoading(false)
  }, [initialCards])

  // 同步 ref
  useEffect(() => { entriesRef.current = entries }, [entries])
  useEffect(() => { idxRef.current = idx }, [idx])

  const rate = useCallback(async (grade: Grade) => {
    const cur = entriesRef.current[idxRef.current]
    if (!cur) return
    const updated = await applyGrade(cur.card, grade, 'review')
    const updatedEntry: ReviewEntry = { card: updated }

    setEntries(prev => {
      // 先更新当前位置的卡片为新版本
      const next = prev.map((e, i) => i === idxRef.current ? updatedEntry : e)

      if (grade === 'good') {
        // good → 不再插入, 这张卡"完成"了
        return next
      }

      // again / hard → 不规则刷新: 当前位置后 1-5 张位置 (随机)
      const ahead = 1 + Math.floor(Math.random() * 5)
      const insertPos = Math.min(idxRef.current + ahead, next.length)
      return [...next.slice(0, insertPos), updatedEntry, ...next.slice(insertPos)]
    })

    if (grade === 'good') {
      setCompletedCount(c => c + 1)
      setDoneIds(prev => {
        const s = new Set(prev)
        s.add(updated.id)
        return s
      })
    }
  }, [])

  const advance = useCallback(() => {
    setIdx(i => i + 1)
  }, [])

  // 结束条件: idx 已走完队列, 且所有初始卡片都评过 good
  const finished = !loading
    && idx >= entries.length
    && doneIds.size >= initialIdsRef.current.size
  const current = finished ? null : entries[idx] ?? null

  return {
    loading,
    entries,
    idx,
    current,
    finished,
    total: entries.length,
    initialCount: initialCards.length,
    completed: completedCount,
    rate,
    advance,
  }
}