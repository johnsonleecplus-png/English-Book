# English Book · Android App

上海中考英文词汇 Android App · 极简黑白灰

通过 [Capacitor](https://capacitorjs.com/) 将 React 代码打包进原生 Android WebView — 用户体验等价于原生 App,开发迭代速度与 Web 项目一致.

> **关于 PWA**: 本项目虽然使用 Vite + vite-plugin-pwa 构建, 但 **不启用 PWA 模式**. 生成的 Service Worker (`sw.js`) 和 Web App Manifest 在 Android WebView 中无效 (WebView 本身就是本地容器, 不需要"添加到主屏"或离线缓存机制). 这些产物只是构建副产物, 不会影响 Android 端运行.


## 致谢 / Credits

### 间隔重复算法 SM-2

本应用使用 **SuperMemo SM-2** 间隔重复算法进行调度。SM-2 由 **Piotr Woźniak** 于 1985-1990 年提出。

> 算法本身不收版权费, 但 SuperMemo 官方要求使用者在应用或文档中注明出处。

引用:

> **Woźniak, P. A. (1990).** Optimization of repetition spacing in the practice of learning.
> *Acta Neurobiologiae Experimentalis*, 50, 197–201.

参考链接:
- SuperMemo 官方说明: <https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-supermedo-method>
- SM-2 介绍: <https://www.supermemo.com/en/archives/1990-2014/sm-2>

应用内的"设置 → 致谢"区块也已标注此引用。

### 开源技术栈

| 依赖 | 用途 | License |
|---|---|---|
| React 19 + TypeScript 6 | UI 框架 | MIT |
| Vite 8 | 构建工具 | MIT |
| Tailwind CSS 4 | 样式框架 | MIT |
| Capacitor 8 | Android 打包 | MIT |
| lucide-react | 图标库 | ISC |
| idb | IndexedDB 封装 | ISC |
| emojilib | emoji 映射 | MIT |
| twemoji | emoji 渲染 | MIT |

### 词库

上海中考英语词汇表 (完整版) — 1711 词条 (1441 单词 + 43 缩写 + 227 词组), 音频由 [Piper TTS](https://github.com/rhasspy/piper) (en_US-amy-medium 离线模型) 生成。

## 项目结构

```
D:\19-Android app\
├── android/                    # Capacitor 生成的原生 Android 工程
│   ├── app/
│   │   ├── build/outputs/apk/  # 构建产物
│   │   └── src/main/
│   │       ├── assets/public/  # Web 资源 (HTML/JS/CSS/audio/icons)
│   │       └── java/...        # MainActivity (Capacitor Bridge)
│   └── gradlew                 # Gradle 构建脚本
├── assets/                     # 源图标 (icon-only, icon-foreground, icon-background, splash)
├── dist/                       # Vite 构建产物 (TypeScript + Tailwind → JS/CSS)
├── node_modules/               # npm 依赖
├── public/                     # 静态资源 (audio/words/*.mp3, icons/, loading.png)
├── src/                        # React 源代码 (App.tsx, components/, lib/, hooks/, data/)
├── tools/                      # 原项目的数据生成脚本
├── capacitor.config.ts         # Capacitor 配置 (appId, appName, webDir, plugins)
├── package.json                # npm 脚本 + 依赖
├── vite.config.ts              # Vite + PWA 配置
├── index.html                  # HTML 入口
├── English-Book-debug.apk              # ✅ Debug APK (可直接安装)
└── English-Book-release-unsigned.apk   # ✅ Release APK (需先签名)
```

## 已完成配置

| 项 | 状态 | 说明 |
|---|---|---|
| Capacitor 8.5.0 | ✅ | `@capacitor/cli` `@capacitor/core` `@capacitor/android` |
| Android 平台 | ✅ | minSdk 24 / targetSdk 36 / compileSdk 36 |
| 应用 ID | ✅ | `com.johnson.englishbook` |
| 应用名称 | ✅ | `English Book` |
| 应用图标 | ✅ | 全部 mipmap 尺寸 (mdpi → xxxhdpi, 含 adaptive icon) |
| 启动屏 | ✅ | 全部 portrait + landscape 尺寸 + dark mode |
| Web 资源打包 | ✅ | 1717 个 mp3 (12.34 MB) + 全部 HTML/JS/CSS 资源 |
| Debug APK | ✅ | 29.91 MB |
| Release APK (unsigned) | ✅ | 28.81 MB |

## 技术栈

### Web 层 (保留原 PWA 全部代码)
- React 19.2 + TypeScript 6
- Vite 8 (构建)
- Tailwind CSS 4
- lucide-react (图标)
- IndexedDB via idb (本地存储)
- SM-2 间隔重复算法
- 1711 个中考词汇 + 1717 个 mp3 音频

### Android 层 (Capacitor 包装)
- Capacitor 8.5
- BridgeActivity (WebView ↔ Native 桥接)
- SplashScreen (Android 12+ 兼容启动屏)
- AndroidX Core Splashscreen

## 构建命令

### 前置要求
- **Node.js** ≥ 22 (已测试 22.23.1)
- **JDK 21** (已使用 OpenJDK 21.0.2)
- **Android SDK** (已使用 platforms;android-36, build-tools;36.0.0, platform-tools)

### 环境变量
```powershell
$env:JAVA_HOME = "D:\jdk-21\jdk-21.0.2"
$env:ANDROID_HOME = "D:\android-sdk"
$env:Path = "$env:JAVA_HOME\bin;$env:ANDROID_HOME\cmdline-tools\latest\bin;$env:ANDROID_HOME\platform-tools;$env:Path"
```

### 开发工作流

```powershell
cd "D:\19-Android app"

# 1. 修改 src/ 或 public/ 下的 Web 代码
# 2. 重新构建 Web 产物
npm run build

# 3. 同步到 Android 工程
npx cap sync android

# 4. 编译 APK
cd android
.\gradlew assembleDebug      # Debug APK (含调试信息)
.\gradlew assembleRelease    # Release APK (未签名)

# 产物路径:
# android/app/build/outputs/apk/debug/app-debug.apk
# android/app/build/outputs/apk/release/app-release-unsigned.apk
```

### 一键构建脚本

```powershell
cd "D:\19-Android app"
npm run build; npx cap sync android; cd android; .\gradlew assembleDebug
```

## 安装到设备

```powershell
# USB 连接 Android 设备 + 开启 USB 调试
adb devices

# 安装 Debug APK
adb install -r "D:\19-Android app\English-Book-debug.apk"

# 启动
adb shell am start -n com.johnson.englishbook/.MainActivity
```

## Release APK 签名 (可选)

Debug APK 可直接安装使用。如果要上架 Google Play 或企业内部分发，需要签名:

```powershell
# 1. 生成 keystore (首次)
keytool -genkey -v -keystore english-book.keystore -alias englishbook -keyalg RSA -keysize 2048 -validity 10000

# 2. 配置 signing (在 android/app/build.gradle 中)
#    signingConfigs { release { storeFile file('english-book.keystore') ... } }

# 3. 构建已签名 Release APK
cd android
.\gradlew assembleRelease

# 4. APK 路径
# android/app/build/outputs/apk/release/app-release.apk
```

## Capacitor 配置 (capacitor.config.ts)

```typescript
{
  appId: 'com.johnson.englishbook',     // Android 包名
  appName: 'English Book',              // 显示名称
  webDir: 'dist',                       // Web 构建产物目录
  android: {
    allowMixedContent: false,           // 禁止 HTTP 混合内容
    captureInput: true,                 // 软键盘正确响应
    webContentsDebuggingEnabled: false, // 生产关闭调试
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 1500,
      backgroundColor: '#f5f5f7',       // 苹果浅灰白 (匹配 PWA 主题)
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
      splashFullScreen: true,
    },
    StatusBar: {
      style: 'DARK',                    // 深色状态栏 (图标深色)
      backgroundColor: '#f5f5f7',       // 浅灰白
    },
  },
}
```

## 与原 Web PWA 的差异

| 项 | Web PWA | Android App |
|---|---|---|
| Service Worker | ✅ 注册并缓存 | ✅ 仍然存在 (Capacitor 通过 http://localhost 提供) |
| IndexedDB | ✅ 浏览器内 | ✅ WebView 内 (同样持久化) |
| 音频播放 | ✅ HTML5 Audio | ✅ HTML5 Audio (在 WebView 中正常工作) |
| TTS (Web Speech API) | ✅ 浏览器 API | ⚠️ WebView 部分支持 (需要 `@capacitor-community/text-to-speech` 插件) |
| 安装方式 | 添加到主屏幕 | APK 安装 |
| 离线支持 | Service Worker 缓存 | APK 资源全部本地打包 |

## 已知问题

1. **Service Worker 缓存**: Capacitor 通过 `http://localhost` 提供资源，PWA 的 SW 会注册并尝试缓存。这是无害的，但首次加载会多 ~50ms。
2. **首次启动**: 因为 WebView + IDB 初始化，首次启动约需 1-2 秒。
3. **图标**: 当前使用的是 "EB" 字样的 monogram (从 loading.png 派生的简洁版)。如需替换，把新图标放到 `assets/icon-only.png` (1024x1024) 然后运行 `npx @capacitor/assets generate --android`。

## 升级流程

修改代码后:
```powershell
cd "D:\19-Android app"
npm run build              # 重新构建 Web
npx cap sync android       # 同步到 Android (含 plugins 更新)
cd android
.\gradlew assembleDebug    # 重新打包 APK
```

## 相关资源

- 原 Web PWA 项目: `D:\Johnson-work\05-English-Book`
- [Capacitor 官方文档](https://capacitorjs.com/docs)
- [Android 开发者文档](https://developer.android.com/)
- [Capacitor Assets 工具](https://github.com/ionic-team/capacitor-assets)