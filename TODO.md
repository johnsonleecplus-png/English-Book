# TODO.md — English Book 路线图

> 写于 2026-08-03,按依赖顺序排,每个 Phase 独立可发布
> 最后更新: 2026-08-04 (Phase 5.1 词库进度 + Phase 3.2 TTS 全离线)

---

## Phase 1: SM-2 调度器 + IndexedDB 持久化 ✅

| # | 任务 | 状态 |
|---|---|---|
| 1.1 | `src/lib/scheduler.ts` —— SM-2 纯函数, ~40 行 | ✅ |
| 1.2 | `src/lib/db.ts` —— IndexedDB 封装 (用 `idb` 库) | ✅ |
| 1.3 | `src/lib/queue.ts` —— 每日 queue builder, 复习优先+新词补齐 | ✅ |
| 1.4 | 首次启动 seed MOCK_WORDS → IDB | ✅ |
| 1.5 | `App.tsx` 接入: rate() 改写,接 IDB | ✅ |
| 1.6 | 进度条改 "今日已完成 / 今日总量" | ✅ |
| 1.7 | 验收: 背 1 张 → 刷新 → due 日期还在 | ✅ |

## Phase 1.5: Home 屏 + Session 状态机 ✅

| # | 任务 | 状态 |
|---|---|---|
| 1.5.1 | Home 页: 今日 X 词 + 连续打卡 + 累计 + [开始] 按钮 | ✅ |
| 1.5.2 | `sessions` 表 | ✅ |
| 1.5.3 | session 状态机: 无→active→completed | ✅ |
| 1.5.4 | 24h 续 session | ✅ |

## Phase 2: 每日配额设置 UI ✅ (走 ConfirmTarget 屏)

| # | 任务 | 状态 |
|---|---|---|
| 2.1 | Confirm 屏 (Home → 选目标 → 开始) | ✅ |
| 2.2 | 5 / 15 / 30 / 50 / 100 chips + 自定义输入 1-200 | ✅ |
| 2.3 | 旧值利旧 (上次目标作默认) + 首次使用提示 | ✅ |
| 2.4 | 写 `settings.dailyNewTarget` + 实时生效 | ✅ |

---

## Phase 3: 真实词表 ✅ (3.2 扩展到 1711 词 + 227 词组)

| # | 任务 | 状态 |
|---|---|---|
| 3.1 | 解析 CSV → `src/data/vocabSeed.ts` (1711 条) | ✅ |
| 3.2 | TTS 预录 (Piper en_US-amy-medium, 64kbps mono 22050Hz) | ✅ 2026-08-04 |
| 3.2.1 | although / opportunity 补 TTS | ✅ 2026-08-04 |
| 3.2.2 | 227 词组音频重命名 + 词组入库 (43 缺词 + 227 词组) | ✅ 2026-08-04 |
| 3.2.3 | CardView 完全离线 (删 Web Speech fallback) | ✅ 2026-08-04 |
| 3.2.4 | seed.ts 老用户 backfill 270 新卡 (不覆盖学习状态) | ✅ 2026-08-04 |

**当前卡片总数**: 1711 (vocabSeed) + 5 MOCK = **1716 卡**

---

## Phase 4: PWA 化 (能装到桌面) ✅ 2026-08-04

| # | 任务 | 状态 |
|---|---|---|
| 4.1 | `vite-plugin-pwa` 接入 (1.3.0) | ✅ |
| 4.2 | `manifest.webmanifest` + 4 种图标 (192/512/maskable/apple-touch) | ✅ |
| 4.3 | iOS Safari "添加到主屏幕" 元数据 (apple-capable/title/icon) | ✅ |
| 4.4 | 离线可用验证 (断网 reload + audio + manifest 都 OK) | ✅ |

**PWA 配置决策** (2026-08-04 拍板):
- `registerType: 'autoUpdate'` —— 新版本自动激活, 不弹提示
- `display: 'standalone'` —— 装桌面后无浏览器 UI, 像原生 app
- `orientation: 'portrait'` —— 锁定竖屏 (跟移动端设计一致)
- `theme_color: '#1d1d1f'` —— 状态栏深灰 (跟 design system 一致)
- `background_color: '#f5f5f7'` —— 启动屏 Apple 浅灰
- workbox `precache: 1733 entries / 12.06 MB` —— 全部 app shell + 1717 audio
- runtime cache: `/audio/.*\.(mp3|wav)` → CacheFirst 1 年有效期

**离线验证** (screenshots/iphone/phase4/):
- `_capture_phase4.py`: manifest 200 / SW activated / 4 icons / audio 200 / iOS meta
- `_capture_phase4_offline.py`: 断网后 reload 成功 + audio 仍 7567 bytes + manifest 200

## Phase 5: 指标可视化

| # | 任务 | 状态 |
|---|---|---|
| 5.1 | **词库进度: 4 档分类 + 剩余天数** (掌握/模糊/不会/未学) | ✅ 2026-08-04 |
| 5.2 | **7 周热力图** (类 GitHub contribution graph, 49 天 grid) | ✅ 2026-08-04 |
| 5.3 | 详细进度 (点 4 档卡片进列表) | ❌ |
| 5.4 | 遗忘曲线小图 (可选) | ❌ |

**5.1 决策** (2026-08-04 拍板):
- 4 档判定 (纯 cards 字段, 不读 reviews):
  - **未学**: `firstSeen === 0`
  - **不会**: `firstSeen > 0 && (reps < 3 || ef < 2.0)`
  - **模糊**: `firstSeen > 0 && reps >= 3 && 2.0 ≤ ef < 2.5`
  - **掌握**: `firstSeen > 0 && reps >= 3 && ef ≥ 2.5`
- 剩余天数 = `ceil(unlearned / dailyNewTarget)`
- UI: Home 屏底部 section, 顶部 1 条横向分段进度条 (4 段: 绿/黄/红/灰) + 2x2 数字网格 + 底部剩余天数

**5.2 决策** (2026-08-04 拍板):
- 7 周 x 7 天 grid (49 天), 起始对齐周一
- 颜色强度 5 档: 0/1-2/3-5/6-10/11+ (success 色 + opacity)
- 今天加 ring 强调
- 右侧显示"近 7 天 X 词"
- 底部"少/多"图例 (5 格)

## Phase 6: 模式补完

| # | 任务 | 状态 | 备注 |
|---|---|---|---|
| 6.1 | `image` 模式 emoji (1476 词全覆盖) | ✅ 2026-08-03 | Browser-native emoji, 0KB |
| 6.2 | `listen` 模式预录 Piper TTS | ✅ 2026-08-04 | 完全离线 |
| 6.3 | `mix` 模式与 SM-2 协调 | ✅ | 每次新卡随机选基础模式 |
| 6.4 | **键盘快捷键** (Space/Enter 揭示 + 1/2/3 评分) | ✅ 2026-08-04 | 按钮上角小 kbd 提示 |
| 6.5 | **复习完毕动画** (🎉 pop + 4 emoji 飘动 + 评分统计) | ✅ 2026-08-04 | 认识% + good/hard/again 计数 |

## Phase 7: 跨设备同步 (可选, 按需)

| # | 任务 | 状态 | 备注 |
|---|---|---|---|
| 7.1 | **导出/导入 JSON 备份** (本地文件) | ✅ 2026-08-04 | $type + $version 1.0, 4 张表全量 |
| 7.2 | Notion API 同步 (进度推到 Notion 页) | ❌ | 2-3h |

---

## 不做的事 (过度设计预警)

- ❌ 后端 (IndexedDB 已够)
- ❌ 自创调度算法 (SM-2 足够)
- ❌ 多 profile / 多用户 (单人用)
- ❌ 复杂数据分析 (够用即可, 不上 BI)
- ❌ 显式 "保存" 按钮 (现代 PWA 标配自动保存)
- ❌ Web Speech 兜底 (必须完全离线, 缺音频 console.warn)

---

## 当前进度条

```
[█████████████████░░░] 90%   整体进度 (Phase 1-7.1, 仅 5.3/5.4/7.2 未做)
```

各 phase:
- [x] Phase 1 SM-2 + IDB
- [x] Phase 1.5 Home 屏 + Session
- [x] Phase 2 每日配额 (Confirm 屏)
- [x] Phase 3 真实词表 (1711 词 + 227 词组 + TTS 全离线)
- [x] Phase 4 PWA 化 (manifest + 4 icons + iOS meta + 离线验证)
- [▓] Phase 5 指标可视化 (5.1/5.2 ✅ / 5.3/5.4 ❌)
- [x] Phase 6 模式补完 (6.1/6.2/6.3/6.4/6.5 ✅)
- [▓] Phase 7 跨设备同步 (7.1 ✅ / 7.2 ❌)

---

## 一次性对话记录 (本次决策)

| 决策点 | 结论 | 时间 |
|---|---|---|
| 存储 | IndexedDB (不用后端, 不用 Notion, 不用 localStorage) | 2026-08-03 |
| 调度算法 | SM-2 (不用 FSRS, 不用自创) | 2026-08-03 |
| 每日配额 | 1-200 (ConfirmTarget 5 档 chips + 自定义) | 2026-08-03 |
| 进入/保存/退出 | 自动保存 + 24h 内续 session (无显式 save 按钮) | 2026-08-03 |
| Home 屏 | 强烈建议加 (Phase 1.5 塞进 Phase 1) | 2026-08-03 |
| 项目名 | English Book | 2026-08-03 |
| 词表数据源 | 上海中考完整版 CSV (1608 词 + 285 词组) → 1711 净入库 | 2026-08-04 |
| TTS 引擎 | Piper en_US-amy-medium (本地, 22050Hz mono, 64kbps MP3) | 2026-08-04 |
| 词条分类阈值 | 掌握 ef≥2.5 && reps≥3 / 不会 ef<2.0 \|\| reps<3 | 2026-08-04 |
| 进度 4 档 | 掌握 / 模糊 / 不会 / 未学 (纯 cards 字段) | 2026-08-04 |
| PWA 引擎 | vite-plugin-pwa 1.3.0 + workbox (autoUpdate, display=standalone) | 2026-08-04 |
| PWA 图标 | SVG favicon → 192/512/maskable/apple-touch (sharp 生成) | 2026-08-04 |
| PWA 预缓存 | 全部 app shell + 1717 audio (12 MB) / audio CacheFirst 1 年 | 2026-08-04 |
| 热力图 5.2 | 7 周 x 7 天 (49 天) / 颜色 5 档 / 今天 ring 强调 | 2026-08-04 |
| 键盘快捷键 6.4 | Space/Enter 揭示 / 1/2/3 评 again/hard/good / 按钮上小 kbd 提示 | 2026-08-04 |
| 完成动画 6.5 | 🎉 animate-pop + 4 个 bounce emoji (⭐✨🏆💪) + 认识% 统计 | 2026-08-04 |
| 备份格式 7.1 | JSON $type='english-book-backup' $version='1.0' / 4 张表 (cards/reviews/settings/sessions) | 2026-08-04 |
