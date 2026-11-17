# Python Project Testing & Building Patterns

Collected from window_tool and similar projects using the Hermes+Claude Code workflow.

## 1. Dataclass Config Defaults Consistency

**Rule**: Dataclass field defaults MUST match `from_dict`/`from_json` fallback defaults.

```python
# WRONG — field defaults don't match from_dict fallbacks
@dataclass(frozen=True)
class HotkeyConfig:
    select_window: str = "ctrl+alt+shift+w"  # field default
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'HotkeyConfig':
        return cls(
            select_window=data.get("select_window", "ctrl+shift+w"),  # DIFFERENT!
        )

# CORRECT — both use same default
@dataclass(frozen=True)
class HotkeyConfig:
    select_window: str = "ctrl+shift+w"
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'HotkeyConfig':
        return cls(
            select_window=data.get("select_window", "ctrl+shift+w"),  # SAME
        )
```

**Why**: `default_factory=HotkeyConfig` uses field defaults. If they differ from `from_dict` fallbacks, new instances get wrong values while loaded configs get correct ones — causing test flakiness and runtime surprises.

## 2. Test Isolation with Temp Config Paths

**Rule**: Config classes that load from disk on construction must accept an override path in `__init__`.

```python
@dataclass
class Config:
    _config_path: Optional[Path] = field(default=None, init=True, repr=False)  # init=True!
    
    def __post_init__(self):
        if self._config_path is None:
            self._config_path = self._get_default_config_path()
```

**Test usage**:
```python
@pytest.fixture
def temp_config_path():
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        path = Path(f.name)
    yield path
    if path.exists():
        path.unlink()

def test_something(temp_config_path):
    config = Config(_config_path=temp_config_path)  # isolated, no user config loaded
    ...
```

**Why**: Without `init=True`, tests can't inject temp paths before `__post_init__` loads the real user config, causing cross-test pollution and flaky tests.

## 3. PyInstaller Windows Build Process

**Pre-build**: Kill any running EXE instances
```bash
taskkill /f /im YourApp.exe 2>&1
sleep 2
```

**Build command**:
```bash
python -m PyInstaller your_app.spec --clean
```

**Post-build verification**:
```bash
timeout 5 dist/YourApp.exe --debug 2>&1 || true
# Check for:
# - "Starting tray UI" or equivalent startup log
# - Hotkey registration success (no 1409 errors on clean system)
# - No import errors or missing modules
```

**Common issues**:
- `PermissionError: [WinError 5] Access denied` → EXE still running, kill first
- Chinese log output garbled in console → normal for PyInstaller, GUI works fine
- Missing modules → add to `hiddenimports` in .spec file

## 4. Hotkey Registration 1409 Errors

**Win32 error 1409 = "Hot key already registered"**

**Expected behavior**:
- On clean system: all 4 hotkeys register with unique IDs (e.g., 5,6,7,8)
- After previous runs: some may show 1409 (OS didn't clean up on crash)
- Fix: `taskkill /f /im YourApp.exe` then restart

**Verification**: Log shows `Registered dynamic hotkey: ... id=5/6/7/8` for all 4.

## 5. Kanban Dispatch for Python Tasks

**Test task template**:
```bash
hermes kanban create "[P5] 单元测试全量跑通" \
  --assignee cc-gui-tester --priority 0 \
  --workspace "dir:D:/Ai/Agent/projects/your_project" \
  --body-file "..."
```

**Build task template**:
```bash
hermes kanban create "[P6] EXE 构建 & 运行验证" \
  --assignee cc-gui-tester --priority 0 \
  --workspace "dir:D:/Ai/Agent/projects/your_project" \
  --body-file "..."
```

**Worker prompt must include**:
- Project root path
- Exact commands to run
- Expected output patterns to verify
- Artifact paths to produce

**429 handling**: See `dispatch-safety.md` §8 — serial dispatch, max 20 min wait per card.

## 6. Complex Task Splitting Pattern (Sequential Dependency Chain)

When a task involves multiple sequential phases with different tool/skill requirements (e.g., compile + deploy), **split into dependent subtasks** instead of one monolithic card. Each subtask gets its own assignee matching the phase.

**Pattern**: P10 (llama.cpp compile + deploy) → P10a (env check) → P10b (clone source) → P10c (cmake + build) → P10d (deploy + verify)

**Creation steps**:
```bash
# 1. Create subtasks (each with specific assignee)
hermes kanban create "[P10a] 环境检查 + CUDA 11.8 安装验证" --assignee cc-backend-developer --priority 0 --workspace "dir:D:/Ai/llama.cpp"
hermes kanban create "[P10b] 拉取 llama.cpp 源码 + 切换稳定标签" --assignee cc-backend-developer --priority 0 --workspace "dir:D:/Ai/llama.cpp"
hermes kanban create "[P10c] CMake 配置 + 编译 llama.cpp (GTX1060 sm_61 + MMQ)" --assignee cc-backend-developer --priority 0 --workspace "dir:D:/Ai/llama.cpp"
hermes kanban create "[P10d] 模型部署 + llama-server 启动验证 + SillyTavern 对接" --assignee cc-backend-developer --priority 0 --workspace "dir:D:/Ai/llama.cpp"

# 2. Link dependencies (child waits for parent)
hermes kanban link --parent P10a --child P10b
hermes kanban link --parent P10b --child P10c
hermes kanban link --parent P10c --child P10d
```

**Rules**:
- Each subtask has ONE assignee matching the skill domain (cc-backend-developer for compile, cc-gui-tester for GUI test)
- Dependencies are explicit via `kanban link` — child auto-promotes to `ready` only when parent is `done`
- Dispatch order is enforced by the board; no race conditions
- Rollback is granular: delete only the failed subtask's artifacts, not the whole pipeline
- Failure isolation: P10c failure doesn't redo P10a/P10b

**Pitfall**: Monolithic "compile + deploy" card → worker gets stuck on env setup, no progress visible, 3x reclaimed zombie runs. Splitting exposes exactly which phase fails.

**When to split**:
- Task has ≥3 distinct phases (env → fetch → build → deploy)
- Different phases need different tools/skills
- Failure in one phase shouldn't invalidate work done in prior phases
- Total estimated time > 30 minutes
