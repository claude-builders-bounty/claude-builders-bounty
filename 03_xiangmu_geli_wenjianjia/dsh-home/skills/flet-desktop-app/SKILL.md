---
name: flet-desktop-app
description: Build, debug, and package Flet desktop apps.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [flet, desktop, gui, python, packaging]
    category: software-development
    related_skills: [safe-file-edits-windows, dogfood]
---

# Flet Desktop App

Flet 1.x 桌面应用（`flet run` / `flet pack`）的 API 事实与由此产生的交互 bug。这些坑的共同特征：**代码不报错、单元测试通过、打包成功、用户点上去一点反应都没有**。

## When to Use / 何时用

- Flet 应用的按钮/开关/单选框点了没反应
- FilePicker / FileDialog 选完文件后界面没变化
- 参数区该显示时不显示、该隐藏时不隐藏
- 打包出来的 exe 行为和 `flet run` 不一致
- 要给 Flet 应用补 UI 回归测试

## FilePicker：拿 `await` 的返回值，不要等回调

Flet 1.0 起 `get_directory_path()` / `get_files()` 是 `async` 方法，**直接把用户选中的路径 return 出来**：

```python
async def pick_src_dir(e):
    fp = ft.FilePicker()
    page.services.append(fp)   # Flet 1.x 用 services 承载
    page.update()              # 挂载后必须刷一次，否则对话框不弹
    path = await fp.get_directory_path(dialog_title="选择源图片文件夹")
    if path:
        path = _normalize_picker_path(path)
        src_field.value = path
        state["src_dir"] = path
        src_field.update()
```

**反模式（静默失效，最常见）：**

```python
fp = ft.FilePicker(on_result=on_result)   # 以为结果走回调
page.services.append(fp)
page.update()
await fp.get_directory_path(...)          # 返回值丢掉 → on_result 不触发 → 什么都没发生
```

自查：`inspect.getsource(ft.FilePicker.get_directory_path)` 看签名。返回 `-> Optional[str]` 就从 `await` 拿，不要靠回调。

**路径必须归一化再交给 `Path()`。** FilePicker 可能返回 `file:///C:/...` 且带 URL 编码（中文目录变成 `%E8%B5%B7...`）。删 `file://` 前缀 → `urllib.parse.unquote` → 去掉 Windows 下多出来的首斜杠，再 `Path()`。

## 单选框：`ft.Radio` 必须包在 `ft.RadioGroup` 里

把 `ft.Radio` 直接放进 `ft.Row`/`ft.Column` 会在运行时报
`radio must be enclosed within radiogroup` —— 编译能过、pytest 能过，一启动就崩。
所有 `Radio` 必须由**一个** `RadioGroup` 包裹，且 `on_change` 挂在 RadioGroup 上：

```python
def _radio_group(label, value, options, on_change):
    radios = [ft.Radio(value=v, label=t) for v, t in options]
    group = ft.RadioGroup(
        content=ft.Row(radios, spacing=20),
        value=value,
        on_change=lambda e: on_change(e.control.value),   # e.control 是 RadioGroup
    )
    return ft.Column([ft.Text(label), group], spacing=8)
```

**回调签名随之改变**：调用方原本传的是接收「值字符串」的 lambda，现在必须用
`e.control.value` 解包，否则拿到的是控件对象。包一层适配函数比逐个改调用方安全。

## 既能选文件夹、又能选单张/多张图片

只给 `get_directory_path()` 时用户没法单独处理几张图。两种选取并存的做法：

```python
async def pick_src_files(e):
    fp = ft.FilePicker()
    page.services.append(fp)
    page.update()
    files = await fp.pick_files(
        dialog_title="选择图片文件",
        allow_multiple=True,
        allowed_extensions=["jpg", "jpeg", "png", "webp"],
    )                    # -> list[FilePickerFile] | None
    if files:
        paths = [_normalize_picker_path(f.path) for f in files if f.path]
        state["src_files"] = paths
        state["src_dir"] = ""          # 两个来源互斥，选文件时清空目录
        src_field.value = f"已选 {len(paths)} 个文件"
        src_field.update()
```

业务侧收集输入文件时**先看显式文件列表，再回落目录递归**：

```python
if state["src_files"]:
    files = [Path(f) for f in state["src_files"] if Path(f).suffix.lower() in EXTS]
else:
    files = [f for f in Path(state["src_dir"]).rglob("*") if f.is_file() and f.suffix.lower() in EXTS]
```

签名自查（`allow_multiple` / `allowed_extensions` 的拼写和返回类型都以实际签名为准）：
`inspect.signature(ft.FilePicker.pick_files)`。

UI 上两个入口并排放在输入框 `suffix`，图标区分：📁 选文件夹、🖼 选图片文件，各带 `tooltip`。

## 开关门控的参数区：`visible` 是快照，不是绑定

```python
# 错——只在构造时算一次
content_container = ft.Container(content=params, visible=value)
```

开关切了之后没有任何东西重新求值 `visible`，所以参数区要么永远不出现、要么永远收不起来。**必须把容器引用交出去，在 `on_change` 里改：**

```python
def _switch_card(title, subtitle, value, on_change, content=None):
    ...
    content_container = None
    if content:
        content_container = ft.Container(content=content, visible=value)
        card_content.controls.append(content_container)
    return _card_container(card_content), content_container   # 把引用返回

card, panel = _switch_card(..., on_change=lambda e: (
    setattr(cfg, 'flag', e.control.value) or save_config(cfg)
    or (panel and setattr(panel, 'visible', e.control.value) or safe_update(panel))
))
```

同一个规则适用于**模式单选**（不缩放/百分比/固定宽高、平铺/单角）：每个条件容器都要在模式回调里显式 `visible = (mode == '...')` 并刷新，不能只在构建时算。

**未挂载的控件 `.update()` 会抛 `RuntimeError`。** 首次构建时控件还没进 page，包一层 try/except 只设属性即可；用户操作时再刷。

## 扫描目录：`rglob` 不是 `iterdir`

`Path.iterdir()` 只扫顶层，子目录里的文件全部漏掉，用户看到的是「目录里明明有图，软件说没有」。递归扫描一律 `p.rglob("*")`，再按 `suffix.lower() in {...}` 过滤。

## 验证：逻辑测试通过 ≠ GUI 能用

最贵的坑。在 Python 里 `Path(dir).rglob()` 数出 29 个文件、pytest 全绿、exe 打包成功 —— **这些都不证明用户点按钮能走通**。中间断的是 UI 事件链：控件没挂上、回调没触发、`visible` 没刷新。

所以验证顺序是：

1. `python -m py_compile` 通过
2. 单元测试通过（只覆盖纯逻辑）
3. **真启动 exe、真点控件、真看界面变化**（截图或人工确认）

第 3 步不能省。用中文路径、带子目录的目录去测 —— 英文路径和顶层文件是最容易「假通过」的输入。

## 打包

```bash
# 先杀掉正在跑的同名进程，否则 exe 被占用、打包出旧文件
powershell -NoProfile -Command "Get-Process | Where-Object { \$_.ProcessName -like '*MyApp*' -or \$_.ProcessName -eq 'flet' } | Stop-Process -Force -ErrorAction SilentlyContinue"

flet pack main.py --name MyApp --distpath dist -y
```

`flet pack` 是 pyinstaller onefile，产物 60MB 量级，耗时 1 分钟左右。打包成功输出最后一行是 `Build complete!`；之后确认 `dist/` 里的 exe 时间戳是新的。

### 交付给别人的机器：单文件 exe + 说明

onefile 产物已经把 Python 解释器和 Flet 运行时全打进去，目标机**不需要装任何东西**。
交付目录这样组：

```
MyApp_v<ver>_Windows/
├── MyApp.exe        # 双击即用
├── config.json      # 首次运行自动生成，可预置默认值
└── 使用说明.txt      # 系统要求 + 功能清单 + 操作步骤
```

打成 zip 分发（`Compress-Archive`）。验证方式：把 exe 从交付目录**原地启动**一次
（`Start-Process -WorkingDirectory <交付目录>`），确认 `MainWindowTitle` 出现 —— 这能
排除「程序依赖源码目录里的文件、单独拷出去就崩」的情况。

不要在 exe 旁边依赖任何外部资源（图标、模板、字体文件）—— onefile 模式下运行时
解包到临时目录，相对路径的「同目录」不是 exe 所在目录。

## Pitfalls

- **别用 `page.overlay` 承载 FilePicker**。Flet 1.x 里 FilePicker 挂 `page.services`；照抄 0.x 的 overlay 写法会得到「对话框不弹 / 回调不触发」。
- **`page.update()` 少一次就白搭**。`services.append` 之后、`await` 之前必须刷；挂载与显示是两步。
- **FilePicker 的 `e.path` 只在回调里有值**。走 `await` 路线时压根不会有 `e`，别写依赖 `e.path` 的代码分支。
- **中文路径是天然的编码陷阱**。未解码的 `%XX` 路径 `Path(...).exists()` 返回 False，而报错信息只会说「目录里没有文件」，很容易误判成扫描逻辑坏了。
- **`read_only=True` 的 TextField 依然要显式 `.update()`**。改 `value` 不会自己刷到界面。
- **改 Flet 源码文件时警惕缩进被改坏**。嵌套回调（`on_change` 里套 lambda）缩进层次深，模糊匹配极易错位，改完立刻 `py_compile`；见 `safe-file-edits-windows`。
