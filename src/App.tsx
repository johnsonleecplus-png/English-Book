import { useCallback, useEffect, useState } from 'react'
import { Home } from './components/Home'
import { History } from './components/History'
import { Settings } from './components/Settings'
import { CardView } from './components/CardView'
import { ConfirmTarget } from './components/ConfirmTarget'
import { Loading } from './components/Loading'
import { ReviewView } from './components/ReviewView'
import { TabBar, type TabId } from './components/TabBar'
import type { Card, Session } from './lib/types'
import { getActiveSession, startSession, endSession, bumpSessionStats } from './lib/session'
import { getStats, type Stats } from './lib/stats'
import { getProgress, type Progress } from './lib/progress'
import { getSettings, setDailyNewTarget } from './lib/queue'
import { ensureSeeded } from './lib/seed'

type Screen = 'loading' | 'home' | 'history' | 'settings' | 'confirm' | 'active' | 'review'

const DEFAULT_STATS: Stats = {
  todayNewTarget: 15,
  todayNewDone: 0,
  todayReviewDone: 0,
  todayTotalDone: 0,
  totalLearned: 0,
  streak: 0,
}

const DEFAULT_PROGRESS: Progress = {
  mastered: 0,
  fuzzy: 0,
  struggling: 0,
  unlearned: 0,
  total: 0,
  daysLeft: 0,
}

function App() {
  const [screen, setScreen] = useState<Screen>('loading')
  const [session, setSession] = useState<Session | null>(null)
  const [stats, setStats] = useState<Stats>(DEFAULT_STATS)
  const [progress, setProgress] = useState<Progress>(DEFAULT_PROGRESS)
  const [hasActive, setHasActive] = useState(false)
  const [defaultTarget, setDefaultTarget] = useState<number>(15)
  const [isFirstTime, setIsFirstTime] = useState(false)
  // 复习模式状态 (Johnson 决策 2026-08-08)
  const [reviewCards, setReviewCards] = useState<Card[]>([])

  /** 重新拉首页统计 + 活动 session */
  const refreshHome = useCallback(async () => {
    await ensureSeeded()
    const [s, st, prog, settings] = await Promise.all([
      getActiveSession(),
      getStats(),
      getProgress(),
      getSettings(),
    ])
    setStats(st)
    setProgress(prog)
    setHasActive(s !== null)
    setDefaultTarget(settings.dailyNewTarget)
    setIsFirstTime(st.totalLearned === 0)
  }, [])

  /** 初次加载: 决定去 Home 还是 CardView (loading 至少 1s) */
  useEffect(() => {
    let cancelled = false
    const startedAt = Date.now()
    const MIN_LOADING_MS = 1000

    void (async () => {
      let nextScreen: Screen = 'home'
      const active = await getActiveSession()
      if (cancelled) return
      if (active) {
        setSession(active)
        nextScreen = 'active'
      } else {
        await refreshHome()
        if (cancelled) return
      }

      const elapsed = Date.now() - startedAt
      if (elapsed < MIN_LOADING_MS) {
        await new Promise(r => setTimeout(r, MIN_LOADING_MS - elapsed))
        if (cancelled) return
      }
      setScreen(nextScreen)
    })()
    return () => { cancelled = true }
  }, [refreshHome])

  /** 进入 Home 时刷新统计 */
  useEffect(() => {
    if (screen === 'home') {
      void refreshHome()
    }
  }, [screen, refreshHome])

  /** 任意 tab 切换 */
  function navigateTab(tab: TabId) {
    if (tab === 'home' && hasActive && session) {
      setScreen('active')
      return
    }
    setScreen(tab)
  }

  /** 开始今日 → 跳 confirm */
  async function handleStart() {
    if (hasActive && session) {
      setScreen('active')
      return
    }
    await refreshHome()
    setScreen('confirm')
  }

  /** confirm → 写设置 + 开 session */
  async function handleConfirmTarget(n: number) {
    await setDailyNewTarget(n)
    const s = await startSession(n)
    setSession(s)
    setHasActive(true)
    setScreen('active')
  }

  /** 评分后更新 session stats */
  async function handleRate(isNew: boolean) {
    if (!session) return
    const updated = await bumpSessionStats(session.id, isNew)
    if (updated) setSession(updated)
  }

  /** 结束 session */
  async function handleFinish() {
    if (session) {
      await endSession(session.id)
    }
    setSession(null)
    setHasActive(false)
    await refreshHome()
    setScreen('home')
  }

  /** 进入复习模式 (Johnson 决策 2026-08-08) */
  async function handleStartReview() {
    const { getReviewableCards } = await import('./lib/progress')
    const cards = await getReviewableCards()
    if (cards.length === 0) return  // 没有可复习的 (按钮应该已 disabled, 双重保险)
    setReviewCards(cards)
    setScreen('review')
  }

  /** 结束复习: 回到设置页, 刷新数据 */
  async function handleReviewFinish() {
    setReviewCards([])
    // 复习后部分卡片可能已掌握 (SM-2 更新), 重新拉 stats 让其他页面同步
    await refreshHome()
    setScreen('settings')
  }

  if (screen === 'loading') {
    return <Loading />
  }

  if (screen === 'home') {
    return (
      <>
        <Home stats={stats} progress={progress} hasActiveSession={hasActive} onStart={handleStart} />
        <TabBar active="home" onChange={navigateTab} />
      </>
    )
  }

  if (screen === 'history') {
    return (
      <>
        <History />
        <TabBar active="history" onChange={navigateTab} />
      </>
    )
  }

  if (screen === 'settings') {
    return (
      <>
        <Settings onStartReview={handleStartReview} />
        <TabBar active="settings" onChange={navigateTab} />
      </>
    )
  }

  if (screen === 'confirm') {
    return (
      <>
        <ConfirmTarget
          defaultTarget={defaultTarget}
          isFirstTime={isFirstTime}
          onConfirm={handleConfirmTarget}
        />
        <TabBar active="home" onChange={navigateTab} />
      </>
    )
  }

  if (screen === 'active' && session) {
    const url = new URL(window.location.href)
    const grayscale = url.searchParams.get('grayscale') === '1'
    return (
      <>
        <CardView
          key={session.id}
          session={session}
          onRate={handleRate}
          onFinish={handleFinish}
          grayscale={grayscale}
        />
        <TabBar active="home" onChange={navigateTab} />
      </>
    )
  }

  // 复习模式: 不渲染 TabBar (专注复习, 顶部有返回按钮)
  if (screen === 'review' && reviewCards.length > 0) {
    return (
      <ReviewView
        key={`review-${reviewCards.length}-${reviewCards[0]?.id ?? 'empty'}`}
        cards={reviewCards}
        onFinish={handleReviewFinish}
      />
    )
  }

  return null
}

export default App