---
name: wsl2-windows-interop-automation
description: "Run Windows GUI automation from WSL2 via interop bridge."
category: devops
tags: [wsl2, windows, interop, gui-automation, cua-driver, computer-use, mcp]
version: 1.0.0
---

# WSL2 → Windows GUI Automation via Interop

Run Windows-native GUI automation binaries (cua-driver, etc.) from WSL2 by executing the Windows `.exe` directly through WSL interop. The binary runs in the Windows user session (Session 1) with full desktop access, communicating via stdio MCP.

## When to Use

- You're running Hermes in WSL2 but need to drive Windows GUI apps (Chrome, Feishu, Explorer, games, etc.)
- The automation tool has a Windows binary that speaks stdio MCP (e.g., cua-driver)
- You want zero network config (no TCP ports, no firewall rules, no HTTP)

## Prerequisites

| Component | Location | Notes |
|-----------|----------|-------|
| Windows binary | Windows host (e.g., `C:\...\cua-driver.exe`) | Installed via scoop/chocolatey/official installer |
| WSL2 interop | Enabled by default | `wsl.conf` must not disable `interop` |
| Windows user session | Active (Session 1) | User must be logged in; binary runs in their desktop session |

## Setup

### 1. Install the Windows binary (on Windows host)

```powershell
# Example: cua-driver via scoop
scoop install cua-driver

# Or download from GitHub releases
# https://github.com/trycua/cua-driver/releases
```

### 2. Run as persistent daemon (Windows side)

```powershell
# Register as startup task (runs in Session 1 with desktop access)
$action = New-ScheduledTaskAction -Execute "cua-driver.exe" -Argument "serve"
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
$principal = New-ScheduledTaskPrincipal -UserId "Administrator" -LogonType Interactive -RunLevel Highest
Register-ScheduledTask -TaskName "cua-driver-serve" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
schtasks /Run /TN "cua-driver-serve"
```

> **Critical**: The task must run as `Interactive` logon type in the user's session (not SYSTEM/Session 0), otherwise UI Automation fails.

### 3. Configure Hermes (WSL2 side)

```bash
# Point Hermes at the Windows binary via interop
export HERMES_CUA_DRIVER_CMD="/mnt/c/Users/<USER>/AppData/Local/Programs/Cua/cua-driver/bin/cua-driver.exe"

# Persist for login shells
echo 'export HERMES_CUA_DRIVER_CMD="/mnt/c/Users/<USER>/AppData/Local/Programs/Cua/cua-driver/bin/cua-driver.exe"' >> ~/.profile

# Persist for systemd service (Hermes Gateway)
mkdir -p ~/.config/systemd/user/hermes-gateway.service.d
cat > ~/.config/systemd/user/hermes-gateway.service.d/cua-driver.conf <<'EOF'
[Service]
Environment=HERMES_CUA_DRIVER_CMD=/mnt/c/Users/<USER>/AppData/Local/Programs/Cua/cua-driver/bin/cua-driver.exe
EOF
systemctl --user daemon-reload
systemctl --user restart hermes-gateway
```

### 4. Verify

```bash
hermes computer-use status
# Should show: cua-driver: installed at /mnt/c/.../cua-driver.exe [custom binary from HERMES_CUA_DRIVER_CMD] (cua-driver 0.28.2)  ready: true
```

## Critical: Hermes Source Patches Required

The upstream `cua_backend.py` has two hardcoded timeouts that **fail on WSL2 interop** because launching a Windows binary from WSL adds ~60-100s cold-start latency.

### Patch 1: Manifest check timeout (`cua_driver_runtime_contract_status`)

```python
# tools/computer_use/cua_backend.py ~line 1056
# Detect WSL2 and use 120s timeout
is_wsl2 = False
if sys.platform == "linux":
    try:
        with open("/proc/version", encoding="utf-8") as f:
            if "microsoft" in f.read().lower():
                is_wsl2 = True
    except Exception:
        pass
manifest_timeout = 15.0 if sys.platform == "win32" else (120.0 if is_wsl2 else 5.0)

result = subprocess.run(
    [resolved, "manifest"],
    timeout=manifest_timeout,  # was: 15.0 if win32 else 5.0
    ...
)
```

### Patch 2: MCP session startup timeout (`_CuaDriverSession._start_lifecycle_locked`)

```python
# tools/computer_use/cua_backend.py ~line 1764
# Detect WSL2 and use 120s timeout
is_wsl2 = False
if sys.platform == "linux":
    try:
        with open("/proc/version", encoding="utf-8") as f:
            if "microsoft" in f.read().lower():
                is_wsl2 = True
    except Exception:
        pass

if not self._ready_event.wait(timeout=30.0 if not is_wsl2 else 120.0):
    # was: timeout=30.0
    ...
```

> **Why 120s?** First `cua-driver.exe manifest` via interop takes ~60-90s (Defender scan, process spawn). Subsequent calls are fast (~1s). The session startup includes manifest check + MCP initialize + capability discovery.

## Verified Working Flow

| Step | Command | Expected |
|------|---------|----------|
| 1. Capture with SOM | `hermes chat -t computer_use -q "用 computer_use capture mode=som app=\"Chrome\""` | Returns screenshot + 400+ element indices |
| 2. List windows | `hermes chat -t computer_use -q "用 computer_use list_windows"` | Returns visible Windows windows with PID/title |
| 3. Click element | `hermes chat -t computer_use -q "用 computer_use click element=8"` | Clicks element #8 in last capture |
| 4. Click coordinate | `hermes chat -t computer_use -q "用 computer_use click coordinate=[100, 130]"` | Clicks at absolute coordinates |

## Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `manifest check failed: timed out after 5.0 seconds` | WSL2 interop cold start >5s | Apply Patch 1 (120s timeout) |
| `cua-driver session never reached ready (timeout 30s; stuck in phase: mcp-initialize)` | Session startup >30s | Apply Patch 2 (120s timeout) |
| `cua-driver: not installed` | `HERMES_CUA_DRIVER_CMD` not set in Gateway env | Add to `hermes-gateway.service.d/cua-driver.conf` + restart |
| `list_windows` returns empty / no visible windows | Daemon running in Session 0 (no desktop) | Task must run as `Interactive` logon type |
| Feishu/Chrome not in `list_windows` | App minimized or no visible window | `focus_app app="Feishu"` first, or restore window |
| **Mouse/keyboard hijacked on Windows host** | `cua-driver.exe` running natively on Windows (not via interop) with global cursor overlay `Cua.AgentCursorOverlay.default` | Kill via `wmic process where "name='cua-driver.exe'" delete`; disable Scheduled Task / startup entry that launches it |
| **User confuses `cua-driver.exe` with `cc-switch.exe`** | Both have switch/driver in name, both may run simultaneously | `cc-switch.exe` = API proxy (no input hooks); `cua-driver.exe` = desktop automation (owns input stack). See `windows-system-maintenance/references/diagnose-process-hijacking.md` |

## Security Notes

- **No network exposure**: Binary runs locally via interop, no TCP ports opened
- **No credential leakage**: Windows binary inherits user's session credentials; Hermes only passes stdio
- **Firewall**: No inbound rules needed (unlike TCP bridge approach)

## Related Skills

- `computer-use` (bundled) — the Hermes tool being bridged
- `watchdog-cron-patterns` — for silent-success monitoring
- `debug-wsl-windows-network` — if interop itself fails
- `wsl-readonly-mount-enforcement` — unrelated but same WSL context

## References

- `references/cua_backend_patches.md` — exact patch diffs for both timeouts
- `references/windows_task_setup.ps1` — ready-to-run Scheduled Task registration script
- `references/hermes_cua_env.sh` — environment variable setup for shell + systemd

---

*Distilled from WSL2 Hermes + cua-driver 0.28.2 interop verification (2026-09-24).*