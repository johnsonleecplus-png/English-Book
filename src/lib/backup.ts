// JSON 备份与恢复 (Phase 7.1)
// - 导出: cards + reviews + settings + sessions 全部数据
// - 导入: 校验 + 替换 (覆盖前建议先导出一份)
// - 格式: 1.0 (含 schemaVersion 字段, 未来可演进)

import { getDB } from './db'
import type { Card, Review, Settings, Session } from './types'

const BACKUP_VERSION = '1.0'
const BACKUP_MIME = 'application/json'
const BACKUP_EXT = '.english-book.json'

export interface BackupPayload {
  $type: 'english-book-backup'
  $version: string
  $exportedAt: number
  cards: Card[]
  reviews: Review[]
  settings: Settings[]
  sessions: Session[]
}

/** 导出全部数据为 JSON 字符串 */
export async function buildBackup(): Promise<string> {
  const db = await getDB()
  const [cards, reviews, settings, sessions] = await Promise.all([
    db.getAll('cards'),
    db.getAll('reviews'),
    db.getAll('settings'),
    db.getAll('sessions'),
  ])
  const payload: BackupPayload = {
    $type: 'english-book-backup',
    $version: BACKUP_VERSION,
    $exportedAt: Date.now(),
    cards,
    reviews,
    settings,
    sessions,
  }
  return JSON.stringify(payload, null, 2)
}

/** 触发浏览器下载, 文件名格式: english-book-YYYY-MM-DD.json */
export function downloadBackup(json: string): void {
  const today = new Date().toISOString().slice(0, 10)
  const blob = new Blob([json], { type: BACKUP_MIME })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `english-book-${today}${BACKUP_EXT}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/** 解析 JSON 字符串, 校验结构, 返回 payload 或 throw */
export function parseBackup(json: string): BackupPayload {
  let obj: unknown
  try {
    obj = JSON.parse(json)
  } catch (e) {
    throw new Error('JSON 解析失败: 文件可能已损坏')
  }
  if (typeof obj !== 'object' || obj === null) {
    throw new Error('备份格式错误: 根节点不是对象')
  }
  const p = obj as Record<string, unknown>
  if (p.$type !== 'english-book-backup') {
    throw new Error('备份格式错误: 不是 English Book 备份文件')
  }
  if (typeof p.$version !== 'string') {
    throw new Error('备份格式错误: 缺版本号')
  }
  if (!Array.isArray(p.cards) || !Array.isArray(p.reviews) ||
      !Array.isArray(p.settings) || !Array.isArray(p.sessions)) {
    throw new Error('备份格式错误: 4 张表 (cards/reviews/settings/sessions) 必须都是数组')
  }
  return p as unknown as BackupPayload
}

/** 从 payload 恢复数据, 覆盖当前 IDB */
export async function restoreBackup(payload: BackupPayload): Promise<void> {
  const db = await getDB()
  // 4 张表清空 + 重写 (用单一 transaction 保证原子性)
  const tx = db.transaction(['cards', 'reviews', 'settings', 'sessions'], 'readwrite')
  const cardsStore = tx.objectStore('cards')
  const reviewsStore = tx.objectStore('reviews')
  const settingsStore = tx.objectStore('settings')
  const sessionsStore = tx.objectStore('sessions')

  await cardsStore.clear()
  await reviewsStore.clear()
  await settingsStore.clear()
  await sessionsStore.clear()

  for (const c of payload.cards) await cardsStore.put(c)
  for (const r of payload.reviews) await reviewsStore.put(r)
  for (const s of payload.settings) await settingsStore.put(s)
  for (const s of payload.sessions) await sessionsStore.put(s)

  await tx.done
}
