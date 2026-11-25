# GUI 测试用 computer_use (CUA) —— Flet 桌面应用专用

> 用 `computer_use` 工具做真实桌面交互测试，替代 pyautogui/pytest-qt 模拟测试。

## 适用场景

- Flet 1.x 桌面应用（`.exe` 打包后）
- FilePicker 原生对话框（Windows 系统对话框，非网页）
- 中文路径选择、特殊字符路径
- 滑块、开关、下拉框、按钮等原生控件交互
- 视觉验证：窗口截图 + 结果文件存在性

## 核心优势 vs pyautogui

| 维度 | pyautogui | computer_use (CUA) |
|---|---|---|
| 定位方式 | 像素坐标（脆弱） | SOM 语义索引 + Vision + AX 树（稳健） |
| FilePicker | 打不中（系统对话框无坐标） | ✅ 能驱动原生对话框 |
| 中文路径 | 需手工输入坐标 | ✅ 能 type 文本、key 确认 |
| 后台运行 | 抢焦点、切前台 | ✅ 背景输入，不抢用户焦点 |
| 验证方式 | 像素对比 | Vision 模型语义理解 |

## 标准工作流

### 1. 启动被测 exe
```python
import subprocess, time
proc = subprocess.Popen(["dist/ImgBatchTool.exe"])
time.sleep(5)  # 等窗口就绪
```

### 2. 捕获 SOM 元素索引
```python
# computer_use(action="capture", mode="som", app="ImgBatchTool")
# 返回：#1 Button '选择源目录' @ (x,y,w,h) [ImgBatchTool]
#        #2 Button '选择输出目录' @ ...
#        #3 Slider '质量' @ ...
#        #4 Switch '递归扫描' @ ...
#        #5 Button '开始处理' @ ...
```

### 3. 真实交互序列

**选源目录（含中文路径）**：
```python
# click element=1, capture_after=True
# → FilePicker 原生对话框弹出
# capture mode=som app="打开文件夹"  # Windows 文件夹选择对话框标题
# type text="C:\\Users\\Administrator\\Desktop\\起诉证据"  # 直接 type 路径
# key keys="return"
# capture_after=True 验证对话框关闭、主窗口路径栏更新
```

**拖动质量滑块**：
```python
# click element=3 (Slider)
# drag from_element=3, to_coordinate=[target_x, target_y]
# 或用 key="arrow_right" 微调
```

**点击开始处理**：
```python
# click element=5, capture_after=True
# 等待处理完成（轮询 capture mode=vision 看进度条/完成提示）
```

### 4. 视觉验证结果
```python
# capture mode=vision question="结果目录下是否有 29 个 .jpg 文件？"
# Vision 模型返回语义判断
```

### 5. 清理
```python
proc.terminate()
```

## Flet 1.x 特有坑点与应对

### FilePicker 是异步协程

- `fp.get_directory_path()` 返回 coroutine，**必须 await**
- 回调函数必须 `async def`
- 在 `computer_use` 测试中：点击按钮后 `capture_after=True` 等对话框真弹出，再驱动对话框

### FilePicker API 版本差异（旧版 vs 新版）

Flet 1.x 打包 exe 时，**运行时注册方式不同**，直接影响 FilePicker 是否弹出：

| 版本 | 注册方式 | 典型代码 | 结果 |
|---|---|---|---|
| **旧版** (0.x 兼容) | `page.overlay.append(page.file_picker)` | `page.file_picker = ft.FilePicker(...); page.overlay.append(page.file_picker)` | ❌ exe 中 FilePicker 不弹出 |
| **新版** (1.x desktop) | `page.services.append(fp)` | `fp = ft.FilePicker(...); page.services.append(fp); await fp.get_directory_path()` | ✅ exe 中正常弹出 |

**排查口诀**：exe 里点按钮 FilePicker 不弹 → 检查是否用 `page.services.append(fp)` + `async def` + `await fp.get_directory_path()`

**测试验证点**：`computer_use` 捕获主窗口 SOM → click 源目录按钮 → `capture_after=True` → 必须看到系统对话框标题为「打开文件夹」/「选择文件夹」

### FilePicker 返回路径格式不一（Windows）

| 格式示例 | 处理 |
|---|---|
| `file:///C:/Users/.../%E8%B5%B7%E8%AF%89%E8%AF%81%E6%8D%AE` | 去 `file://` + `urllib.parse.unquote` + 去首斜杠 |
| `file:///C:/Users/.../起诉证据` | 去 `file://` + 去首斜杠 |
| `/C:/Users/.../起诉证据` | 去首斜杠 |
| `C:\Users\...\起诉证据` | 直接用 |

**测试时必须验证**：归一化后 `Path(normalized).exists()` 且 `rglob` 能找到文件

### 控件未挂载时 `.update()` 抛 RuntimeError

- 生产代码已用 `_safe_update()` 统一吞
- 测试中若触发，`capture_after=True` 能看到报错弹窗，视觉验证会捕获

### exe 启动慢、首次需下载 flet-desktop 客户端

- 首次启动会下载 ~38MB 客户端到 `~/.flet/client/`
- 测试前确保已下载（或在测试脚本里首次启动时等待更久）
- `FLET_CLIENT_URL` 指向镜像（`gh-proxy.com`）加速

## Agent 配置模板：`cc-gui-tester`

```markdown
---
name: cc-gui-tester
description: GUI 自动化测试专用，使用 computer_use (CUA) 做真实桌面交互
tools: ["Read", "Grep", "Glob", "Bash", "Write", "Edit", "Agent", "computer_use"]
model: sonnet
---

# GUI 自动化测试员

## 使命
用 computer_use (CUA) 对 Flet 桌面应用做真实交互测试，**禁止模拟测试替代**。

## 硬规则
1. **必须真跑 exe**、**必须真点 FilePicker**、**必须真输中文路径**、**必须真拖滑块**
2. 失败留证据：capture 截图 + 元素索引 + 异常堆栈 + 视觉验证结果
3. 完成即送审，不自行标记 done
4. 有 Write/Edit 权限，点名路径必须落盘

## 可用工具
- computer_use: capture/click/type/key/drag/scroll/wait/focus_app/list_apps
- 终端: 启动 exe、跑 pytest、查进程
- 文件: 读写测试脚本、对比结果

## 交互优先级
1. SOM 元素索引（首选，最稳）
2. 坐标点击（SOM 失效时回退）
3. 前台模式（后台输入无效时最后手段，需用户批准）

## 验收标准（每张卡必做）
- [ ] exe 启动 5s 内窗口存活、标题正确
- [ ] FilePicker 真弹出、中文路径真选中、确认无报错
- [ ] 所有滑块/开关/按钮真交互、无 NameError
- [ ] 处理完成、结果文件数量正确（视觉验证）
- [ ] 失败时：capture 截图 + 元素索引 + 堆栈全留存
```

## 派单配置

`dispatch_claude.sh` 自动识别：
```bash
case "$AGENT_NAME" in
  cc-gui-tester)
    ALLOWED_TOOLS="$ALLOWED_TOOLS,computer_use"
    ;;
esac
```

`config.env`：
```
WF_AGENT_DIRS="... cc-gui-tester=tests"
```

## 常见失败模式与排查

| 现象 | 可能原因 | 排查步骤 |
|---|---|---|
| capture 返回空 / no on-screen window | exe 未启动、进程名不匹配 | `ps` 确认进程、窗口标题匹配 `app=` 参数 |
| SOM 索引失效 | 两次 capture 间 UI 变了 | 每次 click 前重新 capture |
| FilePicker 不弹出 | click 打错元素、或应用未响应 | capture_after 验证、重试 click |
| type 中文路径后对话框不关 | 未发送 return、或路径格式不对 | 显式 key="return"、归一化路径 |
| 视觉验证说文件数不对 | 处理未完成、或结果目录不对 | 增加等待时间、capture 看进度条 |
| delivery_mode=foreground 报错 | 不支持前台输入 | 回退 SOM/坐标模式 |
| **派单 429、worker 启动即失败** | **cc-switch 走 NVIDIA 上游被限流（40 RPM）** | **改 settings.json ANTHROPIC_BASE_URL 指向 AgentRouter，模型用 deepseek-v4-flash，绕过 cc-switch/NVIDIA** |
| **FilePicker 回调不进、e.path 为空** | **旧版 API `page.overlay` 在 exe 中失效** | **改 `page.services.append(fp)` + `async def` + `await fp.get_directory_path()`** |

## 与测试闸门集成

在 `card_produce_check.py` 的 `_test_gate()` 中新增：
```python
def _gui_test_gate(self, exe_path: Path) -> bool:
    """GUI 启动 + 交互 + 视觉验证全通过才算有产出。"""
    # 1. 启动测试
    # 2. computer_use 交互测试（调用测试脚本）
    # 3. 视觉验证结果目录
    return all_passed
```

**强制要求**：打包卡、UI 改动卡、交付卡必须通过此闸门。

## 证据留存规范

每次测试必须产出：
- `tests/gui/<card_id>/capture_01_som.png` — 初始 SOM 捕获
- `tests/gui/<card_id>/capture_02_filepicker.png` — FilePicker 弹出
- `tests/gui/<card_id>/capture_03_processing.png` — 处理中
- `tests/gui/<card_id>/capture_04_result.png` — 结果验证
- `tests/gui/<card_id>/elements.json` — 元素索引记录
- `tests/gui/<card_id>/test.log` — 完整执行日志

协调者验收时**必须查阅这些证据**，不接受只有文字总结的报告。

## 生产 exe 调试：FilePicker 真实路径捕获

**问题**：模拟测试（直接调函数）无法复现 FilePicker 在打包 exe 中的真实行为。`e.path` 格式随平台/打包方式变化。

**解决**：在生产代码里加**文件落盘日志**，重新打包，用户跑 exe 时自动记录真实值。

```python
# 在 pick_src_dir / pick_dst_dir 的 on_result 回调里插入：
if e.path:
    try:
        with open(r"D:\\path\\to\\debug_path.log", "a", encoding="utf-8") as f:
            f.write(f"[pick_src_dir] raw e.path={repr(e.path)}\n")
    except:
        pass
    normalized_path = _normalize_filepicker_path(e.path)
    try:
        with open(r"D:\\path\\to\\debug_path.log", "a", encoding="utf-8") as f:
            f.write(f"[pick_src_dir] normalized={repr(normalized_path)} exists={Path(normalized_path).exists()}\n")
    except:
        pass
```

**要点**：
- 用绝对路径写日志（打包 exe 后工作目录不确定）
- `try/except pass` 保证不影响主流程
- 记录 `raw` + `normalized` + `Path.exists()` 三个关键信息
- 用户跑完 exe 后读日志即可看到真实格式

**验收**：日志里能看到完整的 `e.path` 原始值，归一化后路径存在且可扫描。