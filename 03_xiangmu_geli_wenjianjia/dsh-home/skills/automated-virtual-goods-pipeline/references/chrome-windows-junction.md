# Chrome on Windows: Playwright channel="chrome" Setup

## Problem
Playwright's `channel="chrome"` on Windows **only resolves the user-level path**:
```
%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe
```
It does NOT see system-level installs at `Program Files\Google\Chrome\Application\chrome.exe`.

## Solution: Extract Real Chrome + Junction to D: Drive

### Why Not Just Install?
- Official installer is "stub" (160 MB) that downloads the real payload at install time
- Stub downloads can be truncated (66 MB vs 160 MB) → `此应用无法在你的电脑上运行`
- Silent install `/silent /install` fails with exit code 5 on some Windows configs
- Installer places Chrome in Program Files (invisible to Playwright)

### Extraction Process (Offline, Deterministic)
```
ChromeStandaloneSetup64.exe (160 MB, signed)
    └─ 7z payload @ offset 0x48C894 → updater.7z (154 MB)
        └─ chrome_installer.exe (155 MB, AMD64 PE)
            └─ 7z payload @ offset 0x4FB4 → chrome.7z (491 MB)
                └─ Chrome-bin/ (492 MB)
                    ├─ chrome.exe (4.6 MB)
                    ├─ chrome_proxy.exe
                    └─ 155.0.8059.80/ (32 files: chrome.dll, *.pak, *.dll, etc.)
```

### Deploy to User-Level Path + D: Drive Junction
```powershell
# Physical payload on D:
$target = 'D:\Ai\Google\Chrome\Application'
Move-Item 'Chrome-bin\*' $target

# Junction at user-level path (Playwright finds this)
$link = "$env:LOCALAPPDATA\Google\Chrome"
New-Item -ItemType Junction -Path $link -Target 'D:\Ai\Google\Chrome'
```

### Verification
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome', headless=True)
    print(f'OK: {b.version}')  # Should print 155.0.8059.80
    b.close()
```

### Automated Script
Use `scripts/extract_chrome_windows.py` — handles download (with resume), signature verification, multi-layer 7z extraction, junction creation, and verification.

### Key Principle
**Extract once, junction forever.** The 492 MB payload stays on D: drive; C: drive only holds the junction reparse point. Re-runs are idempotent.
