# Live2D 模型资源 — 纲手 (Tsunade)

本目录应放置纲手角色的 Live2D 模型资源（Cubism 4 标准）。

## 所需文件

```
public/models/tsunade/
├── tsunade.model3.json   # 模型设置文件（必需）
├── tsunade.moc3          # 模型网格数据（必需）
├── tsunade_00.png        # 贴图纹理（数量与 model3.json 中定义一致）
├── motions/              # 动作文件目录（推荐，可选）
│   ├── idle.motion3.json
│   ├── talk.motion3.json
│   └── ...
├── expressions/          # 表情文件目录（推荐，可选）
│   ├── normal.expression3.json
│   └── ...
├── pose3.json            # 姿势文件（可选）
└── physics3.json         # 物理文件（可选）
```

## 资源获取说明

Live2D 模型版权归原作者所有，**本仓库不内置纲手模型文件**，需自行获取：

1. **自行制作**：使用 [Live2D Cubism Editor](https://www.live2d.com/) 制作 `.model3.json` / `.moc3` 及贴图。
2. **官方/社区资源**：从 Live2D 官方创作市集或作者授权的创作共享资源中下载，并遵守对应授权协议。
3. **授权合规**：使用前请确认已获得模型版权人的授权，禁止将未经授权的模型用于商业用途。

## 路径解析

- 开发环境：Vite 通过 `/models/tsunade/` 提供静态资源（即本目录）。
- 生产环境：electron-builder 会将 `assets/models/` 拷贝到 `resources/models/`，渲染进程应通过 `file://${process.resourcesPath}/models/tsunade/` 访问（由 `PetLive2D` 的 `modelBaseUrl` prop 注入）。

## 开发时的占位行为

当本目录下不存在 `tsunade.model3.json` 时，`PetModel` 会捕获加载错误并自动降级为一个会呼吸的彩色圆形占位 UI，控制台仅输出警告而不报错，应用可正常启动。
