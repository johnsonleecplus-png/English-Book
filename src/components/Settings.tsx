// 设置页: 每日目标 + 复习入口 + 致谢
// - 每日新词目标: 5 / 15 / 30 / 50 / 100 + 自定义 1-200
// - 复习今日模糊/不会: 进入复习模式
// - 致谢: SM-2 算法出处 (SuperMemo) + 开源依赖

import { useEffect, useState } from 'react'
import { Settings as SettingsIcon, Repeat, Trophy, ExternalLink, BookOpen } from 'lucide-react'
import { getSettings, setDailyNewTarget } from '../lib/queue'
import { getReviewableCards } from '../lib/progress'

const CHIPS = [5, 15, 30, 50, 100]

interface SettingsProps {
  /** 触发进入复习模式 (App.tsx 处理) */
  onStartReview?: () => void
}

/** 打开外部链接 (Capacitor 中可在 WebView 内打开) */
function openLink(url: string) {
  window.open(url, '_blank', 'noopener,noreferrer')
}

export function Settings({ onStartReview }: SettingsProps) {
  const [current, setCurrent] = useState<number>(15)
  const [custom, setCustom] = useState<string>('')
  const [showCustom, setShowCustom] = useState(false)
  const [saved, setSaved] = useState(false)
  const [reviewCount, setReviewCount] = useState<number>(0)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      const [s, cards] = await Promise.all([
        getSettings(),
        getReviewableCards(),
      ])
      if (cancelled) return
      setCurrent(s.dailyNewTarget)
      setReviewCount(cards.length)
      if (!CHIPS.includes(s.dailyNewTarget) && s.dailyNewTarget > 0) {
        setShowCustom(true)
        setCustom(String(s.dailyNewTarget))
      }
    })()
    return () => { cancelled = true }
  }, [])

  async function pick(n: number) {
    setCurrent(n)
    setShowCustom(false)
    setCustom('')
    await setDailyNewTarget(n)
    flashSaved()
  }
  async function pickCustom() {
    setShowCustom(true)
  }
  async function applyCustom() {
    const n = parseInt(custom, 10)
    if (n >= 1 && n <= 200) {
      setCurrent(n)
      await setDailyNewTarget(n)
      flashSaved()
    }
  }
  function flashSaved() {
    setSaved(true)
    setTimeout(() => setSaved(false), 1500)
  }

  return (
    <div className="min-h-full pb-24 px-6 py-8">
      <header className="mb-6">
        <h1 className="text-3xl font-extrabold text-[color:var(--color-ink)]">设置</h1>
        <p className="text-sm text-[color:var(--color-muted)] mt-1">偏好</p>
      </header>

      {/* ===== 复习入口 ===== */}
      <section className="rounded-3xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-6 mb-4">
        <div className="flex items-center gap-2 text-[color:var(--color-muted)] text-xs font-bold uppercase tracking-widest mb-3">
          <Trophy className="w-4 h-4" strokeWidth={1.75} />
          复习
        </div>
        <button
          onClick={onStartReview}
          disabled={reviewCount === 0}
          className={`w-full h-14 rounded-2xl font-extrabold text-base flex items-center justify-center gap-2 transition-colors ${
            reviewCount === 0
              ? 'border-2 border-dashed border-[color:var(--color-border)] bg-transparent text-[color:var(--color-muted)] cursor-not-allowed'
              : 'bg-[color:var(--color-ink)] text-white active:scale-[0.98]'
          }`}
        >
          <Repeat className="w-5 h-5" strokeWidth={2} />
          {reviewCount === 0
            ? '没有需要复习的词'
            : `复习今日模糊/不会 (${reviewCount} 词)`}
        </button>
        {reviewCount > 0 && (
          <p className="text-[10px] text-[color:var(--color-muted)] text-center mt-2">
            循环复习直到全部掌握, 不计入今日打卡
          </p>
        )}
      </section>

      {/* ===== 每日新词目标 ===== */}
      <section className="rounded-3xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-6">
        <div className="flex items-center gap-2 text-[color:var(--color-muted)] text-xs font-bold uppercase tracking-widest mb-3">
          <SettingsIcon className="w-4 h-4" strokeWidth={1.75} />
          每日新词目标
        </div>

        <div className="grid grid-cols-5 gap-2 mb-3">
          {CHIPS.map(n => (
            <button
              key={n}
              onClick={() => pick(n)}
              className={`h-12 rounded-2xl font-extrabold text-sm transition-colors ${
                current === n
                  ? 'bg-[color:var(--color-ink)] text-white'
                  : 'border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] text-[color:var(--color-ink)] active:bg-[color:var(--color-border)]'
              }`}
            >
              {n}
            </button>
          ))}
        </div>

        <button
          onClick={pickCustom}
          className={`w-full h-12 rounded-2xl border-2 font-bold text-sm mb-2 transition-colors ${
            showCustom
              ? 'border-[color:var(--color-ink)] bg-[color:var(--color-surface)] text-[color:var(--color-ink)]'
              : 'border-dashed border-[color:var(--color-border)] bg-transparent text-[color:var(--color-muted)] active:bg-[color:var(--color-surface)]'
          }`}
        >
          {showCustom ? (
            <span className="flex items-center justify-center gap-2">
              <input
                type="number"
                inputMode="numeric"
                min="1"
                max="200"
                value={custom}
                onChange={e => setCustom(e.target.value)}
                onBlur={applyCustom}
                onKeyDown={e => { if (e.key === 'Enter') (e.target as HTMLInputElement).blur() }}
                placeholder="输入数字"
                autoFocus
                className="w-24 bg-transparent text-center text-lg font-extrabold text-[color:var(--color-ink)] outline-none tabular-nums"
              />
              <span className="text-[color:var(--color-muted)]">/天</span>
            </span>
          ) : (
            <span>自定义 1-200</span>
          )}
        </button>

        {saved && (
          <div className="text-xs text-[color:var(--color-success)] font-bold text-center mt-2">
            ✓ 已保存: 每天 {current} 个新词
          </div>
        )}
      </section>

      {/* ===== 致谢 ===== */}
      <section className="rounded-3xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-6 mt-4">
        <div className="flex items-center gap-2 text-[color:var(--color-muted)] text-xs font-bold uppercase tracking-widest mb-3">
          <BookOpen className="w-4 h-4" strokeWidth={1.75} />
          致谢
        </div>

        {/* SM-2 算法致谢 */}
        <div className="mb-4">
          <div className="text-sm font-extrabold text-[color:var(--color-ink)] mb-1">
            间隔重复算法 SM-2
          </div>
          <div className="text-xs text-[color:var(--color-muted)] leading-relaxed">
            本应用使用 <span className="font-bold text-[color:var(--color-ink)]">SuperMemo SM-2</span> 算法
            进行间隔重复调度。SM-2 由 <span className="font-bold text-[color:var(--color-ink)]">Piotr Woźniak</span> 于 1985-1990 年提出。
          </div>
          <div className="text-[10px] text-[color:var(--color-muted)] italic mt-1 leading-relaxed">
            Woźniak, P. A. (1990). Optimization of repetition spacing in the practice of learning.
            <br />
            <span className="text-[color:var(--color-ink-2)]">Acta Neurobiologiae Experimentalis</span>, 50, 197–201.
          </div>
          <button
            onClick={() => openLink('https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-supermemo-method')}
            className="mt-2 text-xs text-[color:var(--color-ink-2)] font-bold flex items-center gap-1 active:opacity-60"
          >
            <ExternalLink className="w-3 h-3" strokeWidth={2} />
            SuperMemo 官方说明
          </button>
        </div>

        {/* 分隔线 */}
        <div className="h-px bg-[color:var(--color-border)] my-4" />

        {/* 开源依赖 */}
        <div>
          <div className="text-sm font-extrabold text-[color:var(--color-ink)] mb-2">
            开源技术
          </div>
          <div className="space-y-1.5 text-xs text-[color:var(--color-muted)]">
            <div className="flex items-center justify-between">
              <span>React 19 + TypeScript</span>
              <span className="text-[9px] text-[color:var(--color-ink-2)]">UI 框架</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Vite 8</span>
              <span className="text-[9px] text-[color:var(--color-ink-2)]">构建工具</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Tailwind CSS 4</span>
              <span className="text-[9px] text-[color:var(--color-ink-2)]">样式框架</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Capacitor 8</span>
              <span className="text-[9px] text-[color:var(--color-ink-2)]">Android 打包</span>
            </div>
            <div className="flex items-center justify-between">
              <span>lucide-react</span>
              <span className="text-[9px] text-[color:var(--color-ink-2)]">图标库</span>
            </div>
            <div className="flex items-center justify-between">
              <span>IndexedDB (idb)</span>
              <span className="text-[9px] text-[color:var(--color-ink-2)]">本地存储</span>
            </div>
          </div>
        </div>

        {/* 词库来源 */}
        <div className="h-px bg-[color:var(--color-border)] my-4" />
        <div>
          <div className="text-sm font-extrabold text-[color:var(--color-ink)] mb-1">
            词库
          </div>
          <div className="text-xs text-[color:var(--color-muted)] leading-relaxed">
            上海中考英语词汇表 (完整版) — 1711 词条
            <br />
            <span className="text-[10px]">音频由 Piper TTS (en_US-amy-medium) 离线生成</span>
          </div>
        </div>
      </section>
    </div>
  )
}