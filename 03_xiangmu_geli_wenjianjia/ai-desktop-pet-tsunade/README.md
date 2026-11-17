# AI 桌宠·纲手

基于 **Electron + React + TypeScript** 的桌面 AI 桌宠应用，角色形象为《火影忍者》中的**纲手**。支持 Live2D 动画、多模型 LLM 对话、系统资源监控、定时提醒与数据持久化。

> 当前版本：**v1.0.0** · 授权：**MIT** · 支持平台：**Windows / macOS / Linux**

---

## 项目介绍

「AI 桌宠·纲手」是一款常驻桌面的轻量级 AI 陪伴应用。纲手以无边框透明窗口形式驻留在你的屏幕角落，你可以与她对话、查看系统资源占用、设置定时提醒，所有数据本地持久化，隐私可控。

核心能力：
- **Live2D 动画**：加载纲手 Live2D 模型（Cubism 4 标准），支持待机、说话、饮酒、治愈、生气、害羞等多种动作与表情；模型缺失时自动降级为彩色呼吸圆形占位，应用可正常启动。
- **AI 对话（多模型）**：支持 OpenAI、Anthropic（兼容层）、Ollama 三类提供商，流式与非流式对话，可自定义 API Key、Base URL、模型名与温度；回复内容会映射为纲手的人设动作与心情（毒舌、护短、爱喝酒、怕输钱、医疗忍术专家）。
- **系统监控**：实时采集 CPU 使用率、内存占用、上下行网速，通过托盘式常驻窗口展示。
- **定时提醒**：基于 cron 表达式的提醒调度，到时向渲染进程发送提醒事件（可结合纲手人设播报吐槽）。
- **数据持久化**：SQLite（sql.js / better-sqlite3）存储聊天历史与提醒，electron-store 保存用户设置与 LLM 配置，数据全部本地化，不上云。
- **桌面体验**：无边框透明窗口、置顶、点击穿透、拖拽、单实例保护、开发者工具切换。

---

## 功能特性

| 模块 | 特性 | 说明 |
| --- | --- | --- |
| 宠物展示 | Live2D 模型（纲手） | PixiJS + pixi-live2d-display 渲染，透明背景，响应式缩放 |
| 宠物交互 | 动作 / 表情 / 好感度 | 待机、说话、饮酒、治愈、生气、害羞；好感度随对话累积 |
| AI 对话 | 多模型接入 | OpenAI / Anthropic / Ollama，流式与非流式，人设动作映射 |
| 系统监控 | CPU / 内存 / 网速 | 每 5 秒采集一次，IPC 推送到渲染进程 |
| 定时提醒 | cron 表达式调度 | 每分钟检查一次，触发提醒事件 |
| 数据持久化 | SQLite + electron-store | 聊天历史、提醒、用户设置、LLM 配置全部本地保存 |
| 窗口管理 | 无边框 / 透明 / 置顶 / 点击穿透 | 单实例，支持拖拽与 DevTools 切换 |
| 安全 | contextIsolation / preload / CSP | 密钥不写死代码，全部通过环境变量注入 |

---

## 技术栈

| 层 | 技术 | 版本 | 用途 |
| --- | --- | --- | --- |
| 桌面框架 | Electron | ^31.0.0 | 跨平台桌面应用壳 |
| 前端框架 | React | ^18.3.1 | 渲染进程 UI |
| 语言 | TypeScript | ^5.6.3 | 全栈类型安全 |
| 构建工具 | Vite | ^5.4.10 | 开发服务器与生产打包 |
| 状态管理 | Zustand | ^4.5.4 | 宠物/聊天/设置/监控/提醒状态树 |
| 样式 | Tailwind CSS | ^3.4.14 | 原子化样式 |
| Live2D | pixi.js / pixi-live2d-display | ^6.5.10 / ^0.4.0 | Live2D 模型渲染 |
| LLM 客户端 | openai | ^4.67.0 | OpenAI 兼容接口（含 Ollama） |
| 数据库 | sql.js / better-sqlite3 | ^1.9.0 / ^11.0.0 | 本地聊天与提醒持久化 |
| 配置存储 | electron-store | ^8.2.0 | 用户设置与 LLM 配置 |
| 打包 | electron-builder | ^25.1.0 | NSIS / DMG / AppImage / deb 产物 |

---

## 快速开始

### 1. 克隆仓库

```bash
git clone <仓库地址>
cd ai-desktop-pet-tsunade
```

### 2. 安装依赖

```bash
npm install
```

> 注意：`better-sqlite3` 是原生模块，安装需要 Python 与 C++ 构建工具。Windows 用户请确保已安装 [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)（勾选“适用于 C++ 的桌面开发”工作负载）。

### 3. 配置环境变量

复制环境变量模板：

```bash
copy .env.example .env   # Windows (PowerShell)
# 或者
cp .env.example .env     # macOS / Linux
```

编辑 `.env`，填写你的 LLM Provider 与 API Key（详见下文“配置说明”）。

### 4. 准备 Live2D 模型（可选）

本仓库**不内置**纲手 Live2D 模型文件（版权原因）。开发时模型缺失会自动降级为呼吸圆形占位，应用可正常启动。

如需加载真实模型，请将模型资源放入 `public/models/tsunade/`（开发环境）或构建后的 `resources/models/`（生产环境），具体文件清单与获取方式见：

[模型资源说明 → public/models/tsunade/README.md](public/models/tsunade/README.md)

### 5. 以开发模式运行

```bash
npm run electron:dev
```

- Vite 启动开发服务器（http://localhost:5173）
- Electron 加载开发地址，自动打开开发者工具

或分开运行：

```bash
npm run dev          # 仅启动 Vite
npm run electron     # 仅启动 Electron（需先构建或指定 ELECTRON_START_URL）
```

---

## 模型获取指南

纲手 Live2D 模型的文件清单、版权说明与获取渠道，请参阅：

📄 **[public/models/tsunade/README.md](public/models/tsunade/README.md)**

简要：需要 `tsunade.model3.json`、`tsunade.moc3`、贴图 `.png`，可选 `motions/`、`expressions/`、`pose3.json`、`physics3.json`。可自行使用 Live2D Cubism Editor 制作，或从官方/社区授权资源下载，使用前请确认已获得版权人授权。

---

## 配置说明

所有配置通过 `.env` 环境变量或运行时设置面板修改，密钥**绝不写死在代码中**。

### LLM Provider 与 API Key

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| `LLM_PROVIDER` | LLM 提供商：`openai` \| `anthropic` \| `ollama` | `openai` |
| `OPENAI_BASE_URL` | OpenAI 兼容接口基地址（亦可指向 Ollama / vLLM / LM Studio） | `https://api.openai.com/v1` |
| `OPENAI_API_KEY` | API 密钥 | `sk-...` |
| `OPENAI_MODEL` | 模型名称 | `gpt-4o-mini` |
| `ANTHROPIC_API_KEY` | Anthropic 密钥（通过兼容层或官方 SDK） | `sk-ant-...` |
| `ANTHROPIC_MODEL` | Anthropic 模型 | `claude-3-5-haiku-20241022` |
| `OLLAMA_BASE_URL` | Ollama 本地服务地址 | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama 模型 | `llama3.1:8b` |

### 应用配置

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| `APP_PORT` | Vite 开发服务器端口 | `5173` |
| `LOG_LEVEL` | 日志等级 | `info` |
| `ENABLE_CLICK_THROUGH` | 是否启用点击穿透 | `false` |

### 运行时设置

通过应用内“设置”面板可修改并持久化：
- LLM：提供商、API Key、Base URL、模型名、温度、最大 token
- 显示：是否显示系统监控面板
- 窗口：点击穿透、置顶
- 提醒：cron 表达式列表（启用/禁用）

---

## 打包分发

```bash
npm run build
```

构建流程：`tsc` 类型检查 → `vite build` 渲染进程静态资源 → `electron-builder` 打包桌面应用。

### 产物位置

| 产物 | 位置 | 说明 |
| --- | --- | --- |
| 主进程代码 | `dist/electron/` | Electron 主进程与 preload 编译输出 |
| 渲染进程代码 | `dist/renderer/` | React 应用静态资源 |
| 安装包 | `release/` | 各平台分发包 |

### 安装包类型（electron-builder.json）

| 平台 | 目标 | 文件 |
| --- | --- | --- |
| Windows | `nsis`、`zip` | `AI 桌宠·纲手 Setup x.x.x.exe` / `.zip` |
| macOS | `dmg`、`zip` | `.dmg` / `.zip` |
| Linux | `AppImage`、`deb` | `.AppImage` / `.deb` |

> Windows 默认 `oneClick: false`，允许用户选择安装目录，并自动创建桌面与开始菜单快捷方式。

---

## 常见问题

### Q1. 模型不显示 / 宠物是个彩色圆

`public/models/tsunade/` 下缺少 `tsunade.model3.json` 时，`PetModel` 会捕获加载错误并自动降级为呼吸圆形占位 UI，控制台输出警告而不报错。如需显示真实模型，请放入对应资源文件（见“模型获取指南”）。

### Q2. API 调用报错

- 检查 `.env` 中 `LLM_PROVIDER`、`OPENAI_API_KEY`、`OPENAI_BASE_URL` 是否填写正确。
- OpenAI 兼容提供商（Ollama / vLLM / LM Studio）可设 `OPENAI_API_KEY=dummy`。
- 本地 Ollama 请确保服务已启动且模型已拉取：`ollama pull llama3.1:8b`。
- 网络不通可更换代理或镜像 Base URL。

### Q3. 应用白屏

- 开发模式：确认 Vite dev server 已启动（`npm run dev`），且 `ELECTRON_START_URL=http://localhost:5173` 已设。
- 生产模式：确认已运行 `npm run build` 生成 `dist/renderer/index.html`。
- 按 `F12` 打开开发者工具查看控制台错误。

### Q4. 自动启动不生效

本版本未内置开机自启。如需自启，请将快捷方式放入系统启动文件夹（Windows: `shell:startup`），或在设置中由用户自行配置。

### Q5. `better-sqlite3` 安装失败

该原生模块需编译。Windows 用户请安装 Visual Studio Build Tools（C++ 桌面开发工作负载）及 Python，并配置好 `npm` 构建环境后重新 `npm install`。

---

## 贡献指南

欢迎提交 Issue 与 Pull Request！贡献前请：

1. Fork 仓库并创建特性分支 (`git checkout -b feat/xxx`)。
2. 遵循项目编码规范（函数 < 50 行、文件 < 800 行、嵌套 ≤ 4 层、不可变性）。
3. 提交前运行 `npm run typecheck` 确保零类型错误，运行 `npm run lint` 检查代码风格。
4. 提交信息遵循常规提交格式，例如 `feat: 新增系统监控面板`。
5. 如修改了源码，请同步更新 `version.md` 版本记录。

---

## License

本项目采用 [MIT License](LICENSE) 授权。

---

## 致谢

- [Electron](https://www.electronjs.org/) — 跨平台桌面应用框架
- [React](https://react.dev/) / [Vite](https://vitejs.dev/) — 前端框架与构建工具
- [PixiJS](https://pixijs.com/) / [pixi-live2d-display](https://github.com/takahirox/pixi-live2d-display) — Live2D 渲染
- [Zustand](https://zustand-demo.pmnd.rs/) — 轻量状态管理
- [Tailwind CSS](https://tailwindcss.com/) — 原子化 CSS
- [better-sqlite3](https://github.com/JoshuaWise/better-sqlite3) / [sql.js](https://github.com/sql-js/sql.js/) — 本地数据库
- [electron-store](https://github.com/sindresorhus/electron-store) — 应用配置持久化
- [OpenAI](https://openai.com/) / [Ollama](https://ollama.com/) — LLM 接口兼容

> 角色“纲手”源自《火影忍者》（作者：岸本齐史），仅用于学习交流与个人非商业用途，请尊重原作者版权。Live2D 模型资源需另行取得版权人授权。