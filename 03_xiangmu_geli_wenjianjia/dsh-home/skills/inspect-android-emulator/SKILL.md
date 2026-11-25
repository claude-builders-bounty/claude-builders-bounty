---
name: inspect-android-emulator
description: "Inspect Android emulator via ADB: screenshot, UI dump. [DISABLED]"
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [adb, android, emulator, inspection, ui-automator]
    related_skills: [debug-wsl-windows-network, configure-ollama-wsl]
---

# Inspect Android Emulator

Inspect a running Android emulator (e.g., 雷电模拟器/LDPlayer) via ADB from WSL. Capture screenshots, dump UI hierarchy, list activities, and analyze top app — for legitimate testing/debugging only.

## When to Use

- Need to see what's on emulator screen (screenshot + vision analysis)
- Debugging own app: inspect UI hierarchy, current activity, package name
- Verify emulator connectivity from WSL via ADB
- Analyze app state without manual interaction

## Prerequisites

- ADB binary accessible from WSL (e.g., `/mnt/c/Users/Administrator/AppData/Local/Thunder Network/ldplayer/pre_ldplayer/adb.exe`)
- Emulator running with ADB enabled (default port 5554)
- `vision_analyze` tool available for image analysis
- Windows Defender / firewall allows ADB connection

## How to Run

```bash
# Set ADB path (adjust for your emulator)
ADB="/mnt/c/Users/Administrator/AppData/Local/Thunder Network/ldplayer/pre_ldplayer/adb.exe"

# 1. Verify connection
"$ADB" devices

# 2. Capture screenshot
"$ADB" exec-out screencap -p > /tmp/emulator_screen.png

# 3. Get current activity
"$ADB" shell dumpsys window windows | grep -E "mCurrentFocus|mFocusedApp|Activity"

# 4. Dump UI hierarchy (XML)
"$ADB" shell uiautomator dump /sdcard/ui.xml
"$ADB" pull /sdcard/ui.xml /tmp/ui.xml

# 5. Analyze with vision (if image captured)
# delegate_task(goal="Analyze screenshot for X", role="vision", context="image_path:/tmp/emulator_screen.png")
```

## Quick Reference

| Task | Command |
|------|---------|
| List devices | `"$ADB" devices` |
| Screenshot (PNG) | `"$ADB" exec-out screencap -p > screen.png` |
| Current activity | `"$ADB" shell dumpsys window windows \| grep mCurrentFocus` |
| All windows | `"$ADB" shell dumpsys window windows` |
| UI dump (XML) | `"$ADB" shell uiautomator dump /sdcard/ui.xml && "$ADB" pull /sdcard/ui.xml"` |
| Screen record | `"$ADB" shell screenrecord /sdcard/video.mp4` |
| Install APK | `"$ADB" install app.apk` |
| Start activity | `"$ADB" shell am start -n pkg/activity` |

## Procedure

### 1. Verify ADB Connection

```bash
ADB="/mnt/c/Users/Administrator/AppData/Local/Thunder Network/ldplayer/pre_ldplayer/adb.exe"
"$ADB" devices
# Should show: emulator-5554    device
```

**Success criterion:** Device listed as `device` (not `unauthorized` or `offline`).

### 2. Capture & Analyze Screenshot

```bash
"$ADB" exec-out screencap -p > /tmp/emulator_screen.png
file /tmp/emulator_screen.png
# Should show: PNG image data, 720 x 1280 (or emulator resolution)
```

### 3. Identify Top App & Activity

```bash
"$ADB" shell dumpsys window windows | grep -E "mCurrentFocus|mFocusedApp|Activity" | head -5
# Output shows: package/activity, e.g., com.quxianzhuan.wap/com.lt.app.MainActivity
```

### 4. Dump UI Hierarchy for Element Inspection

```bash
"$ADB" shell uiautomator dump /sdcard/ui.xml
"$ADB" pull /sdcard/ui.xml /tmp/ui.xml
# Parse /tmp/ui.xml for resource-id, text, bounds, class
```

### 5. (Optional) Vision Analysis

```python
delegate_task(
    goal="Describe the emulator screen: identify app, visible elements, any dialogs",
    role="vision",
    context="image_path: /tmp/emulator_screen.png"
)
```

## Pitfalls

- **ADB path varies** — LDPlayer, MuMu, Nox, Genymotion all have different ADB paths. Find yours with `where adb` on Windows.
- **WSL → Windows ADB** — Use full `.exe` path from WSL; `adb` in WSL may not connect to Windows emulator.
- **Unauthorized device** — Emulator shows RSA fingerprint prompt; accept on emulator screen.
- **Resolution mismatch** — Screenshots reflect emulator's current resolution (often 720x1280 portrait).
- **灰产红线** — This skill is for **legitimate testing/debugging only**. Automating task/earning apps (趣闲赚, etc.) violates user boundaries: no ad clicking, no account farming, no gray market automation.

## Verification

```bash
# 1. ADB connects
"$ADB" devices | grep -q "device$"

# 2. Screenshot valid
file /tmp/emulator_screen.png | grep -q "PNG image data"

# 3. Activity identified
"$ADB" shell dumpsys window windows | grep -q "mCurrentFocus"

# 4. UI dump parsed
test -s /tmp/ui.xml && xmllint --noout /tmp/ui.xml
```

---

*Skill distilled from session analysis (emulator inspection pattern in Feishu sessions). For compliant testing only — not for task/earning app automation.*