import { BookOpen, Calendar, CheckCircle2, CircleDashed, Flame, HelpCircle, Plus, XCircle } from 'lucide-react'
import type { Stats } from '../lib/stats'
import type { Progress } from '../lib/progress'

interface HomeProps {
  stats: Stats
  progress: Progress
  hasActiveSession: boolean
  onStart: () => void
}

export function Home({ stats, progress, hasActiveSession, onStart }: HomeProps) {
  // 今日新词进度 (核心指标, SM-2 推荐节奏)
  const newPct = stats.todayNewTarget === 0
    ? 0
    : Math.min(100, Math.round((stats.todayNewDone / stats.todayNewTarget) * 100))
  // 是否超额 (用户多学了, 紫色 + 鼓励文案)
  const overNew = stats.todayNewDone > stats.todayNewTarget

  // 4 档进度 (用了避免全是 0 时显示成空)
  const showProgress = progress.total > 0
  const masterPct = showProgress ? Math.round((progress.mastered / progress.total) * 100) : 0

  return (
    // 单页不滚动: py-5 (顶部 20px), pb-20 (底部 80px 给 tab bar)
    <div className="min-h-full flex flex-col px-5 py-5 pb-20">
      <header className="mb-3">
        <h1 className="text-3xl font-extrabold text-[color:var(--color-ink)] leading-tight">English Book</h1>
        <p className="text-xs text-[color:var(--color-muted)] mt-0.5">上海中考词汇 · 每日打卡</p>
      </header>

      <main className="flex-1 flex flex-col gap-3 justify-end">        {/* 今日新词 (核心) */}
        <section className="rounded-2xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-4">
          <div className="flex items-center gap-1.5 text-[color:var(--color-muted)] text-[10px] font-bold uppercase tracking-widest mb-1.5">
            <BookOpen className="w-3.5 h-3.5" strokeWidth={1.75} />
            今日新词
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-[color:var(--color-ink)] tabular-nums leading-none">
              {stats.todayNewDone}
            </span>
            <span className="text-base text-[color:var(--color-muted)] font-bold">
              / {stats.todayNewTarget}
            </span>
            {overNew && (
              <span className="ml-1 text-[10px] font-bold text-[color:var(--color-ink-2)] bg-[color:var(--color-ink-2)]/10 px-1.5 py-0.5 rounded-full flex items-center gap-0.5">
                <Plus className="w-2.5 h-2.5" strokeWidth={2.5} />
                超出 {stats.todayNewDone - stats.todayNewTarget}
              </span>
            )}
          </div>
          <div className="mt-2 h-1.5 rounded-full bg-[color:var(--color-border)] overflow-hidden">
            <div
              className="h-full bg-[color:var(--color-ink)] transition-all duration-300"
              style={{ width: `${newPct}%` }}
            />
          </div>
          <div className="mt-1.5 text-[10px] text-[color:var(--color-muted)] flex items-center gap-2">
            <span>复习 {stats.todayReviewDone} 词</span>
            <span>·</span>
            <span>合计 {stats.todayTotalDone} 词</span>
          </div>
        </section>

        <div className="grid grid-cols-2 gap-3">
          {/* 连续打卡 */}
          <section className="rounded-2xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-3">
            <div className="flex items-center gap-1.5 text-[color:var(--color-muted)] text-[10px] font-bold uppercase tracking-widest mb-0.5">
              <Flame className="w-3.5 h-3.5" strokeWidth={1.75} />
              连续
            </div>
            <div className="text-3xl font-extrabold text-[color:var(--color-ink)] tabular-nums leading-none">
              {stats.streak}
            </div>
            <div className="text-[10px] text-[color:var(--color-muted)] mt-0.5">天</div>
          </section>

          {/* 累计 */}
          <section className="rounded-2xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-3">
            <div className="flex items-center gap-1.5 text-[color:var(--color-muted)] text-[10px] font-bold uppercase tracking-widest mb-0.5">
              <Calendar className="w-3.5 h-3.5" strokeWidth={1.75} />
              累计
            </div>
            <div className="text-3xl font-extrabold text-[color:var(--color-ink)] tabular-nums leading-none">
              {stats.totalLearned}
            </div>
            <div className="text-[10px] text-[color:var(--color-muted)] mt-0.5">词</div>
          </section>
        </div>

        {/* 词库进度 (Phase 5.1: 4 档分类 + 剩余天数) - 紧凑 */}
        <section className="rounded-2xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-3">
          <div className="flex items-baseline justify-between mb-2">
            <div className="flex items-center gap-1.5 text-[color:var(--color-muted)] text-[10px] font-bold uppercase tracking-widest">
              <CheckCircle2 className="w-3.5 h-3.5" strokeWidth={1.75} />
              词库进度
            </div>
            <div className="text-[10px] text-[color:var(--color-muted)] tabular-nums">
              {progress.total} 词
            </div>
          </div>

          {/* 顶部掌握比例 (单色进度条, 整体感) */}
          <div className="mb-2 h-1.5 rounded-full bg-[color:var(--color-border)] overflow-hidden flex">
            <div className="h-full bg-[color:var(--color-success)]" style={{ width: `${masterPct}%` }} title="掌握" />
            <div className="h-full bg-[color:var(--color-warning)]" style={{ width: `${showProgress ? (progress.fuzzy / progress.total) * 100 : 0}%` }} title="模糊" />
            <div className="h-full bg-[color:var(--color-danger)]" style={{ width: `${showProgress ? (progress.struggling / progress.total) * 100 : 0}%` }} title="不会" />
            <div className="h-full bg-[color:var(--color-muted)]" style={{ width: `${showProgress ? (progress.unlearned / progress.total) * 100 : 0}%` }} title="未学" />
          </div>

          {/* 4 档数字 2x2 网格 - 紧凑 */}
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-xl bg-[color:var(--color-bg)] p-2">
              <div className="flex items-center gap-1 text-[10px] font-bold text-[color:var(--color-success)] mb-0.5">
                <CheckCircle2 className="w-3 h-3" strokeWidth={2} />
                掌握
              </div>
              <div className="text-xl font-extrabold text-[color:var(--color-ink)] tabular-nums leading-none">
                {progress.mastered}
              </div>
            </div>
            <div className="rounded-xl bg-[color:var(--color-bg)] p-2">
              <div className="flex items-center gap-1 text-[10px] font-bold text-[color:var(--color-warning)] mb-0.5">
                <HelpCircle className="w-3 h-3" strokeWidth={2} />
                模糊
              </div>
              <div className="text-xl font-extrabold text-[color:var(--color-ink)] tabular-nums leading-none">
                {progress.fuzzy}
              </div>
            </div>
            <div className="rounded-xl bg-[color:var(--color-bg)] p-2">
              <div className="flex items-center gap-1 text-[10px] font-bold text-[color:var(--color-danger)] mb-0.5">
                <XCircle className="w-3 h-3" strokeWidth={2} />
                不会
              </div>
              <div className="text-xl font-extrabold text-[color:var(--color-ink)] tabular-nums leading-none">
                {progress.struggling}
              </div>
            </div>
            <div className="rounded-xl bg-[color:var(--color-bg)] p-2">
              <div className="flex items-center gap-1 text-[10px] font-bold text-[color:var(--color-muted)] mb-0.5">
                <CircleDashed className="w-3 h-3" strokeWidth={2} />
                未学
              </div>
              <div className="text-xl font-extrabold text-[color:var(--color-ink)] tabular-nums leading-none">
                {progress.unlearned}
              </div>
            </div>
          </div>

          {/* 剩余天数 */}
          <div className="mt-2 pt-2 border-t border-[color:var(--color-border)] text-[10px] text-[color:var(--color-muted)] flex items-center justify-between">
            <span>按当前节奏 {stats.todayNewTarget}/天</span>
            <span className="font-bold text-[color:var(--color-ink)]">
              {progress.unlearned === 0
                ? '🎉 全部学完'
                : progress.daysLeft === 1
                  ? '还剩 1 天'
                  : `还剩 ${progress.daysLeft} 天`}
            </span>
          </div>
        </section>
      </main>

      <footer className="pt-2">
        <button
          onClick={onStart}
          className="w-full h-14 rounded-2xl bg-[color:var(--color-ink)] text-white font-extrabold text-base active:scale-[0.98] transition-transform"
        >
          {hasActiveSession ? '继续' : '开始今日'}
        </button>
      </footer>
    </div>
  )
}
