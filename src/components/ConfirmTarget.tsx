import { useState } from 'react'
import { Sparkles } from 'lucide-react'

interface ConfirmTargetProps {
  /** 昨天 / 上次设置的目标数 (作为默认) */
  defaultTarget: number
  /** 是否首次使用 (没历史) */
  isFirstTime: boolean
  onConfirm: (n: number) => void
}

const CHIPS = [5, 15, 30, 50, 100]

/**
 * 今日新词目标确认屏 (Home → Confirm → Active 中间层)
 * - chips: 5 / 15 / 30 / 50 / 100
 * - 选完点 "开始" → onConfirm(n)
 * - 取消 → 滑回 (TabBar 一直在, 切回 今日 tab 即可)
 */
export function ConfirmTarget({ defaultTarget, isFirstTime, onConfirm }: ConfirmTargetProps) {
  // 选中的目标: 默认昨天的数, 落在 chips 中或自定义
  const [target, setTarget] = useState<number>(() => {
    if (CHIPS.includes(defaultTarget)) return defaultTarget
    // 不在 chips 中, 找最接近的
    return CHIPS.reduce((closest, c) =>
      Math.abs(c - defaultTarget) < Math.abs(closest - defaultTarget) ? c : closest
    , CHIPS[0])
  })
  const [custom, setCustom] = useState<string>('')
  const [showCustom, setShowCustom] = useState(!CHIPS.includes(defaultTarget) && defaultTarget > 0)

  function pick(n: number) {
    setTarget(n)
    setShowCustom(false)
  }
  function pickCustom() {
    setShowCustom(true)
  }
  function applyCustom() {
    const n = parseInt(custom, 10)
    if (n >= 1 && n <= 200) {
      setTarget(n)
    }
  }

  return (
    <div className="min-h-full flex flex-col px-6 py-10 pb-24">
      <main className="flex-1 flex flex-col">
        {/* 标题 */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-[color:var(--color-muted)] text-xs font-bold uppercase tracking-widest mb-2">
            <Sparkles className="w-4 h-4" strokeWidth={1.75} />
            今日计划
          </div>
          <h1 className="text-4xl font-extrabold text-[color:var(--color-ink)] leading-tight">
            今天学几个<br />新词?
          </h1>
          {!isFirstTime && (
            <p className="text-sm text-[color:var(--color-muted)] mt-3">
              昨天学了 {defaultTarget} 个, 可直接用也可改
            </p>
          )}
          {isFirstTime && (
            <p className="text-sm text-[color:var(--color-muted)] mt-3">
              首次使用, 推荐 15 个, 后面随时可加
            </p>
          )}
        </div>

        {/* Chips */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          {CHIPS.map(n => (
            <button
              key={n}
              onClick={() => pick(n)}
              className={`h-20 rounded-2xl border-2 font-extrabold text-2xl tabular-nums transition-colors ${
                target === n && !showCustom
                  ? 'border-[color:var(--color-ink)] bg-[color:var(--color-ink)] text-white'
                  : 'border-[color:var(--color-border)] bg-[color:var(--color-surface)] text-[color:var(--color-ink)] active:bg-[color:var(--color-border)]'
              }`}
            >
              {n}
            </button>
          ))}
        </div>

        {/* 自定义 */}
        <button
          onClick={pickCustom}
          className={`h-14 rounded-2xl border-2 border-dashed font-bold text-base mb-3 transition-colors ${
            showCustom
              ? 'border-[color:var(--color-ink)] bg-[color:var(--color-surface)] text-[color:var(--color-ink)]'
              : 'border-[color:var(--color-border)] bg-transparent text-[color:var(--color-muted)] active:bg-[color:var(--color-surface)]'
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
                placeholder="输入数字"
                autoFocus
                className="w-24 bg-transparent text-center text-2xl font-extrabold text-[color:var(--color-ink)] outline-none tabular-nums"
              />
              <span className="text-sm font-bold text-[color:var(--color-muted)]">个</span>
            </span>
          ) : (
            <span>自定义...</span>
          )}
        </button>
      </main>

      <footer className="pt-6">
        <button
          onClick={() => onConfirm(target)}
          className="w-full h-16 rounded-2xl bg-[color:var(--color-ink)] text-white font-extrabold text-lg active:scale-[0.98] transition-transform"
        >
          开始学 {target} 个新词
        </button>
      </footer>
    </div>
  )
}
