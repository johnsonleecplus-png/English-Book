// MOCK_WORDS — Phase 1 阶段的演示词表
// 5 个硬编码词, Phase 3 真实词表接入后会替换
// (从 App.tsx:5-11 抽出, 字段保持原 4 个, 不加 image 字段 — Phase 6 再说)

import type { Card } from './types'

export const MOCK_WORDS: Pick<Card, 'id' | 'word' | 'pos' | 'cn' | 'example'>[] = [
  { id: 'develop',     word: 'develop',     pos: 'v.',    cn: '发展, 开发', example: 'The city is developing rapidly.' },
  { id: 'although',    word: 'although',    pos: 'conj.', cn: '虽然, 尽管', example: 'Although it rained, we went out.' },
  { id: 'opportunity', word: 'opportunity', pos: 'n.',    cn: '机会, 时机', example: 'A great opportunity to learn.' },
  { id: 'kindness',    word: 'kindness',    pos: 'n.',    cn: '善良, 仁慈', example: 'Thank you for your kindness.' },
  { id: 'achieve',     word: 'achieve',     pos: 'v.',    cn: '达到, 完成', example: 'She worked hard to achieve her dream.' },
]
