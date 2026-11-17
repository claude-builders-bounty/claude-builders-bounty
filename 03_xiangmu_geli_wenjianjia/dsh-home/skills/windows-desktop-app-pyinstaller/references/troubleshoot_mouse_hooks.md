# Troubleshooting: Residual WH_MOUSE_LL Hook Processes

## Problem
After testing/debugging a pystray app with `WH_MOUSE_LL` (low-level mouse hook), mouse behaves erratically:
- Cursor jumps/stutters
- Clicks don't register
- "Mouse being stolen" sensation
- Multiple app instances still running in background

## Root Cause
`WH_MOUSE_LL` hooks (ID 14) are global. If the hook thread exits without calling `UnhookWindowsHookEx`, Windows removes the hook automatically — **but only when the installing thread dies**. If the process crashes or is killed mid-hook, the hook may persist until the process fully terminates. Multiple test runs leave multiple `YourApp.exe` processes, each holding a hook — they fight over the mouse.

## Detection
```powershell
# Find processes that commonly install WH_MOUSE_LL hooks
$candidates = @(
    "your_app_name", "autohotkey", "powertoys", "strokesplus", "xmouse",
    "obs", "sharex", "snagit", "geforce", "discord", "steam",
    "teamviewer", "anydesk", "mstsc", "vmware", "virtualbox"
)

Get-Process | Where-Object {
    $name = $_.ProcessName.ToLower()
    $candidates | Where-Object { $name -like "*$_*" }
} | Select-Object ProcessName, Id, Path
```

**Expected for your app:** 0 processes. If >0, they're residuals.

## Fix
```powershell
# Kill all residual instances
Stop-Process -Name "YourApp" -Force -ErrorAction SilentlyContinue
Start-Sleep 1
# Verify
Get-Process -Name "YourApp" -ErrorAction SilentlyContinue
# Should return nothing
```

## Prevention (in app code)
```python
import atexit
import win32gui
import win32con

class HotkeyManager:
    def __init__(self):
        self._hooks = []
        atexit.register(self._cleanup_all)
    
    def register_hook(self, hook_id, hwnd):
        self._hooks.append((hook_id, hwnd))
    
    def _cleanup_all(self):
        for hook_id, hwnd in self._hooks:
            try:
                win32gui.UnhookWindowsHookEx(hook_id)
            except:
                pass
        # Also kill self if somehow stuck
        import os
        os._exit(0)
```

**Key:** Register `atexit` cleanup AND call `UnhookWindowsHookEx` explicitly in normal shutdown path. `os._exit(0)` in atexit ensures hard exit if normal cleanup hangs.

## Verification
After cleanup, mouse should feel normal immediately. No reboot needed.

---

*Real case: 2026-10-27 WindowTool session — 5 residual WindowTool.exe processes (PIDs 1812, 14852, 20060, 18084, 17256) each holding WH_MOUSE_LL hook. `Stop-Process -Name WindowTool -Force` cleared all, mouse restored instantly.*