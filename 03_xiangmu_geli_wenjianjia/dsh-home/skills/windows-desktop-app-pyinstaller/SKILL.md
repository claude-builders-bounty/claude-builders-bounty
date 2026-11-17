---
name: windows-desktop-app-pyinstaller
description: Build Windows desktop apps with PyInstaller, pystray, Win32.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [windows, desktop, pyinstaller, pystray, tkinter, win32, packaging]
    category: software-development
---

# Windows Desktop App with PyInstaller

Build, test, and debug Windows desktop applications using Python, PyInstaller onefile, pystray for system tray, tkinter for dialogs, and Win32 APIs (hotkeys, window management, registry). The class of bugs: "code compiles, tests pass, exe builds, but user interaction silently fails" — hotkeys don't register, tray menu doesn't open, window capture doesn't trigger, registry writes crash.

## When to Use

- Building a Windows tray app with PyInstaller onefile
- pystray + tkinter integration (event loop conflict)
- Win32 global hotkeys (RegisterHotKey) or low-level mouse hooks (WH_MOUSE_LL)
- Windows registry reads/writes (autostart, settings)
- Single-instance mutex preventing re-launch
- EXE testing: launch, tray icon, menu, hotkeys, dialogs, registry

## Prerequisites

- Windows host with Python 3.10+
- PyInstaller, pystray, pywin32, Pillow installed
- Git-bash/MSYS terminal (terminal tool runs bash)
- Admin not required for build/test, only for Task Scheduler registration

## Quick Reference

| Goal | Command |
|---|---|
| Kill stale EXE before test | `taskkill /f /im YourApp.exe` |
| PyInstaller clean build | `python -m PyInstaller your_app.spec --clean` |
| Run EXE with debug log | `timeout 5 dist/YourApp.exe --debug` |
| Verify EXE startup | Check log for "Starting tray UI" + hotkey IDs |
| Run unit tests | `python -m pytest tests/ -v` |
| Check registry autostart | `reg query HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v YourApp` |

## Procedure

### 1. Single-Instance Mutex — Kill Before Test
PyInstaller onefile with single-instance mutex blocks second launch with "already running" message. Previous test runs leave processes alive.

```bash
# Always kill before launching test EXE
taskkill /f /im YourApp.exe 2>&1
# Then launch
cd dist && timeout 5 YourApp.exe --debug
```

**Pitfall:** Double-clicking the exe seems to "not open" — it's the mutex blocking. `taskkill` first.

### 2. pystray + tkinter Event Loop Conflict
pystray runs its own message loop (`_icon.run()`), NOT tkinter's. Passing a hidden tkinter root (`tk.Tk().withdraw()`) as `parent` to a modal dialog (`wait_window()`) deadlocks — the dialog waits for tkinter events that never come.

**Fix:** Pass `parent=None` to the dialog constructor. Let it create its own `tk.Tk()` and run `mainloop()`. pystray's callback blocks until dialog closes (modal behavior works).

```python
# In tray callback (runs on pystray thread)
show_settings_dialog(parent=None, config=self.config, on_save=callback)

# In SettingsDialog.show()
if self.parent:
    self.root = tk.Toplevel(self.parent)
    self.root.wait_window()
else:
    self.root = tk.Tk()
    self.root.mainloop()
```

**Pitfall:** `parent=self._root` (hidden tkinter root) → dialog opens then instantly closes/crashes. `parent=None` → dialog works.

**Symptom match:** "点击设置 → 窗口一闪即关/程序闪退" → 99% 是 pystray/tkinter 事件循环冲突，改 `parent=None` 即愈。

### 3. WH_MOUSE_LL Low-Level Mouse Hook Requires Message Loop
`SetWindowsHookEx(WH_MOUSE_LL, ...)` installs the hook in the calling thread. That thread **must** run a Windows message loop (`GetMessage/TranslateMessage/DispatchMessage`) to keep the hook alive. If the thread exits, Windows auto-removes the hook.

**Pattern:** Spawn a daemon thread, install hook, run message loop until capture done.

```python
def capture_window_by_click(self, callback):
    def capture_thread():
        hook_proc = WINFUNCTYPE(...)(self._mouse_hook_proc)
        self._hook_handle = user32.SetWindowsHookExW(WH_MOUSE_LL, hook_proc, 0, 0)
        if self._hook_handle == 0:
            callback(None); return
        
        # Run message loop in THIS thread
        msg = wintypes.MSG()
        while self._hook_handle is not None:
            result = user32.GetMessageW(byref(msg), 0, 0, 0)
            if result <= 0: break
            user32.TranslateMessage(byref(msg))
            user32.DispatchMessageW(byref(msg))
    
    thread = threading.Thread(target=capture_thread, daemon=True)
    thread.start()
    return True  # sync result via Event if needed
```

**Pitfall:** Hook installs, thread returns immediately → hook removed → click never triggers callback.

### 4. Config Singleton Reload After Save
Config is a singleton via `get_config()`. After `config.save()`, the in-memory singleton still holds old values. Must reload.

```python
def on_settings_save(new_config):
    new_config.save()
    from core.config import get_config
    self.config = get_config()  # reload singleton
    # now self.config has new values
    if old_hotkeys != self.config.hotkeys:
        self._re_register_hotkeys()
```

**Pitfall:** `self.config = new_config` only updates local reference; `get_config()` elsewhere returns stale singleton.

### 5. Registry Autostart — Catch All OS Errors
`winreg.DeleteValue` can raise `FileNotFoundError` (key missing), `PermissionError` (no write access), or `OSError` (other). Catch all three.

```python
try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.DeleteValue(key, app_name)
except (FileNotFoundError, PermissionError, OSError):
    pass  # ignore: missing, no permission, or other OS error
```

**Pitfall:** Only catching `FileNotFoundError` → crash on `PermissionError` when user toggles autostart.

### 6. EXE Verification Checklist
After build, run EXE with `--debug` and verify:

- Log shows "Configuration loaded from ..."
- Log shows all hotkeys: "Registered dynamic hotkey: ... id=N" (IDs unique)
- Log shows "Starting tray UI"
- Tray icon visible in system tray
- Right-click → vertical menu opens
- Each menu item works
- Hotkeys trigger expected actions
- Settings dialog opens (no crash), tabs switch, hotkey capture works
- Autostart toggle doesn't crash
- Registry reflects autostart state

## Pitfalls Summary

- **Mutex blocks re-launch:** `taskkill /f /im App.exe` before every test
- **pystray ≠ tkinter loop:** `parent=None` for dialogs, let dialog run own `mainloop()`
- **WH_MOUSE_LL needs message loop:** Run `GetMessage/DispatchMessage` in hook thread
- **Config singleton stale:** `get_config()` after every `save()`
- **Registry errors:** Catch `(FileNotFoundError, PermissionError, OSError)`
- **Test order:** `py_compile` → `pytest` → build EXE → manual EXE verification (cannot skip step 4)
- **Chinese paths in registry:** Use raw strings `r"Software\Microsoft\..."`, not escaped
- **PyInstaller permission error:** Kill running exe before rebuild
- **Stale WH_MOUSE_LL hooks from crashed processes:** If mouse behaves erratically (stuck, auto-restart feel), check for orphaned `YourApp.exe` processes holding low-level mouse hooks. `Stop-Process -Name YourApp -Force` to clear all. Multiple crashed instances each install `WH_MOUSE_LL` (14) and the hook chain conflicts.

## Verification

```bash
# 1. Syntax
python -m py_compile main.py
# 2. Unit tests
python -m pytest tests/ -v
# 3. Build
python -m PyInstaller app.spec --clean
# 4. Run test (kill first)
taskkill /f /im App.exe
cd dist && timeout 5 App.exe --debug
# Check log for: Starting tray UI, 4 hotkeys registered
# 5. Manual: tray icon, menu, hotkeys, settings dialog, autostart toggle
```

## Regression Test Pattern
For projects with GUI + Win32 integration, add a GUI regression test layer:

```bash
# Unit tests (fast, headless)
python -m pytest tests/ -v
# GUI regression tests (requires display, tests actual EXE)
python -m pytest tests_gui/ -v
# Total target: 118+ unit + 12+ GUI = 130+ passed
```

GUI regression tests verify:
- EXE launches, tray icon appears, hotkeys register
- Settings dialog opens without crash (pystray/tkinter loop)
- Hotkey change → save → immediate effect → persists across restart
- Window capture (WH_MOUSE_LL) → crosshair → target selected
- Autostart toggle on/off → registry correct, no crash
- Menu items: hide/show/topmost work on captured window

---

*Distilled from the 2026-10-27 WindowTool session (P0-P9): PyInstaller mutex, pystray/tkinter loop conflict, WH_MOUSE_LL message loop, config singleton reload, registry exception handling, full regression test.*