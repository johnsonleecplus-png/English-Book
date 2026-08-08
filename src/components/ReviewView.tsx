// 复习模式: 对今日模糊/不会的单词进行循环不规则刷新复习
// Johnson 决策 2026-08-08
// - 队列来源: lib/progress.ts 的 getReviewableCards() (fuzzy + struggling)
// - good → 标记完成, 不再循环
// - again/hard → 不规则刷新到当前位置后 1-5 张位置
// - 全部完成 → 自动返回 (调用 onFinish)
// - 用户可随时点 "结束复习" 提前返回

import { useEffect, useRef, useState } from 'react'
import { Image, Languages, Volume2, X, HelpCircle, Check, Shuffle, ArrowLeft, Trophy } from 'lucide-react'
import type { Card, Grade, Mode } from '../lib/types'
import { useReviewQueue } from '../hooks/useReviewQueue'
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

interface ReviewViewProps {
  cards: Card[]
  onFinish: () => void
  grayscale?: boolean
}

export function ReviewView({ cards, onFinish, grayscale = false }: ReviewViewProps) {
  const queue = useReviewQueue(cards)
  const [mode, setMode] = useState<Mode>('en2cn')
  const [mixMode, setMixMode] = useState<Mode>('en2cn')
  const [feedback, setFeedback] = useState<'good' | 'again' | null>(null)
  const [transitioning, setTransitioning] = useState(false)
  const [revealed, setRevealed] = useState(false)
  const cardRef = useRef<HTMLDivElement>(null)
  const cardInnerRef = useRef<HTMLDivElement>(null)

  const entry = queue.current
  const word = entry?.card
  const effectiveMode: Mode = mode === 'mix' ? mixMode : mode

  // 切混合模式: 每次新卡随机选基础模式
  useEffect(() => {
    if (mode === 'mix') {
      setMixMode(BASE_MODES[Math.floor(Math.random() * BASE_MODES.length)])
    }
  }, [mode, queue.idx])

  // 自动播音策略: 同 CardView (listen + en2cn 自动播)
  useEffect(() => {
    if (!word) return
    if (effectiveMode === 'listen' || effectiveMode === 'en2cn') {
      const t = setTimeout(() => speak(), 50)
      return () => clearTimeout(t)
    }
  }, [word?.id, effectiveMode])

  // 切到新卡 → 重置 revealed
  useEffect(() => {
    setRevealed(false)
  }, [word?.id])

  // 自动结束: 全部卡片都评过 good → 1.5 秒后自动返回
  useEffect(() => {
    if (queue.finished) {
      const t = setTimeout(onFinish, 1500)
      return () => clearTimeout(t)
    }
  }, [queue.finished, onFinish])

  // 键盘快捷键
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement | null)?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA') return
      if ((e.target as HTMLElement | null)?.isContentEditable) return
      if (!entry) return
      if (transitioning) return
      if (e.code === 'Escape') {
        e.preventDefault()
        onFinish()
        return
      }
      if (e.code === 'Space') {
        e.preventDefault()
        if (!revealed) {
          setRevealed(true)
          setTimeout(() => speak(), 50)
        }
        return
      }
      if (!revealed) return
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
  }, [entry, transitioning, revealed, onFinish])

  function speak() {
    if (!word) return
    const w = word.word.toLowerCase()
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
        }
      })
      .catch(() => {})
  }

  async function handleRate(grade: Grade) {
    if (transitioning || !entry) return
    setTransitioning(true)
    setFeedback(grade === 'again' ? 'again' : 'good')
    if (grade === 'again') {
      cardRef.current?.classList.add('animate-shake')
      setTimeout(() => cardRef.current?.classList.remove('animate-shake'), 400)
    }
    // 仅更新 SM-2 (applyGrade), 不计 session (review 是独立机制)
    await queue.rate(grade)

    setTimeout(() => {
      queue.advance()
      setFeedback(null)
      setTransitioning(false)
    }, 600)
  }

  // 加载中
  if (queue.loading) {
    return (
      <div className="h-screen flex items-center justify-center text-[color:var(--color-muted)]" style={{ height: '100dvh' }}>
        加载复习题中...
      </div>
    )
  }

  // 全部完成 → 显示 1.5s 后自动返回
  if (queue.finished) {
    return (
      <div className="h-screen flex flex-col items-center justify-center gap-4 px-6 pb-24 text-center" style={{ height: '100dvh' }}>
        <div className="text-7xl animate-pop">🎉</div>
        <div>
          <div className="text-3xl font-extrabold text-[color:var(--color-ink)]">复习完成!</div>
          <div className="text-sm text-[color:var(--color-muted)] mt-1">
            本次复习 {queue.initialCount} 词, 全部掌握
          </div>
        </div>
        <div className="text-xs text-[color:var(--color-muted)]">即将返回设置页...</div>
      </div>
    )
  }

  // 渲染卡片内容
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

  // 复习进度: 已完成 / 初始
  const reviewPct = queue.initialCount === 0 ? 0 : Math.round((queue.completed / queue.initialCount) * 100)

  return (
    <div className="h-screen flex flex-col overflow-hidden" style={{ height: '100dvh' }}>
      {/* ===== 顶部状态栏: 复习模式标识 + 进度 + 退出 ===== */}
      <header className="px-4 pt-4 pb-2 shrink-0">
        <div className="flex items-center gap-2 mb-3">
          {/* 返回 / 退出复习按钮 */}
          <button
            onClick={onFinish}
            title="结束复习 (Esc)"
            className="w-9 h-9 rounded-full border border-[color:var(--color-border)] flex items-center justify-center active:bg-[color:var(--color-surface)] shrink-0"
          >
            <ArrowLeft className="w-4 h-4 text-[color:var(--color-ink)]" strokeWidth={1.75} />
          </button>

          {/* 复习模式标签 */}
          <div className="flex items-center gap-1 text-xs font-bold text-[color:var(--color-muted)]">
            <Trophy className="w-3.5 h-3.5" strokeWidth={1.75} />
            复习模式
          </div>

          <div className="flex-1" />

          {/* 进度: X/Y 已掌握 */}
          <div className="text-xs text-[color:var(--color-muted)] font-bold tabular-nums">
            <span className="text-[color:var(--color-ink)]">{queue.completed}</span>
            <span> / {queue.initialCount}</span>
          </div>
        </div>

        {/* 进度条 */}
        <div className="h-1.5 rounded-full bg-[color:var(--color-border)] overflow-hidden mb-3">
          <div
            className="h-full bg-[color:var(--color-success)] transition-all duration-300"
            style={{ width: `${reviewPct}%` }}
          />
        </div>

        {/* 模式 tabs */}
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

      {/* ===== 卡片区 ===== */}
      <main className="flex-1 px-4 py-4 flex items-center justify-center overflow-hidden">
        <div
          ref={cardRef}
          onClick={() => {
            if (!revealed) {
              setRevealed(true)
              setTimeout(() => speak(), 50)
            } else {
              speak()
            }
          }}
          className={`relative w-full max-w-md rounded-3xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-6 h-full max-h-[560px] overflow-hidden cursor-pointer transition-all ${
            feedback ? 'border-[color:var(--color-ink)]' : ''
          }`}
        >
          {effectiveMode !== 'listen' && (
            <button
              onClick={(e) => { e.stopPropagation(); speak() }}
              title="读英文"
              className="absolute top-4 right-4 w-9 h-9 rounded-full border border-[color:var(--color-border)] flex items-center justify-center active:bg-[color:var(--color-surface)] transition-colors z-10"
            >
              <Volume2 className="w-4 h-4 text-[color:var(--color-ink)]" strokeWidth={1.75} />
            </button>
          )}

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

      {/* ===== 底部按钮 ===== */}
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
              className="h-14 rounded-2xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] text-[color:var(--color-ink)] flex items-center justify-center active:bg-[color:var(--color-ink)] active:text-[color:var(--color-surface)] active:border-[color:var(--color-ink)] transition-colors disabled:opacity-50"
            >
              <X className="w-6 h-6" strokeWidth={2} />
            </button>
            <button
              onClick={() => handleRate('hard')}
              title="模糊 (快捷键 2)"
              disabled={transitioning}
              className="h-14 rounded-2xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] text-[color:var(--color-ink)] flex items-center justify-center active:bg-[color:var(--color-ink)] active:text-[color:var(--color-surface)] active:border-[color:var(--color-ink)] transition-colors disabled:opacity-50"
            >
              <HelpCircle className="w-6 h-6" strokeWidth={2} />
            </button>
            <button
              onClick={() => handleRate('good')}
              title="认识 (快捷键 3)"
              disabled={transitioning}
              className="h-14 rounded-2xl border-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)] text-[color:var(--color-ink)] flex items-center justify-center active:bg-[color:var(--color-ink)] active:text-[color:var(--color-surface)] active:border-[color:var(--color-ink)] transition-colors disabled:opacity-50"
            >
              <Check className="w-6 h-6" strokeWidth={2.5} />
            </button>
          </div>
        )}
      </footer>
    </div>
  )
}