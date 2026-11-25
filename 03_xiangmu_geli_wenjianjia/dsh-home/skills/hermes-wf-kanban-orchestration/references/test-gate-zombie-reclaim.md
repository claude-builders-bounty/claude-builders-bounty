# 看板卡片产出校验：测试闸门与僵尸回收

> 文件有变化 ≠ 可用。必须真跑测试、真起窗口、真跑 exe 才算有产出。

## 测试闸门 `_test_gate()`

**位置**：`scripts/hermes-wf/card_produce_check.py`

### 逻辑

```python
def _test_gate(self, repo_root: Path) -> bool:
    """带 tests/ 的项目，必须真跑 pytest 全绿才算有产出。"""
    tests_dir = repo_root / "tests"
    if not tests_dir.exists():
        return True  # 无 tests/ 不强制
    
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-q", "--tb=no"],
        cwd=repo_root, capture_output=True, text=True, timeout=120
    )
    return result.returncode == 0
```

### 关键点

- **向上回溯找仓库根**：从 `WF_AGENT_DIRS` 子目录（如 `backend/`、`frontend/`）向上找 `tests/` 或 `.git` 祖先
- **可关闭**：`WF_TEST_GATE=0` 仅限明确知道测试环境不可用时
- **超时**：120 秒，防止死锁
- **输出**：pytest 返回码为 0 才放行

### 实测效果

| 卡 | 之前 | 加闸门后 |
|---|---|---|
| 单元测试卡 | 文件变化 → produced ✅ | pytest 16 failed → blocked ❌ → 修 3 真 bug → 79 passed ✅ |
| 打包卡 | 文件变化 → produced ✅ | 需先跑测试全绿才放行 |
| E2E 卡 | 绕过 UI 直调引擎 → produced | 真跑全链路 85 passed |

## 僵尸卡回收 `reclaim_stale()`

**位置**：`scripts/hermes-wf/kanban_auto_dispatch.py`

### 逻辑

```python
def reclaim_stale(self) -> list[str]:
    """扫描 running 卡，pid 死或日志超 WF_STALE_RUNNING_SECONDS 无更新 → 打回 ready。"""
    reclaimed = []
    for task in self.db.running_tasks():
        pid = task.metadata.get("worker_pid")
        log_path = task.metadata.get("worker_log")
        
        if pid and not is_pid_alive(pid):
            self._unblock_to_ready(task.id, f"worker pid {pid} 已死")
            reclaimed.append(task.id)
        elif log_path and (time.time() - Path(log_path).stat().st_mtime) > WF_STALE_RUNNING_SECONDS:
            self._unblock_to_ready(task.id, f"worker 日志 {WF_STALE_RUNNING_SECONDS}s 无更新")
            reclaimed.append(task.id)
    return reclaimed
```

### 配置

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `WF_STALE_RUNNING_SECONDS` | 1800 (30min) | 超时即判定僵死 |
| `WF_TEST_GATE` | 1 | 1=强制测试全绿，0=关闭 |

### 双向实测

- **死 pid**：kill worker 进程 → 下一轮 tick 自动回收 ready ✅
- **活 pid**：正常跑的 worker → 不误杀 ✅
- **日志超时**：worker 卡死不输出 → 30 分钟后回收 ✅

## GUI 启动测试（必须纳入闸门）

```python
def _gui_smoke_test(exe_path: Path) -> bool:
    """启动 exe，等 5s，查进程存活、查窗口标题正确。"""
    proc = subprocess.Popen([str(exe_path)])
    time.sleep(5)
    try:
        # 查进程存活
        assert proc.poll() is None
        # 查窗口标题（需 pygetwindow 或类似）
        import pygetwindow as gw
        wins = gw.getWindowsWithTitle("ImgBatchTool")
        assert len(wins) > 0
        return True
    finally:
        proc.terminate()
```

**验收标准**：进程存活 + 窗口标题包含预期字符串（如 "ImgBatchTool - 离线图片批量处理工具")。

> ⚠️ **本模板已存在但本轮未被真跑**。协调者只看文档里有模板，未实际执行。
> **强制要求**：每次打包后、每次 UI 改动后、交付前，必须真跑一次此测试并附 `ps` 进程输出截图。

## 交互测试（必须纳入闸门）

```python
def _gui_interaction_test(exe_path: Path) -> bool:
    """真点按钮、改滑块、选目录、验不报错。"""
    proc = subprocess.Popen([str(exe_path)])
    time.sleep(5)
    try:
        import pygetwindow as gw
        import pyautogui
        wins = gw.getWindowsWithTitle("ImgBatchTool")
        if not wins:
            return False
        win = wins[0]
        win.activate()
        time.sleep(1)
        
        # 1. 点 FilePicker 选源目录按钮
        pyautogui.click(win.left + 600, win.top + 150)
        time.sleep(2)
        # 2. 拖动质量滑块
        pyautogui.moveTo(win.left + 400, win.top + 300, duration=0.5)
        pyautogui.dragRel(100, 0, duration=1, button='left')
        time.sleep(1)
        # 3. 点击开关
        pyautogui.click(win.left + 200, win.top + 200)
        time.sleep(1)
        
        # 无异常抛出 = 通过
        return True
    except Exception as e:
        print(f"交互测试失败: {e}")
        return False
    finally:
        proc.terminate()
```

**覆盖点**：FilePicker 选源/输出、所有滑块 on_change、所有开关、开始/取消按钮。

> ⚠️ **本模板已存在但本轮未被真跑**。导致 `save_config` NameError、FilePicker 不弹等阻断级 bug 全漏。
> **强制要求**：每次 UI 改动后、交付前，必须真跑一次此测试并附交互日志（含点击坐标、异常堆栈）。

## Worker 方向性错误（方案本身是废的）

| 表现 | 根因 | 对策 |
|---|---|---|
| 文件存在、测试能过、日志显示完成 | 裸 PyInstaller + `--collect-all flet` 收不到 38MB flet-desktop 客户端 | 必须用 `flet pack` 官方入口 |
| requirements.txt 钉 `flet==0.21.2` | 降级炸弹：与 1.x API 不兼容，UI 直接崩 | 锁定实测版本 + 不可降级注释 |
| frozen 态 `CONFIG_PATH` 用 `__file__` | 打包后写入 `_MEIPASS` 临时目录，重启即丢 | `_runtime_root()` 锚定 `sys.executable.parent` |
| 代码审查只盯 engine.py | 31 处 lambda NameError、FilePicker 注册错、async/await omissions 全漏 | 审查卡 body 强制逐文件过 `frontend/` |
| 目录扫描不递归 | `Path.iterdir()` 只扫顶层，子目录图片全漏 | 必须用 `Path.rglob("*")` 或 `os.walk` 递归 |

**判据**：协调层必须独立验证真实路径（启动 exe、跑测试、查进程），不采信任何 worker 自述。