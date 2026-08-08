import { openDB, type DBSchema, type IDBPDatabase } from 'idb'
import type { Card, Review, Settings, Session } from './types'

// DBSchema 给 idb 提供类型安全的 store/index 访问
interface EBDB extends DBSchema {
  cards: {
    key: string
    value: Card
    indexes: { 'by-due': number; 'by-firstSeen': number }
  }
  reviews: {
    key: number
    value: Review
    indexes: { 'by-card': string; 'by-session': string; 'by-time': number }
  }
  settings: {
    key: string
    value: Settings
  }
  sessions: {
    key: string
    value: Session
    indexes: { 'by-date': string; 'by-endedAt': number }
  }
}

const DB_NAME = 'english-book'
const DB_VERSION = 1

let _dbPromise: Promise<IDBPDatabase<EBDB>> | null = null

export function getDB(): Promise<IDBPDatabase<EBDB>> {
  if (!_dbPromise) {
    _dbPromise = openDB<EBDB>(DB_NAME, DB_VERSION, {
      upgrade(db, oldVersion) {
        // Phase 1 schema v1
        if (oldVersion < 1) {
          const cards = db.createObjectStore('cards', { keyPath: 'id' })
          cards.createIndex('by-due', 'due')
          cards.createIndex('by-firstSeen', 'firstSeen')

          const reviews = db.createObjectStore('reviews', { keyPath: 'id', autoIncrement: true })
          reviews.createIndex('by-card', 'cardId')
          reviews.createIndex('by-session', 'sessionId')
          reviews.createIndex('by-time', 'reviewedAt')

          db.createObjectStore('settings', { keyPath: 'key' })

          const sessions = db.createObjectStore('sessions', { keyPath: 'id' })
          sessions.createIndex('by-date', 'date')
          sessions.createIndex('by-endedAt', 'endedAt')
        }
        // 未来版本: if (oldVersion < 2) { ... }
      },
    })
  }
  return _dbPromise
}

export type { EBDB }
