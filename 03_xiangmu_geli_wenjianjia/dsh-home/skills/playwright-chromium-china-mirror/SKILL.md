---
name: playwright-chromium-china-mirror
description: Configure Playwright/Chromium domestic mirror (npmmirror) for fast downloads in China.
version: 0.1.0
author: User (Hermes Agent)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [playwright, chromium, mirror, npmmirror, china, download, browser]
    related_skills: [configure-feishu-gateway, wsl2-windows-interop-automation, hermes-systemd-timers-setup]
---

# Playwright Chromium China Mirror

Configure Playwright to download Chromium and browser binaries via the npmmirror (阿里云镜像) domestic CDN instead of the official Google/Microsoft CDN. Essential for WSL2/Windows users in China where direct downloads fail or are extremely slow.

## When to Use

- `npx playwright install chromium` times out or fails
- `browser_exec` / `cua-driver` browser automation fails due to missing Chromium
- Running in China mainland network environment
- Need persistent configuration across WSL restarts and gateway restarts

Don't use for:
- Non-China network environments (official CDN is faster outside China)
- Other browsers (Firefox, WebKit) unless they also need mirroring

## Prerequisites

- Playwright installed (`npm install -g playwright` or via project)
- WSL2 with systemd or Windows host
- Network access to `npmmirror.com` (阿里云镜像)
- `hermes-gateway` systemd service for persistent config

## How to Run

```bash
# Quick one-liner (temporary, current shell only)
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/

# Persistent: add to ~/.profile
echo 'export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/' >> ~/.profile
source ~/.profile

# Persistent for systemd service (gateway)
mkdir -p ~/.config/systemd/user/hermes-gateway.service.d/
cat > ~/.config/systemd/user/hermes-gateway.service.d/playwright-mirror.conf << 'EOF'
[Service]
Environment=PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
EOF
systemctl --user daemon-reload
systemctl --user restart hermes-gateway
```

## Quick Reference

| Method | Scope | Persistence |
|--------|-------|-------------|
| `export PLAYWRIGHT_DOWNLOAD_HOST=...` | Current shell only | ❌ |
| `~/.profile` | User login shells | ✅ |
| Systemd drop-in | `hermes-gateway` service | ✅ (recommended) |
| `.env` file | All Hermes processes | ✅ (if gateway reads .env) |

## Procedure

### 1. Verify Mirror Accessibility

**Completion criterion**: Mirror URL responds with directory listing.

```bash
# Test mirror reachable
curl -sI https://npmmirror.com/mirrors/playwright/ | head -1
# Expected: HTTP/2 200 or HTTP/1.1 200

# Test specific Chromium version listing
curl -s https://npmmirror.com/mirrors/playwright/chromium-1169/ | head -5
# Should show file listing (Linux/Win/Mac builds)
```

### 2. Configure Temporary (Current Shell)

**Completion criterion**: `PLAYWRIGHT_DOWNLOAD_HOST` env var set.

```bash
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
echo $PLAYWRIGHT_DOWNLOAD_HOST
```

### 3. Configure Persistent for User Shell (`~/.profile`)

**Completion criterion**: Variable set on every new shell.

```bash
# Add to profile (idempotent - won't duplicate if already present)
grep -q 'PLAYWRIGHT_DOWNLOAD_HOST' ~/.profile || \
  echo 'export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/' >> ~/.profile

# Reload
source ~/.profile

# Verify
echo $PLAYWRIGHT_DOWNLOAD_HOST
```

### 4. Configure Persistent for Gateway (Systemd Drop-in) — RECOMMENDED

**Completion criterion**: Gateway service has env var; survives restart.

```bash
# Create drop-in directory
mkdir -p ~/.config/systemd/user/hermes-gateway.service.d/

# Write environment file
cat > ~/.config/systemd/user/hermes-gateway.service.d/playwright-mirror.conf << 'EOF'
[Service]
Environment=PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
EOF

# Reload systemd and restart gateway
systemctl --user daemon-reload
systemctl --user restart hermes-gateway

# Verify in gateway logs
journalctl --user -u hermes-gateway -n 50 --no-pager | grep -i playwright
# Should see chromium download using npmmirror URLs
```

### 5. Verify Chromium Download Works

**Completion criterion**: Chromium downloads and installs successfully.

```bash
# Test download (dry run first)
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ \
  npx playwright install chromium --dry-run 2>&1 | head -20

# Actual install (if not already installed)
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ \
  npx playwright install chromium

# Verify binary exists
ls -la ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome
# Or for Windows interop:
ls -la /mnt/c/Users/$USER/AppData/Local/ms-playwright/chromium-*/chrome-win/chrome.exe
```

### 6. Verify Browser Automation Works

**Completion criterion**: `browser_exec` or `computer_use` can launch browser.

```bash
# Test via Hermes CLI
hermes chat -q "Test browser" --skills browser_exec

# Or direct browser test
cd /home/user01/.hermes/python && python3 -c "
from browser_use import Browser
import asyncio
async def test():
    browser = Browser()
    await browser.new_page('https://example.com')
    print(await browser.page.title())
    await browser.close()
asyncio.run(test())
"
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| Mirror URL changes | Check https://npmmirror.com/mirrors/playwright/ for current path |
| Gateway doesn't pick up env var | Ensure drop-in file is in `hermes-gateway.service.d/`, run `daemon-reload`, `restart` |
| Windows interop path differs | Windows stores cache at `%LOCALAPPDATA%\ms-playwright\`; WSL at `~/.cache/ms-playwright/` |
| Multiple Playwright versions | Each version has separate folder; mirror must have matching version |
| Firewall blocks npmmirror | Verify `curl https://npmmirror.com` works; corporate proxy may need config |
| `browser_exec` uses different cache | Set env var in gateway service (drop-in) since it spawns browser processes |

## Verification

```bash
# 1. Environment variable in gateway process
systemctl --user show hermes-gateway --property=Environment | grep PLAYWRIGHT
# Should show: PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/

# 2. Chromium binary present
ls ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome 2>/dev/null | head -1
# Or on Windows host:
ls /mnt/c/Users/$USER/AppData/Local/ms-playwright/chromium-*/chrome-win/chrome.exe 2>/dev/null | head -1

# 3. Download speed test (should be fast in China)
time curl -o /dev/null -s -w '%{speed_download}\n' https://npmmirror.com/mirrors/playwright/chromium-1169/chromium-linux.zip
# Expect: > 1MB/s on typical China broadband

# 4. End-to-end browser test
hermes chat -q "Open example.com and tell me the title" --skills browser_exec
# Should succeed without timeout
```

## Mirror Alternatives (If npmmirror Fails)

```bash
# Alternative mirrors (less reliable):
# export PLAYWRIGHT_DOWNLOAD_HOST=https://mirrors.huaweicloud.com/playwright/
# export PLAYWRIGHT_DOWNLOAD_HOST=https://mirrors.tuna.tsinghua.edu.cn/playwright/
# export PLAYWRIGHT_DOWNLOAD_HOST=https://mirrors.aliyun.com/playwright/

# Official (fallback, slow in China):
# unset PLAYWRIGHT_DOWNLOAD_HOST
```

---

*Distilled from session 20260924_151137_4b2afe9e (531 messages: Ollama WSL network fix included Playwright Chromium download via npmmirror). Pattern: domestic mirror required for Chromium download in China; persistent config via systemd drop-in for gateway; verified working with browser_exec and cua-driver.*