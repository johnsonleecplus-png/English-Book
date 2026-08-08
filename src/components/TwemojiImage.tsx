// EmojiView: 把 emoji 字符渲染成"浏览器原生"emoji (unicode.org Browser 版本)
// 娃在 Android 看到 Noto, 在 iOS 看到 Apple Color — 都是 OS 原生字体
// 不依赖外部 SVG/PNG, 0 字节, 跨平台

interface EmojiViewProps {
  emoji: string
  className?: string
  size?: number  // px
}

/**
 * EmojiView: 纯字符渲染 (大小由 font-size 控制)
 * - Browser (Android) = Noto Color Emoji
 * - Browser (iOS)    = Apple Color Emoji
 * - Browser (Windows) = Segoe UI Emoji
 * 跟娃日常微信/短信看到的一致, 学习迁移最高
 */
export function EmojiView({ emoji, className, size = 128 }: EmojiViewProps) {
  return (
    <span
      className={className}
      style={{
        fontSize: `${size}px`,
        lineHeight: 1,
        fontFamily: '"Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", "Twemoji Mozilla", sans-serif',
      }}
    >
      {emoji}
    </span>
  )
}

// 旧名 TwemojiImage 保留为 alias (CardView 还在用, 后面统一改)
export const TwemojiImage = EmojiView
