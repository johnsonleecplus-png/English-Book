// 加载页 (Phase: 设计感启动页)
// - 显示: App 初次启动 / 切 tab 时短暂的 IDB 读取
// - 设计: final-3-poster.png (鸟 + WE CAN DO IT! + FOR VOCAB? + 进度点)
// - 整张 PNG 作为图片, 9:16 比例, 白底
// - 加轻微的淡入 + 鸟身体微微脉冲, 让加载感觉"活的"

import { useEffect, useState } from 'react'

export function Loading() {
  // 防止 React StrictMode 双调用导致动画重置
  const [shown, setShown] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setShown(true), 30)
    return () => clearTimeout(t)
  }, [])

  return (
    <div className="min-h-full flex items-center justify-center bg-white">
      <div
        className="w-full max-w-md h-full flex items-center justify-center"
        style={{
          opacity: shown ? 1 : 0,
          transition: 'opacity 0.5s ease-out',
        }}
      >
        <img
          src="/loading.png"
          alt="English Book · 上海中考词汇 · WE CAN DO IT!"
          className="w-full h-full object-contain"
          style={{
            animation: 'loading-pulse 2.4s ease-in-out infinite',
            // 9:16 比例, 充满手机屏
            aspectRatio: '9 / 16',
            maxHeight: '100dvh',
          }}
        />
      </div>
    </div>
  )
}
