# Diagnosing Mouse/Keyboard Hijacking on Windows

When the user reports "something keeps stealing my mouse/focus" or "mouse jumps around on its own", check for these three known culprits **in order**.

## 1. `cua-driver.exe` — Computer Use Agent Driver (Highest Confidence)

**What it is**: The Windows binary for the Computer Use Agent (CUA) automation stack. It installs a global cursor overlay (`Cua.AgentCursorOverlay.default` window class) that intercepts and simulates mouse/keyboard input.

**Why it hijacks**: Designed to control the desktop. When active, it owns the input stack.

**Detection**:
```cmd
rem Check if running
tasklist | findstr /i cua-driver

rem Or via WMIC (works even if tasklist misses it)
wmic process where "name='cua-driver.exe'" get ProcessId,CommandLine
```

**Kill (requires Admin for WMIC path)**:
```cmd
rem Try normal first
taskkill /f /im cua-driver.exe

rem If "Access denied" (running as different integrity level):
wmic process where "name='cua-driver.exe'" delete
```

**Prevent restart**:
- Check Windows Scheduled Tasks for `cua-driver-serve` or similar
- Check `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` and `HKLM` equivalent
- Check Startup folder: `shell:startup`
- If installed via Hermes `computer-use` skill, disable the skill or stop the gateway service

---

## 2. `cc-switch.exe` — Claude Code Proxy (Medium Confidence)

**What it is**: Local proxy that translates Anthropic protocol to third-party APIs (NVIDIA, AgentRouter, etc.). Runs on `127.0.0.1:15721`.

**Why it appears to "launch repeatedly"**: It's a GUI app (`com.ccswitch.desktop-siw` window class) that must stay running for the proxy to work. If it crashes or is killed, any watchdog/cron that monitors it will restart it every few seconds.

**Does it hijack mouse directly?**: **No** — it has no input hooks. But its repeated window creation/foreground calls can steal focus momentarily.

**Detection**:
```cmd
tasklist | findstr /i cc-switch
```

**Kill**:
```cmd
taskkill /f /im cc-switch.exe
```

**Prevent restart**:
- Stop any cron/watchdog that monitors it
- The proxy **must run** for Claude Code to work — don't disable permanently, just ensure only one instance runs

---

## 3. `WindowTool.exe` — Custom Window Manager (Low Confidence, but High Impact)

**What it is**: User's custom PyInstaller/pystray/win32api tool (`D:\Ai\Agent\projects\window_tool\dist\WindowTool.exe`). Registers global hotkeys:
- `Win+Ctrl+Shift+W` — capture window under cursor
- `Win+Ctrl+Shift+H` — hide captured window
- `Win+Ctrl+Shift+U` — show captured window
- `Win+Ctrl+Shift+T` — toggle topmost

**Why it hijacks**: Global hotkeys at `Win+Ctrl+Shift+...` conflict with Windows/system/other app bindings. Accidental press → immediate window capture/focus switch/Z-order change.

**Auto-start vectors (ALL must be disabled)**:
| Vector | Location | How to disable |
|--------|----------|----------------|
| Registry Run key | `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\WindowTool` | `reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v WindowTool /f` |
| Config file | `%APPDATA%\WindowTool\config.json` | Set `"autostart": false` |
| Startup folder | `shell:startup\WindowTool.lnk` | Delete shortcut |
| Scheduled Task | `schtasks /query /fo list /v | findstr -i window` | `schtasks /delete /tn "<taskname>" /f` |

**Kill**:
```cmd
taskkill /f /im WindowTool.exe
```

**Verify fully stopped**:
```cmd
tasklist | findstr -i window
rem Should return no results
```

---

## Diagnostic Checklist (Run in Order)

```cmd
rem 1. Check for CUA driver (most likely culprit)
tasklist | findstr /i cua-driver

rem 2. Check for cc-switch (focus flicker culprit)
tasklist | findstr /i cc-switch

rem 3. Check for WindowTool (hotkey conflict culprit)
tasklist | findstr /i window

rem 4. Check all three via WMIC (catches processes tasklist misses)
wmic process where "name='cua-driver.exe' or name='cc-switch.exe' or name='WindowTool.exe'" get ProcessId,Name,CommandLine
```

**If any found**: Kill via WMIC `delete` (bypasses integrity-level blocks), then disable auto-start vectors.

---

## Real Session Example (2026-10-29)

**User report**: "Something keeps launching cc-switch every few seconds and stealing my mouse"

**Actual findings**:
1. `cua-driver.exe` (PID 11152) running — **true mouse hijacker** (cursor overlay)
2. `cc-switch.exe` (PID 11740) running — relaunching every few seconds via cron watchdog
3. `WindowTool.exe` (PID 12748) running — global hotkeys `Win+Ctrl+Shift+W/H/U/T`

**Resolution**:
1. `wmic process where "name='cua-driver.exe'" delete` — killed CUA driver
2. `taskkill /f /im cc-switch.exe` — killed proxy (user can restart when needed)
3. `taskkill /f /im WindowTool.exe` + `reg delete HKCU\Run /v WindowTool /f` + config.json `autostart=false` — fully disabled WindowTool

**Result**: Mouse focus hijacking stopped immediately.

---

## Key Insight

**`cua-driver.exe` ≠ `cc-switch.exe`**. They are completely different binaries:
- `cua-driver.exe` = Computer Use automation (mouse/keyboard control)
- `cc-switch.exe` = API proxy for Claude Code (no input hooks)

Users conflate them because both may run simultaneously and both have "switch/driver" in the name. Always check for **both** and kill the right one.
