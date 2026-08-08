# English Book · Android App (中文)

把 **English Book** (上海中考词汇闪卡 PWA) 包装成原生 Android 应用。

## 核心策略: Capacitor

保留 100% 的 React 代码不变，只是在外面套一个原生 Android WebView。这样:
- ✅ 所有功能 (SM-2 算法 / IndexedDB / 音频 / 动画) 都和 Web 版一模一样
- ✅ 维护成本低 — Web 代码改了，只需 `npm run build && npx cap sync && gradlew assembleDebug`
- ✅ 性能等同于原生应用 (WebView 直接渲染)

## 关键文件

| 文件 | 作用 |
|---|---|
| `capacitor.config.ts` | Capacitor 配置 (appId / appName / 启动屏 / 状态栏) |
| `android/` | 完整的 Android Gradle 工程 (可直接用 Android Studio 打开) |
| `assets/` | 源图标 (可替换 + 重新生成) |
| `English-Book-debug.apk` | 已构建的 Debug APK (可直接 `adb install`) |
| `English-Book-release-unsigned.apk` | Release APK (未签名, 需要 keytool 签名后才能分发) |

## 快速开始

```powershell
# 1. 修改 src/ 或 public/ 下的代码
# 2. 一键重建
cd "D:\19-Android app"
npm run build
npx cap sync android
cd android
.\gradlew assembleDebug

# 3. 安装
adb install -r "D:\19-Android app\English-Book-debug.apk"
```

## 已构建的 APK

- `English-Book-debug.apk` — 29.91 MB (直接安装即可)
- `English-Book-release-unsigned.apk` — 28.81 MB (需先签名)

## 详细文档

完整文档请看 `README.md`。