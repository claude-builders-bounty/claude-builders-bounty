# flet 1.0.4 破坏性变更速查表

> 从 flet 0.x 迁移到 1.0.4 时的全部破坏性变更。一次性全改，别靠重启试错。

## 变更表

| 0.x 写法 | 1.0.4 正确写法 | 症状 | 定位命令 |
|---|---|---|---|
| `ft.app(target=main)` | `ft.run(main)` | `AttributeError: module 'flet' has no attribute 'app'` | `grep -rn "ft\.app(" frontend/` |
| `ft.Color("#RRGGBBAA")` | 直接传 `"#RRGGBBAA"` 字符串 | `AttributeError: module 'flet' has no attribute 'Color'` | `grep -rn "ft\.Color(" frontend/` |
| `ft.Colors("#RRGGBBAA")` | 直接传 `"#RRGGBBAA"` 字符串 | `ft.Colors` 是枚举不吃 hex | `grep -rn "ft\.Colors(" frontend/` |
| `Switch.label_style=...` | `Switch.label_text_style=...` | `TypeError: unexpected keyword argument 'label_style'` | `grep -rn "label_style" frontend/` |
| `Dropdown.on_change=...` | `Dropdown.on_select=...` | `AttributeError: on_change 非法` | `grep -rn "on_change" frontend/` |
| `ft.MaterialStateColor({...})` | 裸 dict `{ft.ControlState.SELECTED:..., ft.ControlState.DEFAULT:...}` | `AttributeError: module 'flet' has no attribute 'MaterialStateColor'` | `grep -rn "MaterialStateColor" frontend/` |
| `ft.border.all(...)` | `ft.Border.all(...)` | `AttributeError: module 'flet.controls.border' has no attribute 'all'` | `grep -rn "ft\.border\.all" frontend/` |
| 控件 `.update()` | try/except RuntimeError 或 `_safe_update()` 统一吞 | `RuntimeError: control not mounted` | `grep -rn "\.update()" frontend/` |
| `FilePicker.get_directory_path()` | `await FilePicker.get_directory_path()` | `RuntimeWarning: coroutine ... was never awaited` | `grep -rn "get_directory_path" frontend/` |
| `page.file_picker = fp` / `page.overlay.append(fp)` | `page.services.append(fp)` | `Unknown control: FilePicker` | `grep -rn "page\.file_picker\|page\.overlay\.append.*FilePicker" frontend/` |

## 验证手段（一次性抓全）

### 1. 静态校验器 `check_flet_kwargs.py`
```python
# AST 解析所有 ft.X(...) 调用，反射真实签名比对
# 一次报出所有不合法关键字，修完输出 "✅ 全部合法"
```

### 2. Mock Page 全量构建 `mock_build_ui.py`
```python
# 用 MagicMock 当 page 跑完整 build_ui(page, cfg, on_start, on_cancel)
# 一次抓全构建期异常，避免反复重启试错
```

## 常见误区

- **别把 `ft.Colors` 当成接受 hex 的函数** —— 它是枚举，成员只有 `PRIMARY`、`SECONDARY` 等预设色
- **`FilePicker` 在 1.x 是 async** —— 必须 `await fp.get_directory_path(...)`，且 `pick_src_dir`/`pick_dst_dir` 改 `async def`
- **`page.services` 不是 `page.overlay`** —— `hasattr(ft.Page, 'file_picker')` 返回 False，正确注册位置是 `page.services.append(fp)`
- **`_safe_update()` 要放在模块级** —— 别写在函数里，否则 lambda 闭包捕获不到
- **`save_config` 等回调必须模块级导入** —— `ui.py` 顶部 `from backend.config import AppConfig, save_config`。函数内局部 import 无法被 lambda 闭包捕获，任何滑块/开关一动就 `NameError: save_config`。

## FilePicker 正确注册模式（实测可用）

```python
async def pick_src_dir(e):
    def on_result(e: ft.FilePickerResultEvent):
        if e.path:
            state["src_dir"] = e.path
            src_field.value = e.path
            cfg.last_src_dir = e.path
            save_config(cfg)          # 模块级导入的 save_config，lambda 能看到
            _safe_update(src_field)
            _check_start_btn()

    fp = ft.FilePicker(on_result=on_result)
    page.services.append(fp)          # ✅ 正确：注册到 page.services
    await fp.get_directory_path(dialog_title="选择源图片文件夹")  # ✅ 必须 await
```

**三个错全中就会报 `Unknown control: FilePicker` + 对话框不弹**：
1. `page.file_picker = fp` —— Page 无此属性（`hasattr(ft.Page, 'file_picker')` = False）
2. `page.overlay.append(fp)` —— overlay 不是服务注册位
3. `fp.get_directory_path(...)` 不加 await —— 协程未被驱动

## 🚨 关键发现：Flet 1.0.4 中 `get_directory_path()` 直接返回路径，不依赖 `on_result` 回调

**本轮实测铁证**：在 Flet 1.0.4 桌面端打包 exe 中，`FilePicker.get_directory_path()` 是 **async 方法直接返回 `Optional[str]`（用户选中的路径或 None）**，**`on_result` 回调不会被触发**。

**错误假设（导致本轮反复修复无效）**：
- 以为必须用 `on_result` 回调拿 `e.path`
- 以为 `page.services.append(fp)` 后回调会自动调用
- 实际：`await fp.get_directory_path()` 直接返回路径，回调根本不进

**正确模式（实测有效）**：
```python
async def pick_src_dir(e):
    fp = ft.FilePicker()  # ✅ 不需要 on_result
    page.services.append(fp)
    path = await fp.get_directory_path(dialog_title="选择源图片文件夹")
    if path:
        state["src_dir"] = path
        src_field.value = path
        cfg.last_src_dir = path
        save_config(cfg)
        _safe_update(src_field)
        _check_start_btn()
```

**验收**：真实 exe 中点击按钮 → FilePicker 弹出 → 选目录 → 返回路径 → 界面显示路径、文件数正确。

**排查口诀**：FilePicker 选完目录没反应、回调不进 → **别信回调，直接 `await fp.get_directory_path()` 拿返回值**.

## 迁移清单

- [ ] `ft.app` → `ft.run`
- [ ] `ft.Color` / `ft.Colors` → 裸 hex 字符串
- [ ] `Switch.label_style` → `label_text_style`
- [ ] `Dropdown.on_change` → `on_select`
- [ ] `ft.MaterialStateColor` → `ft.ControlState` dict
- [ ] `ft.border.all` → `ft.Border.all`
- [ ] 所有 `.update()` 包 `_safe_update()`
- [ ] `FilePicker.get_directory_path()` 加 `await`，回调函数改 `async def`
- [ ] FilePicker 注册到 `page.services.append()`
- [ ] 跑 `check_flet_kwargs.py` 确认 ✅
- [ ] 跑 `mock_build_ui.py` 确认 ✅
- [ ] 真实 `python main.py` 起窗口验证

## 相关工具脚本

- `scripts/check_flet_kwargs.py` —— AST + 反射签名静态校验
- `scripts/mock_build_ui.py` —— Mock Page 全构建验证
- `scripts/wrap_updates.py` —— 批量包裹 `.update()` 为 `_safe_update()`

## 常见前端 Bug 模式（非 flet 特有，但本项目踩过）

### 目录扫描不递归

**位置**：`frontend/app.py`、`frontend/ui.py` 等处理源目录的代码

**错误写法**：
```python
files = [f for f in src_path.iterdir()  # ❌ 只扫顶层
         if f.is_file() and f.suffix.lower() in valid_exts]
```

**正确写法**：
```python
files = [f for f in src_path.rglob("*")  # ✅ 递归扫描子目录
         if f.is_file() and f.suffix.lower() in valid_exts]
```

**症状**：用户选了包含子目录的文件夹，界面显示 "源目录中没有支持的图片文件"，但实际上子目录里有大量图片。

**根因**：`Path.iterdir()` 只返回直接子项，不递归进入子目录。`Path.rglob("*")` 或 `os.walk` 才会递归。

**验收**：单测建 `testdir/subdir/image.jpg`，选 `testdir` 必须找到 1 个文件。

### FilePicker 中文路径编码问题

**位置**：`frontend/ui.py` 的 `pick_src_dir` / `pick_dst_dir` 的 `on_result` 回调

**现象**：用户选中文路径目录（如 `C:\Users\Administrator\Desktop\起诉证据`），FilePicker 返回的 `e.path` 可能是：
- `file:///C:/Users/Administrator/Desktop/%E8%B5%B7%E8%AF%89%E8%AF%81%E6%8D%AE`（URL 编码 + `file://` 前缀）
- `file:///C:/Users/Administrator/Desktop/起诉证据`（仅带前缀）
- `/C:/Users/Administrator/Desktop/起诉证据`（开头斜杠）

直接传给 `Path()` 会导致路径解析失败、扫描不到文件。

**必须在写入 state 前规范化**：
```python
import urllib.parse
raw = e.path
if raw.startswith("file://"):
    raw = raw[7:]  # 去掉 file://
raw = urllib.parse.unquote(raw)  # URL 解码
if raw.startswith("/"):
    raw = raw[1:]  # Windows 下去掉开头斜杠
state["src_dir"] = raw
```

**验收**：手动测试选中文路径目录，文件数显示正确（如 29 个）。

### lambda 闭包捕获不到函数内局部导入

**位置**：`frontend/ui.py` 等有滑块/开关回调的文件

**错误写法**：
```python
# 顶部只导入 AppConfig
from backend.config import AppConfig

# 函数内局部导入 save_config
from backend.config import save_config

# 31 处 lambda 裸调 save_config
on_change=lambda v: setattr(cfg, 'quality', v) or save_config(cfg),
```

**正确写法**：
```python
# 顶部模块级导入
from backend.config import AppConfig, save_config
```

**根因**：Python lambda 闭包只能捕获**模块级**和**外层函数**作用域的变量，**无法看到函数内部的局部 import**。任何滑块/开关一动就 `NameError: save_config`。

**验收**：交互测试必须真动所有滑块、开关，验无 NameError。

### 交付包同步缺失

**现象**：worker 在项目目录修复了代码，但交付包（`img_batch_tool/`）未同步，导致用户跑旧 exe 仍报 bug。

**根因**：打包脚本从项目目录读源码，但协调者手动修复或 worker 修复后，未将变更同步到交付包目录再重新打包。

**修正流程**：
1. 代码修复在项目目录（`project/`）完成并测试通过
2. `cp project/frontend/*.py img_batch_tool/frontend/` 同步到交付包
3. 重新 `flet pack` 打包 exe
4. `cp dist/ImgBatchTool.exe img_batch_tool/dist/` 同步 exe
5. `cp dist/config.json img_batch_tool/dist/` 同步配置
6. 交付包内再次真跑 pytest + exe 启动验证

**验收**：交付包内 `pytest tests/ -q` 全绿 + exe 启动 WINDOW_OK。

### Switch 开关切换不更新内容区可见性

**位置**：`frontend/ui.py` 的 `_switch_card` 函数（约 228-258 行）

**现象**：点击功能开关（如「改尺寸」「转格式」「重命名」「水印」），对应的参数配置区不显示/不隐藏。

**根因**：`_switch_card` 创建 content 容器时用 `visible=initial_state` 初始化，但 `Switch.on_change` 回调中**只改了 state 字典的值，没同步更新 content 容器的 `visible` 属性**，也没调用 `content.update()`。

**错误写法**：
```python
def _switch_card(title, key, content, initial=False):
    state[key] = initial
    content.visible = initial  # 只在创建时赋值
    sw = ft.Switch(
        label=title,
        value=initial,
        on_change=lambda e: state.__setitem__(key, e.control.value)  # ❌ 只改 state，不改 content.visible
    )
    return ft.Column([sw, content])
```

**正确写法**：
```python
def _switch_card(title, key, content, initial=False):
    state[key] = initial
    content.visible = initial
    def on_change(e):
        state[key] = e.control.value
        content.visible = e.control.value  # ✅ 同步更新 content.visible
        content.update()                   # ✅ 必须调用 update() 让 UI 刷新
    sw = ft.Switch(label=title, value=initial, on_change=on_change)
    return ft.Column([sw, content])
```

**验收**：真实 exe 中点击每个开关，对应参数区即时显示/隐藏，无延迟、无残留。

**排查口诀**：开关动了但内容区不动 → **找 on_change 里有没有 `content.visible = ...` 和 `content.update()`**。