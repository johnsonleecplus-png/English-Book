// 词 → emoji 视觉映射 (POC 已选定 emoji 优先路线, 0 KB, 浏览器原生, 抽象词更直观)
// 来源: src/data/wordEmojis.ts (1476 词, 跟 CSV 词表 1:1 对齐)
// 选 emoji 原则: 直接对应物 > 近义/隐喻; 去奖杯 (🥇 仅字面 gold); 抽象词标 null 让 UI 走 CN 文字兜底
// Lucide 兜底: emoji 不覆盖的极少数词 (主要是字母/数字/标点 等) 用 LineIcons

import { WORD_EMOJIS } from '../data/wordEmojis'

/**
 * 词 → emoji (POC 首选, 全 1476 词覆盖)
 * null = UI fallback 显示 CN 文字
 */
export { WORD_EMOJIS }

/**
 * 词 → Lucide icon 名称 (emoji 缺位时 fallback, 当前 emoji 覆盖率 ~99% 仅极少数留空)
 * 兜底: emoji = null 时 UI 调 getIconComponent
 */
export const WORD_ICONS: Record<string, string> = {
  // 5 MOCK 词 (emoji 都有, 留映射占位)
  develop:    'Hammer',
  although:   'CornerDownLeft',
  opportunity: 'Compass',
  kindness:   'Heart',
  achieve:    'Trophy',
  // 8 扩展词
  able:       'Shield',
  ability:    'Star',
  accept:     'Hand',
  accident:   'AlertTriangle',
  active:     'Zap',
  actor:      'User',
  praise:     'ThumbsUp',
  table:      'Table2',
  word:       'Type',
  surface:    'Layers',
}

// Lucide 兜底组件 (emoji 极少数 null 时用, 多数场景下不会触发)
import {
  Hammer, CornerDownLeft, Compass, Heart, Trophy,
  Shield, Star, Hand, AlertTriangle, Zap, User,
  ThumbsUp, Table2, Type, Layers,
} from 'lucide-react'
import type { ComponentType, SVGProps } from 'react'

type IconComp = ComponentType<SVGProps<SVGSVGElement> & { className?: string; strokeWidth?: number; size?: number }>

const ICON_COMPONENTS: Record<string, IconComp> = {
  Hammer, CornerDownLeft, Compass, Heart, Trophy,
  Shield, Star, Hand, AlertTriangle, Zap, User,
  ThumbsUp, Table2, Type, Layers,
}

export function getIconComponent(name: string | undefined): IconComp | null {
  if (!name) return null
  return ICON_COMPONENTS[name] ?? null
}

/**
 * 词 → emoji 查询 (UI 调用入口)
 * 返回 emoji 字符串, 或 null (UI 显示 CN 文字)
 */
export function getWordEmoji(word: string): string | null {
  return WORD_EMOJIS[word] ?? null
}
