// 历史页:
// - 顶部: 7 周热力图 (近 49 天 daily count)
// - 本周汇总 (完成/认识/新词复习)
// - sessions 列表 (按日期降序, 单屏最多 3 条, 不滚动)

import { useEffect, useState } from 'react'
import { Calendar, Check, Flame, HelpCircle, X } from 'lucide-react'
import type { HistoryItem, Heatmap } from '../lib/stats'
import { getHistoryList, getHeatmap } from '../lib/stats'

const WEEKDAY = ['日', '一', '二', '三', '四', '五', '六']
const MAX_SESSIONS_INLINE = 3  // 单屏最多 3 条 session, 更多显示 "查看全部"

function formatDateLabel(dateStr: string): string {
  const [, mm, dd] = dateStr.split('-')
  const d = new Date(dateStr)
  const wd = WEEKDAY[d.getDay()]
  return `${mm}-${dd} 周${wd}`
}

function isToday(dateStr: string): boolean {
  const today = new Date()
  const yyyy = today.getFullYear()
  const mm = String(today.getMonth() + 1).padStart(2, '0')
  const dd = String(today.getDate()).padStart(2, '0')
  return dateStr === `${yyyy}-${mm}-${dd}`
}

export function History() {
  const [items, setItems] = useState<HistoryItem[]>([])
  const [heatmap, setHeatmap] = useState<Heatmap>({ weeks: [], maxCount: 0, totalLast7: 0, totalAll: 0 })
  const [loading, setLoading] = useState(true)
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      const [list, hm] = await Promise.all([getHistoryList(), getHeatmap()])
      if (!cancelled) {
        setItems(list)
        setHeatmap(hm)
        setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [])

  // 本周汇总 (last 7 days from today)
  const todayMs = new Date().setHours(0, 0, 0, 0)
  const weekAgoMs = todayMs - 6 * 86400_000
  const weekItems = items.filter(it => {
    const ms = new Date(it.session.date).getTime()
    return ms >= weekAgoMs && ms <= todayMs + 86400_000
  })
  const weekDone = weekItems.reduce((s, it) => s + it.session.completedCount, 0)
  const weekNew = weekItems.reduce((s, it) => s + it.session.newCount, 0)
  const weekRev = weekItems.reduce((s, it) => s + it.session.reviewsCount, 0)
  const allReviews = weekItems.reduce((s, it) => s + it.goodCount + it.hardCount + it.againCount, 0)
  const weekGoodPct = allReviews === 0 ? 0 : Math.round(
    weekItems.reduce((s, it) => s + it.goodCount, 0) / allReviews * 100,
  )

  // 单屏显示: 3 条或全部
  const visibleItems = showAll ? items : items.slice(0, MAX_SESSIONS_INLINE)
  const hasMore = items.length > MAX_SESSIONS_INLINE

  return (
    // 单页不滚动: py-4 (顶部 16px), pb-20 (底部 80px 给 tab bar)
    <div className="min-h-full pb-20 px-5 py-4">
      <header className="mb-3">
        <h1 className="text-2xl font-extrabold text-[color:var(--color-ink)] leading-tight">历史</h1>
        <p className="text-xs text-[color:var(--color-muted)] mt-0.5">复习记录与进度</p>
      </header>

      {/* 7 周热力图 (紧凑) */}
      <section className="rounded-2xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-3 mb-3">
        <div className="flex items-baseline justify-between mb-2">
          <div className="flex items-center gap-1.5 text-[color:var(--color-muted)] text-[10px] font-bold uppercase tracking-widest">
            <Flame className="w-3.5 h-3.5" strokeWidth={1.75} />
            7 周打卡
          </div>
          <div className="text-[10px] text-[color:var(--color-muted)] tabular-nums">
            近 7 天 <span className="text-[color:var(--color-ink)] font-bold">{heatmap.totalLast7}</span> 词
          </div>
        </div>

        {heatmap.weeks.length === 0 ? (
          <div className="text-center text-[color:var(--color-muted)] py-3 text-xs">加载中...</div>
        ) : (
          <>
            <div className="flex gap-1">
              {/* 星期 label (左) */}
              <div className="flex flex-col gap-1 justify-around text-[9px] text-[color:var(--color-muted)] font-bold pr-1">
                <span>一</span>
                <span>三</span>
                <span>五</span>
                <span>日</span>
              </div>
              {/* 7 周列 */}
              {heatmap.weeks.map((week) => (
                <div key={week.weekIndex} className="flex flex-col gap-1 flex-1">
                  {week.days.map((cell, dIdx) => {
                    if (!cell) return <div key={dIdx} className="aspect-square" />
                    let bg = 'var(--color-border)'
                    let opacity = 1
                    if (cell.isFuture) {
                      bg = 'transparent'
                      opacity = 0.3
                    } else if (cell.count >= 100) {
                      bg = 'var(--color-success)'
                    } else if (cell.count >= 50) {
                      bg = 'var(--color-success)'; opacity = 0.75
                    } else if (cell.count >= 25) {
                      bg = 'var(--color-success)'; opacity = 0.5
                    } else if (cell.count >= 1) {
                      bg = 'var(--color-success)'; opacity = 0.25
                    }
                    return (
                      <div
                        key={dIdx}
                        title={`${cell.date} · ${cell.count} 词`}
                        className={`aspect-square rounded-[2px] ${cell.isToday ? 'ring-1 ring-[color:var(--color-ink)]' : ''}`}
                        style={{ background: bg, opacity }}
                      />
                    )
                  })}
                </div>
              ))}
            </div>

            {/* 图例 */}
            <div className="mt-2 flex items-center justify-between text-[9px] text-[color:var(--color-muted)]">
              <span>少</span>
              <div className="flex items-center gap-0.5">
                {[0.15, 0.35, 0.55, 0.75, 1].map((o, i) => (
                  <div
                    key={i}
                    className="w-2.5 h-2.5 rounded-[1px]"
                    style={{
                      background: i === 0 ? 'var(--color-border)' : 'var(--color-success)',
                      opacity: i === 0 ? 1 : o,
                    }}
                  />
                ))}
              </div>
              <span>多</span>
            </div>
          </>
        )}
      </section>

      {/* 本周汇总 (紧凑) */}
      <section className="rounded-2xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-3 mb-3">
        <div className="flex items-center gap-1.5 text-[color:var(--color-muted)] text-[10px] font-bold uppercase tracking-widest mb-2">
          <Calendar className="w-3.5 h-3.5" strokeWidth={1.75} />
          本周
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div>
            <div className="text-xl font-extrabold text-[color:var(--color-ink)] tabular-nums leading-none">
              {weekDone}
            </div>
            <div className="text-[9px] text-[color:var(--color-muted)] font-bold mt-0.5">完成</div>
          </div>
          <div>
            <div className="text-xl font-extrabold text-[color:var(--color-ink)] tabular-nums leading-none">
              {weekGoodPct}<span className="text-sm text-[color:var(--color-muted)]">%</span>
            </div>
            <div className="text-[9px] text-[color:var(--color-muted)] font-bold mt-0.5">认识</div>
          </div>
          <div>
            <div className="text-xl font-extrabold text-[color:var(--color-ink)] tabular-nums leading-none">
              {weekNew}<span className="text-sm text-[color:var(--color-muted)]">/{weekRev}</span>
            </div>
            <div className="text-[9px] text-[color:var(--color-muted)] font-bold mt-0.5">新词/复习</div>
          </div>
        </div>
      </section>

      {/* sessions 列表 (单屏最多 3 条) */}
      {loading ? (
        <div className="text-center text-[color:var(--color-muted)] py-4 text-xs">加载中...</div>
      ) : items.length === 0 ? (
        <div className="text-center text-[color:var(--color-muted)] py-4">
          <div className="text-3xl mb-1">📭</div>
          <div className="text-xs">还没有复习记录</div>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {visibleItems.map(it => {
            const total = it.goodCount + it.hardCount + it.againCount
            return (
              <div
                key={it.session.id}
                className="rounded-2xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-3"
              >
                <div className="flex items-baseline justify-between mb-1.5">
                  <div className="text-xs font-extrabold text-[color:var(--color-ink)] flex items-center gap-1.5">
                    {formatDateLabel(it.session.date)}
                    {isToday(it.session.date) && (
                      <span className="text-[9px] text-[color:var(--color-success)] bg-[color:var(--color-success)]/10 px-1.5 py-0.5 rounded font-bold">
                        今天
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-[color:var(--color-muted)] tabular-nums">
                    完成 {it.session.completedCount}
                  </div>
                </div>

                {total > 0 && (
                  <div className="h-1 rounded-full bg-[color:var(--color-border)] overflow-hidden flex mb-1.5">
                    <div className="h-full bg-[color:var(--color-success)]" style={{ width: `${(it.goodCount / total) * 100}%` }} />
                    <div className="h-full bg-[color:var(--color-warning)]" style={{ width: `${(it.hardCount / total) * 100}%` }} />
                    <div className="h-full bg-[color:var(--color-danger)]" style={{ width: `${(it.againCount / total) * 100}%` }} />
                  </div>
                )}

                <div className="flex items-center justify-between text-[10px]">
                  <div className="flex items-center gap-2 text-[color:var(--color-muted)]">
                    <span className="flex items-center gap-0.5">
                      <Check className="w-2.5 h-2.5 text-[color:var(--color-success)]" strokeWidth={2.5} />
                      {it.goodCount}
                    </span>
                    <span className="flex items-center gap-0.5">
                      <HelpCircle className="w-2.5 h-2.5 text-[color:var(--color-warning)]" strokeWidth={2.5} />
                      {it.hardCount}
                    </span>
                    <span className="flex items-center gap-0.5">
                      <X className="w-2.5 h-2.5 text-[color:var(--color-danger)]" strokeWidth={2.5} />
                      {it.againCount}
                    </span>
                  </div>
                  <div className="font-extrabold text-[color:var(--color-ink)] tabular-nums">
                    {it.goodPct}%
                  </div>
                </div>
              </div>
            )
          })}

          {/* 查看更多 / 收起 */}
          {hasMore && (
            <button
              onClick={() => setShowAll(s => !s)}
              className="mt-1 h-10 rounded-xl border-2 border-[color:var(--color-border)] text-[color:var(--color-ink)] font-bold text-xs active:bg-[color:var(--color-surface)]"
            >
              {showAll ? `收起 (共 ${items.length} 条)` : `查看全部 ${items.length} 条 →`}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
