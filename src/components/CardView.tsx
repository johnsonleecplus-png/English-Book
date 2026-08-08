import { useEffect, useRef, useState } from 'react'
import { Image, Languages, Volume2, X, HelpCircle, Check, Shuffle, Plus } from 'lucide-react'
import type { Mode, Grade, Session } from '../lib/types'
import { useQueue } from '../hooks/useQueue'
import { WORD_EMOJIS, WORD_ICONS, getIconComponent } from '../lib/iconMap'
import { EmojiView } from './TwemojiImage'
import { AutoFitText } from './AutoFitText'

const MODES: { id: Mode; label: string; Icon: typeof Image }[] = [
  { id: 'image',  label: '图说', Icon: Image },
  { id: 'en2cn',  label: '英译', Icon: Languages },
  { id: 'cn2en',  label: '中译', Icon: Languages },
  { id: 'listen', label: '听说', Icon: Volume2 },
  { id: 'mix',    label: '混合', Icon: Shuffle },
]
const BASE_MODES: Mode[] = ['image', 'en2cn', 'cn2en', 'listen']

interface CardViewProps {
  session: Session
  onRate: (isNew: boolean) => Promise<void>
  onFinish: () => void
  grayscale?: boolean
}

export function CardView({ session, onRate, onFinish, grayscale = false }: CardViewProps) {
  const queue = useQueue()
  const [mode, setMode] = useState<Mode>('en2cn')
  const [mixMode, setMixMode] = useState<Mode>('en2cn')
  const [feedback, setFeedback] = useState<'good' | 'again' | null>(null)
  const [transitioning, setTransitioning] = useState(false)
  const [gradeStats, setGradeStats] = useState({ good: 0, hard: 0, again: 0 })
  const [displayDone, setDisplayDone] = useState(session.completedCount)
  const [revealed, setRevealed] = useState(false)
  const cardRef = useRef<HTMLDivElement>(null)
  const cardInnerRef = useRef<HTMLDivElement>(null)  // 字号自适应测宽用 (内层 padding-6)

  const entry = queue.current
  const word = entry?.card
  const effectiveMode: Mode = mode === 'mix' ? mixMode : mode

  // 切混合模式: 每次新卡随机选基础模式
  useEffect(() => {
    if (mode === 'mix') {
      setMixMode(BASE_MODES[Math.floor(Math.random() * BASE_MODES.length)])
    }
  }, [mode, queue.idx])

  // 自动播音策略:
  //   - listen 模式: 进新卡就播 (听音做题, 不播没法选)
  //   - en2cn 模式: 进新卡就播 (先听发音, 再看英文, 再猜中文 — Johnson 决策 2026-08-08)
  //   - 其他模式 (image / cn2en / mix): 进新卡不播, 等用户点揭示后再读
  //     (image 看图猜词, cn2en 看中文反推单词 — 都是先看/猜再揭晓)
  useEffect(() => {
    if (!word) return
    if (effectiveMode === 'listen' || effectiveMode === 'en2cn') {
      const t = setTimeout(() => speak(), 50)
      return () => clearTimeout(t)
    }
  }, [word?.id, effectiveMode])

  // 切到新卡 → 重置 revealed (遮蔽状态)
  useEffect(() => {
    setRevealed(false)
  }, [word?.id])

  // 键盘快捷键:
  // - Space: 揭示答案 (reveal)
  // - 1/2/3: 评分 (必须 revealed 后才能用, 防止偷看)
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement | null)?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA') return
      if ((e.target as HTMLElement | null)?.isContentEditable) return
      if (!entry) return
      if (transitioning) return

      if (e.code === 'Space') {
        e.preventDefault()
        if (!revealed) {
          setRevealed(true)
          setTimeout(() => speak(), 50)
        }
        return
      }
      if (!revealed) return  // 没揭示不能评分

      if (e.code === 'Digit1' || e.code === 'Numpad1') {
        e.preventDefault()
        handleRate('again')
      } else if (e.code === 'Digit2' || e.code === 'Numpad2') {
        e.preventDefault()
        handleRate('hard')
      } else if (e.code === 'Digit3' || e.code === 'Numpad3') {
        e.preventDefault()
        handleRate('good')
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [entry, transitioning, revealed])

  // 完全离线 TTS: 全部走预录 MP3 (Piper en_US-amy-medium)
  function speak() {
    if (!word) return
    const w = word.word.toLowerCase()
    // 空格和单引号都转下划线 (跟 audio 文件名约定一致, 词组如 "lose one's life" → lose_one_s_life.mp3)
    const audioPath = `/audio/words/${w.replaceAll(' ', '_').replaceAll("'", '_')}.mp3`
    fetch(audioPath, { method: 'HEAD' })
      .then(r => {
        const len = parseInt(r.headers.get('content-length') || '0', 10)
        const ct = r.headers.get('content-type') || ''
        const isRealAudio = r.ok && len > 1024 && ct.startsWith('audio/')
        if (isRealAudio) {
          const audio = new Audio(audioPath)
          audio.playbackRate = 0.9
          audio.onerror = () => console.warn(`[tts] audio play error: ${audioPath}`)
          audio.play().catch((e) => console.warn(`[tts] audio play rejected: ${audioPath} (${e?.message ?? e})`))
        } else {
          console.warn(`[tts] MP3 miss or bad type: ${audioPath} (status=${r.status}, len=${len}, ct=${ct})`)
        }
      })
      .catch((e) => console.warn(`[tts] fetch HEAD failed: ${audioPath} (${e?.message ?? e})`))
  }

  async function handleRate(grade: Grade) {
    if (transitioning || !entry) return
    setTransitioning(true)
    setFeedback(grade === 'again' ? 'again' : 'good')
    if (grade === 'again') {
      cardRef.current?.classList.add('animate-shake')
      setTimeout(() => cardRef.current?.classList.remove('animate-shake'), 400)
    }
    await queue.rate(grade, session.id)
    await onRate(entry.isNew)
    setGradeStats(s => ({ ...s, [grade]: s[grade] + 1 }))
    setDisplayDone(d => d + 1)

    setTimeout(() => {
      queue.advance()
      setFeedback(null)
      setTransitioning(false)
    }, 600)
  }

  async function handleAddMore(extra: number) {
    await queue.reload(extra)
  }

  // 加载中
  if (queue.loading) {
    return (
      <div className="h-screen flex items-center justify-center text-[color:var(--color-muted)]" style={{ height: '100dvh' }}>
        加载中...
      </div>
    )
  }

  // queue 跑空 — 给用户选择: 继续加新词 / 回首页
  if (!entry) {
    const gradeTotal = gradeStats.good + gradeStats.hard + gradeStats.again
    const goodPct = gradeTotal === 0 ? 0 : Math.round((gradeStats.good / gradeTotal) * 100)
    return (
      <div className="h-screen flex flex-col items-center justify-center gap-5 px-6 pb-24 text-center" style={{ height: '100dvh' }}>
        <div className="relative w-24 h-24 flex items-center justify-center">
          <div className="text-7xl animate-pop">🎉</div>
          <div className="absolute -top-2 -left-2 text-2xl animate-bounce" style={{ animationDelay: '0.1s' }}>⭐</div>
          <div className="absolute -top-2 -right-2 text-2xl animate-bounce" style={{ animationDelay: '0.3s' }}>✨</div>
          <div className="absolute -bottom-1 -left-2 text-2xl animate-bounce" style={{ animationDelay: '0.5s' }}>🏆</div>
          <div className="absolute -bottom-1 -right-2 text-2xl animate-bounce" style={{ animationDelay: '0.7s' }}>💪</div>
        </div>
        <div>
          <div className="text-3xl font-extrabold text-[color:var(--color-ink)]">太棒了!</div>
          <div className="text-sm text-[color:var(--color-muted)] mt-1">
            本次 {gradeTotal} 张 · 认识 {goodPct}%
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs text-[color:var(--color-muted)]">
          <span className="flex items-center gap-1">
            <Check className="w-3.5 h-3.5 text-[color:var(--color-success)]" strokeWidth={2.5} />
            {gradeStats.good}
          </span>
          <span className="flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5 text-[color:var(--color-warning)]" strokeWidth={2.5} />
            {gradeStats.hard}
          </span>
          <span className="flex items-center gap-1">
            <X className="w-3.5 h-3.5 text-[color:var(--color-danger)]" strokeWidth={2.5} />
            {gradeStats.again}
          </span>
        </div>
        <div className="flex flex-col gap-3 mt-2 w-full max-w-xs">
          <button
            onClick={() => handleAddMore(10)}
            className="h-14 rounded-2xl bg-[color:var(--color-ink)] text-white font-extrabold active:scale-[0.98] transition-transform flex items-center justify-center gap-2"
          >
            <Plus className="w-5 h-5" strokeWidth={2.5} />
            再学 10 个新词
          </button>
          <button
            onClick={() => handleAddMore(20)}
            className="h-12 rounded-2xl border-2 border-[color:var(--color-ink)] text-[color:var(--color-ink)] font-extrabold active:scale-[0.98] transition-transform flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" strokeWidth={2.5} />
            再学 20 个新词
          </button>
          <button
            onClick={onFinish}
            className="h-12 rounded-2xl text-[color:var(--color-muted)] font-bold active:scale-[0.98] transition-transform"
          >
            今日到这, 回首页
          </button>
        </div>
      </div>
    )
  }

  // ===== 渲染卡片内容（始终显示完整问题+答案, 无揭示步骤）=====
  function renderMain() {
    if (!word) return null
    switch (effectiveMode) {
      case 'image': {
        const emoji = WORD_EMOJIS[word.word]
        if (emoji) {
          return (
            <div className="select-none" style={{ filter: grayscale ? 'grayscale(100%)' : 'none' }}>
              <EmojiView emoji={emoji} size={96} />
            </div>
          )
        }
        const iconName = WORD_ICONS[word.word]
        const Icon = getIconComponent(iconName)
        if (Icon) return <Icon className="w-24 h-24 text-[color:var(--color-ink)]" strokeWidth={1.25} />
        return (
          <div className="w-full max-w-[300px] aspect-[3/2] rounded-2xl bg-[color:var(--color-surface)] border-2 border-dashed border-[color:var(--color-border)] flex items-center justify-center text-[color:var(--color-muted)] text-sm">
            [无图标: {word.word}]
          </div>
        )
      }
      case 'en2cn':
        return <AutoFitText text={word.word} parentRef={cardInnerRef} sizes={['text-6xl', 'text-5xl', 'text-4xl']} className="font-extrabold text-center text-[color:var(--color-ink)] tracking-tight" />
      case 'cn2en':
        return <div className="text-5xl font-extrabold text-center text-[color:var(--color-ink)]">{word.cn.split(',')[0]}</div>
      case 'listen':
        return (
          <button
            onClick={(e) => { e.stopPropagation(); speak() }}
            className="w-28 h-28 rounded-full border-2 border-[color:var(--color-ink)] flex items-center justify-center active:scale-95 transition-transform"
          >
            <Volume2 className="w-12 h-12 text-[color:var(--color-ink)]" strokeWidth={1.5} />
          </button>
        )
    }
  }

  // 各模式的答案区 (中文 / pos / example 全部居中)
  function renderAnswer() {
    if (!word) return null
    if (effectiveMode === 'en2cn' || effectiveMode === 'cn2en') {
      return (
        <>
          <div className="text-sm text-[color:var(--color-muted)] font-bold uppercase tracking-widest text-center">{word.pos}</div>
          {effectiveMode === 'en2cn' ? (
            <div className="text-4xl font-extrabold text-[color:var(--color-ink)] break-words text-center">{word.cn}</div>
          ) : (
            <AutoFitText text={word.word} parentRef={cardInnerRef} sizes={['text-5xl', 'text-4xl', 'text-3xl']} className="font-extrabold text-[color:var(--color-ink)] break-words text-center" />
          )}
          {word.example && (
            <div className="text-sm text-[color:var(--color-muted)] mt-2 italic break-words text-center max-w-full">"{word.example}"</div>
          )}
        </>
      )
    }
    // image / listen
    return (
      <>
        <AutoFitText text={word.word} parentRef={cardInnerRef} sizes={['text-4xl', 'text-3xl', 'text-2xl']} className="font-extrabold text-[color:var(--color-ink)] break-words text-center" />
        <div className="text-2xl text-[color:var(--color-muted)] break-words text-center">{word.cn}</div>
        {word.example && (
          <div className="text-sm text-[color:var(--color-muted)] mt-2 italic break-words text-center max-w-full">"{word.example}"</div>
        )}
      </>
    )
  }

  return (
    <div
      className="h-screen flex flex-col overflow-hidden"
      style={{ height: '100dvh' }}
    >
      {/* ===== 顶部状态栏 ===== */}
      <header className="px-4 pt-4 pb-2 shrink-0">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex-1 h-2 rounded-full bg-[color:var(--color-border)] overflow-hidden">
            <div
              className="h-full bg-[color:var(--color-ink)] transition-all duration-300"
              style={{ width: `${Math.min(100, (displayDone % 50) * 2)}%` }}
            />
          </div>
          <div className="text-xs text-[color:var(--color-muted)] font-bold tabular-nums">
            {displayDone} 张
          </div>
        </div>

        <div className="grid grid-cols-5 gap-1 pb-1">
          {MODES.map(m => {
            const Icon = m.Icon
            return (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={`px-1.5 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-colors flex items-center justify-center gap-1 min-w-0 ${
                  mode === m.id
                    ? 'bg-[color:var(--color-ink)] text-white'
                    : 'bg-[color:var(--color-surface)] text-[color:var(--color-muted)]'
                }`}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" strokeWidth={1.75} />
                <span className="truncate">{m.label}</span>
              </button>
            )
          })}
        </div>
      </header>

      {/* ===== 卡片区（揭示步骤: 未揭示显示 ?, 点击/按 Space/按底部"答案"按钮揭示）===== */}
      <main className="flex-1 px-4 py-4 flex items-center justify-center overflow-hidden">
        <div
          ref={cardRef}
          onClick={() => {
            if (!revealed) {
              setRevealed(true)
              // 揭示时立即朗读 (image/cn2en 模式下, 这是揭晓单词的时刻)
              setTimeout(() => speak(), 50)
            } else {
              speak()
            }
          }}
          className={`relative w-full max-w-md rounded-3xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-6 h-full max-h-[560px] overflow-hidden cursor-pointer transition-all ${
            feedback ? 'border-[color:var(--color-ink)]' : ''
          }`}
        >
          {/* 右上的发音按钮 (备用, 点卡片也能发音) */}
          {effectiveMode !== 'listen' && (
            <button
              onClick={(e) => { e.stopPropagation(); speak() }}
              title="读英文"
              className="absolute top-4 right-4 w-9 h-9 rounded-full border border-[color:var(--color-border)] flex items-center justify-center active:bg-[color:var(--color-surface)] transition-colors z-10"
            >
              <Volume2 className="w-4 h-4 text-[color:var(--color-ink)]" strokeWidth={1.75} />
            </button>
          )}

          {/* 本次 session 内评分累计 */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-4 text-sm font-bold tabular-nums">
            <div className="flex items-center gap-1 text-[color:var(--color-ink)]">
              <Check className="w-3.5 h-3.5" strokeWidth={2.5} />
              <span>{gradeStats.good}</span>
            </div>
            <div className="flex items-center gap-1 text-[color:var(--color-muted)]">
              <HelpCircle className="w-3.5 h-3.5" strokeWidth={2} />
              <span>{gradeStats.hard}</span>
            </div>
            <div className="flex items-center gap-1 text-[color:var(--color-muted)]">
              <X className="w-3.5 h-3.5" strokeWidth={2} />
              <span>{gradeStats.again}</span>
            </div>
          </div>

          <div ref={cardInnerRef} className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-6">
            {renderMain()}
            <div className="h-px w-12 bg-[color:var(--color-border)] my-1" />
            {revealed ? (
              renderAnswer()
            ) : (
              <div className="flex flex-col items-center gap-2 animate-pulse">
                <div className="text-7xl font-extrabold text-[color:var(--color-muted)] opacity-25 select-none">?</div>
                <div className="text-xs text-[color:var(--color-muted)] opacity-60">点一下 / 按空格 揭示</div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* ===== 底部按钮: 未揭示→大"答案"按钮; 已揭示→3 个评分按钮 ===== */}
      <footer className="px-4 pb-20 pt-2 shrink-0">
        {!revealed ? (
          <button
            onClick={() => {
              setRevealed(true)
              setTimeout(() => speak(), 50)
            }}
            className="h-14 w-full rounded-2xl bg-[color:var(--color-ink)] text-white font-extrabold active:scale-[0.98] transition-transform flex items-center justify-center"
          >
            答案
          </button>
        ) : (
          <div className="grid grid-cols-3 gap-3">
            <button
              onClick={() => handleRate('again')}
              title="忘了 (快捷键 1)"
              disabled={transitioning}
              className="h-14 rounded-2xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] text-[color:var(--color-ink)] flex items-center justify-center active:bg-[color:var(--color-ink)] active:text-[color:var(--color-surface)] active:border-[color:var(--color-ink)] transition-colors disabled:opacity-50 relative"
            >
              <X className="w-6 h-6" strokeWidth={2} />
            </button>
            <button
              onClick={() => handleRate('hard')}
              title="模糊 (快捷键 2)"
              disabled={transitioning}
              className="h-14 rounded-2xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] text-[color:var(--color-ink)] flex items-center justify-center active:bg-[color:var(--color-ink)] active:text-[color:var(--color-surface)] active:border-[color:var(--color-ink)] transition-colors disabled:opacity-50 relative"
            >
              <HelpCircle className="w-6 h-6" strokeWidth={2} />
            </button>
            <button
              onClick={() => handleRate('good')}
              title="认识 (快捷键 3)"
              disabled={transitioning}
              className="h-14 rounded-2xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] text-[color:var(--color-ink)] flex items-center justify-center active:bg-[color:var(--color-ink)] active:text-[color:var(--color-surface)] active:border-[color:var(--color-ink)] transition-colors disabled:opacity-50 relative"
            >
              <Check className="w-6 h-6" strokeWidth={2.5} />
            </button>
          </div>
        )}
      </footer>
    </div>
  )
}
