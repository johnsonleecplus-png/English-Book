// ============================================================================
// SM-2 间隔重复算法 (SuperMemo 2)
// ----------------------------------------------------------------------------
// 算法由 Piotr Woźniak 于 1985 年提出, 在 1990 年正式发表:
//
//   Woźniak, P. A. (1990). Optimization of repetition spacing in the
//   practice of learning. Acta Neurobiologiae Experimentalis, 50, 197-201.
//
// 算法本身不收版权费, 但 SuperMemo 官方要求使用者在应用中注明出处
// (已在 Settings 页面 "致谢" 区块标注, 详见
// https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-supermemo-method)
//
// 本文件为本项目对 SM-2 的自定义实现, 适配单词卡场景:
// - good:   reps 0→1 (interval=1) / reps 1→2 (interval=6) / reps≥2 (interval = prev * ef)
// - hard:   interval *= 1.2 (下限 1), ef -= 0.15, reps += 1
// - again:  重置 reps=0, interval=1, ef -= 0.2
// ============================================================================
import type { Card, Grade } from './types'

const EF_MIN = 1.3
const DAY_MS = 24 * 60 * 60 * 1000

export interface ScheduleResult {
  ef: number
  interval: number
  reps: number
  due: number
}

/**
 * Pure SM-2 update for one card.
 * - good:  reps 0→1 (interval=1) / reps 1→2 (interval=6) / reps≥2 (interval = prev * ef)
 *          ef 不变
 * - hard:  interval *= 1.2 (下限 1), ef -= 0.15, reps += 1
 * - again: 重置 reps=0, interval=1, ef -= 0.2
 *
 * 详细规则见 TODO.md Phase 1 关键决策。
 */
export function schedule(
  card: Pick<Card, 'ef' | 'interval' | 'reps'>,
  grade: Grade,
  now: number = Date.now(),
): ScheduleResult {
  let { ef, interval, reps } = card

  if (grade === 'again') {
    reps = 0
    interval = 1
    ef = Math.max(EF_MIN, ef - 0.2)
  } else if (grade === 'hard') {
    interval = Math.max(1, Math.round(interval * 1.2))
    ef = Math.max(EF_MIN, ef - 0.15)
    reps += 1
  } else {
    // good
    if (reps === 0) {
      interval = 1
    } else if (reps === 1) {
      interval = 6
    } else {
      interval = Math.round(interval * ef)
    }
    reps += 1
  }

  const due = now + interval * DAY_MS
  return { ef, interval, reps, due }
}
