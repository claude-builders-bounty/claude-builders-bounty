# Windows-Specific Quirks

Hermes runs natively on Windows (PowerShell, cmd, Windows Terminal, git-bash
mintty, VS Code integrated terminal). Most of it just works, but a handful
of differences between Win32 and POSIX have bitten us — document new ones
here as you hit them so the next person (or the next session) doesn't
rediscover them from scratch.

### Input / Keybindings

**Alt+Enter doesn't insert a newline** — Windows Terminal (and mintty) grab it
for fullscreen before prompt_toolkit sees it. Use **Ctrl+Enter** instead (the
CLI binds it to newline on Windows; raw Ctrl+J does the same, harmlessly).
To inspect how your terminal reports a keystroke, run
`python scripts/keystroke_diagnostic.py` from the repo root.

### Config / Files

**HTTP 400 "No models provided" on first run** — `config.yaml` was saved with
a UTF-8 BOM (Notepad does this). Re-save as UTF-8 without BOM;
`hermes config edit` writes correctly.

### `execute_code` / Sandbox

**WinError 10106** from the sandbox child process — it can't create an
`AF_INET` socket. Root cause is usually Hermes's env scrubber dropping
`SYSTEMROOT`/`WINDIR`/`COMSPEC` (Python's `socket` needs `SYSTEMROOT` to find
`mswsock.dll`), not a broken Winsock LSP. The `_WINDOWS_ESSENTIAL_ENV_VARS`
allowlist in `tools/code_execution_tool.py` covers it; if you still hit it,
echo `os.environ` inside an `execute_code` block to confirm `SYSTEMROOT` is set.

### Testing on Windows

`scripts/run_tests.sh` is POSIX-only (expects `.venv/bin/activate`); the
Hermes-installed `venv/Scripts/` has no pip/pytest (stripped for size).
Install pytest into a system Python and run directly (the repo no longer
uses pytest-xdist; the canonical runner does per-file subprocess isolation,
which the POSIX-only wrapper handles):

```bash
"/c/Program Files/Python311/python" -m pip install --user pytest pyyaml
export PYTHONPATH="$(pwd)"
"/c/Program Files/Python311/python" -m pytest tests/foo/test_bar.py -v --tb=short
```

(POSIX-only tests need skip guards — see the cross-platform guard list in
`references/contributor-guide.md`.)

### Path / Filesystem

**Line endings.** Git may warn `LF will be replaced by CRLF`. Cosmetic — the
repo's `.gitattributes` normalizes. Don't let editors auto-convert committed
POSIX-newline files to CRLF.

**Forward slashes work almost everywhere.** `C:/Users/...` is accepted by
every Hermes tool and most Windows APIs. Prefer forward slashes in code
and logs — avoids shell-escaping backslashes in bash.

### Windows-Native Hermes Migration (D: drive, no WSL2)

**Use case**: Move Hermes from WSL2 (`/home/user01/.hermes/`) to Windows
native on D: drive (`D:\Ai\Agent\hermes\`) to free C: drive space and
run without WSL2 dependency.

**Files to relocate** (copy, then update config):
- `scope-recall/` → `D:\Ai\Agent\hermes\scope-recall\` (48 MB SQLite DB)
- `chroma/` → `D:\Ai\Agent\hermes\chroma\` (ChromaDB vector store)
- `memories/` → `D:\Ai\Agent\hermes\memories\`
- `config.yaml` → `D:\Ai\Agent\hermes\config.yaml`
- `SOUL.md` / `USER.md` / `MEMORY.md` → `D:\Ai\Agent\hermes\`

**Config changes for Windows native**:
```yaml
# config.yaml - auxiliary vision via local Ollama (not ModelScope)
auxiliary:
  vision:
    provider: ollama
    base_url: http://127.0.0.1:11434  # localhost, not WSL gateway IP
    model: qwen2.5-vl:7b
  compression:
    provider: nvidia

# terminal working directory
terminal:
  cwd: D:\Ai\Agent\xiangmu
```

**Verified working config.yaml diff** (from this migration):
```yaml
# Before (WSL2)
aauxiliary:
  vision:
    provider: nvidia
    model: moonshotai/kimi-k3
  compression:
    provider: nvidia

# After (Windows native)
aauxiliary:
  vision:
    provider: ollama
    base_url: http://127.0.0.1:11434
    model: qwen2.5-vl:7b
  compression:
    provider: nvidia
```

**SOUL.md / USER.md / MEMORY.md updates**:
- Replace `systemd 用户级 Gateway` → `Windows 任务计划程序`
- Replace `172.24.160.1:11434` (WSL gateway) → `127.0.0.1:11434` (Windows localhost)
- Replace `~/.hermes/chroma/` (WSL) → `D:\Ai\Agent\hermes\chroma\`
- Replace WSL paths in `MEMORY.md` environment baseline with Windows D: paths

**Scheduled tasks (Windows Task Scheduler, run as SYSTEM)**:
```bat
# Xianyu daily pipeline at 02:30
schtasks /create /tn "XianyuPipeline" /tr "D:\Ai\Agent\xiangmu\run_xianyu_pipeline.bat" /sc daily /st 02:30 /ru "SYSTEM" /rl highest /f

# Hermes memory compression at 03:00
schtasks /create /tn "HermesMemoryCompress" /tr "D:\Ai\Agent\hermes\run_memory_compress.bat" /sc daily /st 03:00 /ru "SYSTEM" /rl highest /f
```

**Wrapper scripts** load `.env` then call Python:
```bat
@echo off
set PROJECT_DIR=D:\Ai\Agent\xiangmu\xianyu_pipeline
for /f "usebackq delims=" %%a in (`type "%PROJECT_DIR%\config\.env" ^| findstr /v /r /c:"^#" /c:"^$"`) do set "%%a"
cd /d %PROJECT_DIR%
%VENV_PYTHON% main.py run --pages 3 --limit 10 --listing-mode api >> logs\daily_pipeline.log 2>> logs\daily_pipeline.err.log
```

**Key rule**: Never use `schtasks` or PowerShell `Register-ScheduledTask` from a non-elevated shell — they silently fail with `HRESULT 0x80070005`. Always run the registration script as Administrator (right-click → 以管理员身份运行).

**Working schtasks command format** (tested):
```bat
REM Xianyu daily pipeline at 02:30
schtasks /create /tn "XianyuPipeline" /tr "D:\Ai\Agent\xiangmu\run_xianyu_pipeline.bat" /sc daily /st 02:30 /ru "SYSTEM" /rl highest /f

REM Hermes memory compression at 03:00
schtasks /create /tn "HermesMemoryCompress" /tr "D:\Ai\Agent\hermes\run_memory_compress.bat" /sc daily /st 03:00 /ru "SYSTEM" /rl highest /f
```
- `/ru "SYSTEM" /rl highest` runs as SYSTEM with highest privileges (no password needed)
- `/f` forces overwrite if task exists
- Registration .bat must be **right-click → 以管理员身份运行**

