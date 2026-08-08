// 底部 Tab Bar (Phase: 移动端导航)
// - 3 个常驻 tab: 今日 / 历史 / 设置
// - 当前页高亮 (背景 + icon 颜色)
// - 全部用 lucide 单色 stroke icon, 跟整体黑白灰调一致
// - CardView / ConfirmTarget 屏不显示 (避免误触)

import { Calendar, Home, Settings as SettingsIcon } from 'lucide-react'

export type TabId = 'home' | 'history' | 'settings'

interface TabBarProps {
  active: TabId
  onChange: (tab: TabId) => void
}

const TABS: { id: TabId; label: string; Icon: typeof Home }[] = [
  { id: 'home',     label: '今日', Icon: Home },
  { id: 'history',  label: '历史', Icon: Calendar },
  { id: 'settings', label: '设置', Icon: SettingsIcon },
]

export function TabBar({ active, onChange }: TabBarProps) {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 border-t-2 border-[color:var(--color-border)] bg-[color:var(--color-surface)]/95 backdrop-blur-sm"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      <div className="max-w-md mx-auto grid grid-cols-3">
        {TABS.map(({ id, label, Icon }) => {
          const isActive = id === active
          return (
            <button
              key={id}
              onClick={() => onChange(id)}
              className={`flex flex-col items-center justify-center gap-1 py-2.5 transition-colors ${
                isActive
                  ? 'text-[color:var(--color-ink)]'
                  : 'text-[color:var(--color-muted)] active:text-[color:var(--color-ink)]'
              }`}
            >
              <Icon
                className="w-6 h-6"
                strokeWidth={isActive ? 2.25 : 1.75}
                fill={isActive ? 'currentColor' : 'none'}
                fillOpacity={isActive ? 0.12 : 0}
              />
              <span className={`text-[11px] font-bold tracking-wider ${isActive ? 'font-extrabold' : ''}`}>
                {label}
              </span>
              {isActive && (
                <span className="absolute bottom-0 h-0.5 w-10 rounded-full bg-[color:var(--color-ink)]" />
              )}
            </button>
          )
        })}
      </div>
    </nav>
  )
}
