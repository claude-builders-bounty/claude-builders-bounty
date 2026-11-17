# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 格式，并采用 [语义化版本](https://semver.org/lang/zh-CN/) 管理版本。

## [1.0.0] - 2026-11-10

### 新增
- 初始化项目骨架：Electron + React + TypeScript + Vite
- 主进程：无边框透明宠物窗口、置顶、点击穿透、单实例保护、窗口拖拽与 DevTools 切换
- 主进程：IPC 通信层，覆盖宠物状态、聊天、设置、系统监控、定时提醒、窗口控制等通道
- 主进程：系统监控（CPU / 内存 / 上下行网速），每 5 秒采集并通过 IPC 推送
- 主进程：基于 cron 表达式的定时提醒调度器，每分钟检查一次
- 主进程：LLM 客户端，支持 OpenAI / Anthropic / Ollama，流式与非流式对话，回复内容映射为纲手动作与心情
- 主进程：SQLite 数据库（sql.js / better-sqlite3）存储聊天历史与提醒；electron-store 保存用户设置与 LLM 配置
- 渲染进程：Zustand 状态树（宠物/聊天/设置/系统监控/提醒/窗口）
- 渲染进程：React 组件——宠物窗口、聊天面板、设置面板、系统监控
- 渲染进程：Live2D 占位模型组件（PixiJS + pixi-live2d-display），模型缺失自动降级为呼吸圆形
- 渲染进程：纲手 System Prompt 与少样例（毒舌、护短、爱喝酒、怕输钱、医疗忍术专家）
- 安全：contextIsolation、preload 脚本、CSP，密钥不写死代码，全部走环境变量
- 构建：electron-builder 配置，支持 Windows (nsis/zip)、macOS (dmg/zip)、Linux (AppImage/deb)

### 已知问题
- 未内置纲手 Live2D 模型文件（版权原因），需用户自行放入 `public/models/tsunade/`
- 暂无开机自启功能
