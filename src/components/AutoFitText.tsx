import { useEffect, useRef, useState } from 'react'

/**
 * AutoFitText: 自动选字号, 保证单行不换行 / 不超宽
 *
 * - 给定候选字号列表 (从大到小), 测渲染后 scrollWidth 是否超出容器, 超过就降一档
 * - 词组 (含空格) 即使超长也允许 wrap, 字号不缩
 * - 切卡 (text 变) 时重新测量
 */
type Props = {
  text: string
  className?: string  // 字号无关 class (text-center / font-bold / 等)
  sizes: string[]     // 候选 Tailwind 字号 class, 从大到小, 如 ['text-6xl', 'text-5xl', 'text-4xl']
  parentRef?: React.RefObject<HTMLElement | null>  // 容器 ref (卡片 div)
}

export function AutoFitText({ text, className = '', sizes, parentRef }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const [picked, setPicked] = useState(sizes[0])

  useEffect(() => {
    const el = ref.current
    const parent = parentRef?.current
    if (!el || !parent) return
    // 词组 (含空格) 不缩字号, 允许 wrap
    if (text.includes(' ')) {
      setPicked(sizes[sizes.length - 1])
      return
    }
    // 单字 / 单词: 测量 scrollWidth, 找最大字号使不超 parent.clientWidth
    // 临时设最大字号测
    const max = sizes[0]
    el.style.fontSize = ''
    el.className = `whitespace-nowrap ${className} ${max}`.trim()
    const maxW = el.scrollWidth
    const limit = parent.clientWidth - 16  // 留 8px×2 padding
    if (maxW <= limit) {
      setPicked(max)
      return
    }
    // 降一档再测
    for (let i = 1; i < sizes.length; i++) {
      el.className = `whitespace-nowrap ${className} ${sizes[i]}`.trim()
      if (el.scrollWidth <= limit) {
        setPicked(sizes[i])
        return
      }
    }
    // 都不行就用最小
    setPicked(sizes[sizes.length - 1])
  }, [text, ...sizes, parentRef])

  return (
    <div
      ref={ref}
      className={`whitespace-nowrap ${className} ${picked}`.trim()}
    >
      {text}
    </div>
  )
}
