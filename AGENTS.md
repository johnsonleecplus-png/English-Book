# AGENTS.md — English Book

> 写给后续接手这个项目的 AI 编码 agent (Codex / Cursor / Aider / Devin / OpenCode / Gemini CLI 等)
> 同时也是给作者 Johnson 自己看的项目备忘录

## 项目是什么

**English Book** —— 上海中考英文词汇表的 PWA 背单词应用。
多邻国风的极简黑白灰设计,5 种学习模式,纯前端 + IndexedDB 存储,无后端。

## 技术栈

| 层 | 选型 | 版本 |
|---|---|---|
| 框架 | React | 19.2.8 |
| 语言 | TypeScript | ~6.0 |
| 构建 | Vite | 8.2 |
| 样式 | Tailwind CSS | 4.3 |
| 图标 | lucide-react | 1.28 |
| Lint | oxlint | 1.75 |
| 存储 | IndexedDB (idb ^8.0) | — |

## 目录结构 (Phase 1 完成后)

```
english-book/
├── src/
│   ├── App.tsx              # 状态机: loading | home | active
│   ├── main.tsx             # React 挂载
│   ├── components/
│   │   ├── Home.tsx         # P1.5 首页: 今日 / 连续 / 累计 / [开始今日]
│   │   └── CardView.tsx     # 卡片视图: tab + 卡片 + 评分 (从原 App.tsx 抽出)
│   ├── hooks/
│   │   └── useQueue.ts      # 今日 queue + rate/advance 控制
│   ├── lib/
│   │   ├── types.ts         # Card / Review / Settings / Session / Grade / Mode
│   │   ├── scheduler.ts     # SM-2 纯函数
│   │   ├── db.ts            # idb wrapper, 4 表 schema v1
│   │   ├── seed.ts          # 首次启动 seed MOCK_WORDS (幂等)
│   │   ├── session.ts       # sessions CRUD + 24h 续 session
│   │   ├── queue.ts         # 每日 queue builder (复习优先+新词补齐)
│   │   ├── stats.ts         # 首页统计 (todayDone/streak/totalLearned)
│   │   └── mockWords.ts     # MOCK_WORDS 5 词 (Phase 3 替换)
│   ├── App.css              # Vite 默认 (未用, 留作 cleanup)
│   └── index.css            # CSS tokens + animations
├── public/
│   ├── favicon.svg
│   └── icons.svg
├── screenshots/
│   └── iphone/              # iPhone 14 Pro 视口截图 (Playwright 自动化)
│       ├── _capture.py      # 截图脚本 (Home + 4 模式 + 完成后回 Home)
│       ├── _verify_phase1.py # IDB 验收脚本 (1.7 持久化 + 1.5.4 24h)
│       └── *.png
├── index.html
├── package.json             # name: english-book
├── vite.config.ts
├── tsconfig.app.json        # strict + verbatimModuleSyntax + erasableSyntaxOnly
└── .oxlintrc.json
```

## 开发命令

```bash
npm run dev      # 启动 dev server (localhost:5173, host 0.0.0.0)
npm run build    # tsc -b + vite build → dist/
npm run preview  # 预览生产构建
npm run lint     # oxlint 检查

# 截图验证 (需要 dev server 跑着)
cd screenshots/iphone && python _capture.py

# 验收 (IDB 端到端)
cd screenshots/iphone && python -X utf8 _verify_phase1.py
```

## 当前已完成 (2026-08-03)

### Phase 1: SM-2 + IndexedDB
- 1.1 ✅ SM-2 调度器 (`src/lib/scheduler.ts`, 纯函数 ~50 行)
- 1.2 ✅ IDB schema v1: 4 表 (cards / reviews / settings / sessions)
- 1.3 ✅ 每日 queue builder (复习优先 + 新词补齐, 按 newRatio)
- 1.4 ✅ 首次启动 seed MOCK_WORDS → IDB (幂等)
- 1.5 ✅ App.tsx 重构: 状态机 loading → home / active
- 1.6 ✅ 进度条 "X / 30 今日" 替换原 "1 / 5 队列"
- 1.7 ✅ 验收: 评分 1 张 → 刷新 → IDB 状态保留 (ef/interval/reps/due/firstSeen)

### Phase 1.5: Home 屏 + Session 状态机
- 1.5.1 ✅ Home 屏: 今日 X/Y + 连续 N 天 + 累计 N 词 + [开始今日]
- 1.5.2 ✅ sessions 表 (id=日期, startedAt/endedAt/targetCount/completedCount/reviewsCount/newCount)
- 1.5.3 ✅ session 状态机: 无→active(开始)→completed(queue 完/主动结束)→回 Home
- 1.5.4 ✅ 24h 续 session: 启动时检测, 自动续; 24h 外不续

### Phase 6.1: image 模式视觉 — emoji 路线 (1476 词全覆盖)
- 6.1.1 ✅ 选型: emoji 路线 (浏览器原生 = unicode.org Browser 版本, Noto on Android, Apple on iOS)
  - **不**走 Twemoji (npm 包 404, CDN 不可控, 0 文件自带)
  - **不**走 OpenClipart (跨 1500 词配图 = 50MB+, 不实际)
  - **不**走 Lucide 全覆盖 (215KB → 846KB bundle, 抽象词无图)
- 6.1.2 ✅ emoji mapping 数据: `src/data/wordEmojis.json` + `wordEmojis.ts` (typed Record<string,string|null>)
  - 1476 词 (覆盖 CSV 1444 唯一单字 + 32 batch1 旧版)
  - 611 unique emoji, 10 null (function words / 字母 / 虚词)
  - hot emoji 预算 ❤️=0 ⭐=2 🎉=0 🏆=3 ✨=0 🥇=2 全部 ≤3
- 6.1.3 ✅ iconMap.ts 改: 引入 WORD_EMOJIS 1476 词, 删 13 词 hardcode
- 6.1.4 ✅ TS 编译 0 error, vite build 240KB JS (gzip 79KB)
- 6.1.5 ✅ 截图验证: 25 词测试 (concrete/abstract/null 混合) + 彩色/灰阶 20 张
  - 位置: `screenshots/iphone/emoji-full/{color,gray}-{01-10}.png`
  - 灰阶: `?grayscale=1` URL 参数, 走 `filter: grayscale(100%)` CSS
- 6.1.6 ✅ null emoji 兜底: CardView image 模式走 "[无图标: word]" 占位 (走 CN 文字)

### Phase 3: 真实词表 (CSV → IDB) + 开放节奏
- 3.1 ✅ 解析 CSV (1897 行 → 1441 唯一单字, 排除 MOCK 5 词和短语) → `src/data/vocabSeed.ts`
  - 字段: word + pos (中文) + cn (释义)
  - example 字段空 (CSV 无例句, 后续可补)
- 3.2 ✅ seed.ts 改: 首次启动灌 MOCK 5 + VOCAB 1441, 幂等 (existing.seededAt > 0 跳过)
  - 灌库时按 word 跳过已存在卡 (保留 IDB 学习状态, 避免覆盖)
- 3.3 ✅ 开放节奏: `Settings.dailyNewTarget` 默认 15, 复习卡无上限
  - `queue.ts` 改: ALL due reviews + up to dailyNewTarget new
  - **去掉 30/天总封顶**, 用户想学多少学多少
- 3.4 ✅ CardView queue-done 屏幕: 「再学 10/20 个新词」+「今日到这, 回首页」
  - 不再 auto-onFinish (旧设计导致用户看不到加新词按钮)
  - reload 接受 extraNew 参数, append 到当前 queue
- 3.5 ✅ Home.tsx 改: 「今日新词 X/15」+ 复习 X / 合计 X 副指标 + 超额 badge
- 3.6 ✅ React 19 strict mode 坑修: useQueue 用 `initialLoadedRef` 防止 effect 双调导致 queue 重复追加
  - 症状: 15 张卡变 30 张 (debug log 显示 total=15 但 UI 跑 30)
  - 修法: ref guard + reload 只在 prev=[] 时替换

### Phase 3.1: ConfirmTarget 屏 (今天学几个确认)
- 3.1.1 ✅ `Settings.dailyNewTarget` 既是"上次目标"也是"今天目标", confirm 后写回实现利旧
  - 加 `setDailyNewTarget(n)` 写入 IDB
- 3.1.2 ✅ 新组件 `src/components/ConfirmTarget.tsx`
  - chips: 5 / 15 / 30 / 50 / 100
  - 自定义输入 (1-200)
  - 副标题: 首次用 "首次使用, 推荐 15 个" / 复用 "昨天学了 X 个, 可直接用也可改"
- 3.1.3 ✅ App.tsx 加 'confirm' 屏状态
  - Home → 点击「开始今日」→ Confirm → 开始
  - 已有 active session 时直接续 (不显示 confirm)
  - isFirstTime = totalLearned === 0 决定副标题文案
- 3.1.4 ✅ IDB migration: 老用户 (Phase 1 状态, settings.dailyTarget + 5 张 MOCK 卡) 升级兼容
  - 字段名迁移: dailyTarget → dailyNewTarget (getSettings + ensureSeeded 双层)
  - VOCAB backfill: seededAt > 0 但 cards < 100 → 仍走 seed
  - 触发时机: App.tsx mount 时调 ensureSeeded, 不依赖 useQueue
- 3.1.5 ✅ 截图验证: `screenshots/iphone/phase31/{first,day2}-{01..05}.png`
  - first-02: 首次, 15 chip 高亮
  - first-03: 选 30, 按钮变 "开始学 30 个新词"
  - first-04: 跑完 30 张, 出现 "再学 N" 按钮
  - day2-02: 第二天, "昨天学了 30 个", 30 chip 默认高亮 (利旧)

## 当前未做 (下一阶段, 详见 TODO.md)

- ❌ Phase 3.2: 例句补全 (CSV 无 example, 当前空字符串)
- ❌ Phase 4: PWA manifest + service worker
- ❌ Phase 5: 指标可视化 (热力图/streak 已显示, 7 日热力图待做)
- ❌ Phase 6.2: 模式补完 (listen 预录音频, mix 协调)
- ❌ Phase 7: 跨设备同步 (JSON 备份先行)

## 架构约定 (接手必读)

### 状态管理
- **现在**: 纯 React `useState` 局部 + IndexedDB (idb) 持久化 + 自定义 hooks (`useQueue`)
- **仍然不引入** Redux/Zustand

### 数据流
```
App 挂载 → getActiveSession()
            ├─ 24h 内 active → CardView (useQueue 拉今日 queue)
            └─ 无 → Home (stats: todayDone/streak/totalLearned)

评分点击 → useQueue.rate()
            ├─ applyGrade (scheduler + 写 cards + 写 reviews)
            ├─ bumpSessionStats (session.completedCount++)
            └─ 600ms 后 useQueue.advance() → 下一张

queue 完 → onFinish → endSession → 回 Home → refresh stats
```

### IDB Schema v1
```
cards:       { keyPath: 'id' (word.toLowerCase), indexes: by-due, by-firstSeen }
reviews:     { keyPath: 'id' (autoIncrement),    indexes: by-card, by-session, by-time }
settings:    { keyPath: 'key' (singleton 'main') }
sessions:    { keyPath: 'id' (YYYY-MM-DD),       indexes: by-date, by-endedAt }
```

### 设计系统
- 颜色: 13 个 CSS 变量 (`--color-ink` / `--color-ink-2` / `--color-surface` / `--color-border` / `--color-muted` + accent/danger/success/warning 全家)
  - 注意: AGENTS.md 原本说"只用 5 个", 2026-08-03 加了 8 个 (Apple 浅灰白 + Duolingo 绿黄红). 实际看 `src/index.css`.
- **不要**再加新颜色变量
- 圆角: 卡片 `rounded-3xl`, 按钮 `rounded-2xl`, tab `rounded-full`
- 字号: 大字 `text-6xl` (主词), 中字 `text-5xl` (答案大词), 小字 `text-3xl` (对照小词), 标签 `text-xs`

### 模式与评分的关系
- **模式** 只决定"显示什么" (英→中显示英文, 中→英显示中文)
- **评分** (good/hard/again) 是 SM-2 的输入, 决定"什么时候再出现"
- 两套系统**完全解耦**, 改模式不影响调度, 改算法不影响 UI

### 关键设计决策
- **无显式"保存"按钮**: 每评分 = 1 次 IDB 写 (transaction 自动)
- **退出 = 直接关 tab**: 无需任何操作
- **24h 内未完成 session 可续**: 超过视为放弃
- **首次启动 seed**: `settings.seededAt > 0` 判定, 幂等
- **session 续上时换 id**: 旧 id 行删除, 避免两行 active (id 是日期, 同一天只能一行)

## 验收工作流

### 1) 截图对照 (UI 改完必跑)
```bash
cd screenshots/iphone && python _capture.py
# 输出 6 张: 00-home / 01-en2cn-before / 02-en2cn-after / 03-cn2en-after / 04-listen / 05-home-after
```

### 2) IDB 端到端验收 (Phase 改完必跑)
```bash
cd screenshots/iphone && python -X utf8 _verify_phase1.py
# 9/9 PASS: 1.7 持久化 (5) + 1.5.4 24h 续 (3) + 1.5.4 24h 边界 (1)
# ⚠️ 一定要 -X utf8 (Windows console GBK 编码会炸 emoji)
# ⚠️ 一定要 dev server 跑着 (http://127.0.0.1:5173)
# ⚠️ 脚本里用 `clear()` 清 IDB, 不用 `deleteDatabase` (onblocked 死锁)
# ⚠️ 用 `wait_until="domcontentloaded"`, 不用 `networkidle` (Vite HMR 死等)
```

## 已知坑 (接手必看)

### 编译/构建
- `verbatimModuleSyntax: true` → type-only import 必须用 `import type { X }`
- `erasableSyntaxOnly: true` → 不能用 `enum` / `namespace` / `const enum`
- `noUnusedLocals` / `noUnusedParameters` → 不用的 import / 形参要删
- `tsc -b` 用 build mode, 改 `tsconfig.app.json` 可能要 `rm -rf node_modules/.tmp/tsconfig.app.tsbuildinfo` 重建

### npm 安装
- Node 20.18 (项目要求 20.19+) 触发 optional dep 装不上:
  - `npm i @rolldown/binding-win32-x64-msvc@<ver> --no-save` (Vite 8)
  - `npm i @oxlint/binding-win32-x64-msvc@<ver> --no-save` (oxlint)
  - 根治: 升 Node 到 20.19+ / 22.12+

### IDB
- `deleteDatabase` 在持有连接的 page 里调用 → onblocked 死锁. 改用 `clear()`.
- `getAllFromIndex` 必须 `DBSchema` 里声明 `value: T`, 否则返回 `unknown[]`

### 24h 续 session
- **不要**走"今天日期"快查路径, 因为同 id 的 session 如果 startedAt 超过 24h 会被误判. 直接 24h 兜底.

### React 19 + StrictMode
- `useEffect` 会双调用, 写 effect 要幂等 (e.g. `ensureSeeded` 已有 `seededAt > 0` 检查)

## 截图验证工作流

`screenshots/iphone/_capture.py` 是 Playwright 自动化脚本, 模拟 iPhone 14 Pro 视口截 6 张关键状态图。修改 UI 后必须重跑。

## 协作偏好 (作者: Johnson)

- 节奏快, 长文档不爱看
- "先给意见再动手" —— 重大决策前要简短方案对比, 不要直接动
- 不喜欢重复确认, 小改动直接做
- 跨项目偏好见 `~/.minimax/memory` (Notion 父页面 = `04-投资信息` / id `2cd0559f-56a7-8098-9fb3-f3f6b95b5f2a`)

## 关键文档

- **TODO.md** —— 分阶段路线图 (7 个 Phase)
- **README.md** —— 当前还是 Vite 默认模板, 未改写

