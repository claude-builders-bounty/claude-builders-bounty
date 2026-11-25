---
name: fanqie-publisher-cli
description: "Publish novels to 番茄 using fanqie-publisher-cli Node tool."
version: 0.1.0
author: User (Hermes Agent)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - fanqie
    - publisher
    - novel-pipeline
    - cli
    - automation
    related_skills:
    - novel-generation-pipeline
    - qbook-ranking-scraper
---

# fanqie-publisher-cli Integration

Publish generated novels to 番茄小说 (Fanqie) using the fanqie-publisher-cli Node.js tool. Novel pipeline step 7 (发布).

## When to Use

- Need to publish chapters to 番茄作家后台 automatically
- fanqie-publisher-cli not installed or failing
- Need to configure 番茄 Cookie for authentication
- Dry-run testing before real publish

**Don't use for:**
- Non-番茄 platforms (起点, 晋江, etc.)
- Manual publishing (use browser directly)

## Prerequisites

- Node.js + npm (for `fanqie-publisher-cli`)
- 番茄作家后台 Cookie (登录后获取)
- fanqie-publisher-cli installed at `~/fanqie-publisher-cli` (git clone + npm install)
- Generated novel chapters in InkOS project structure

## How to Run

```bash
# 1. Install fanqie-publisher-cli (one-time, China network)
git clone https://github.com/funnaz/fanqie-publisher-cli ~/fanqie-publisher-cli
cd ~/fanqie-publisher-cli && npm config set registry https://registry.npmmirror.com && npm install

# 2. Get 番茄 Cookie (manual: login → DevTools → Application → Cookies)
# Copy cookie string (e.g., "sessionid=xxx; uid=yyy; ...")

# 3. Create publish config
cat > /tmp/fanqie_config.json <<'EOF'
{
  "book": "测试小说",
  "chapters": "/home/user01/novel-pipeline/my-novel/books/测试小说/chapters",
  "url": "https://fanqienovel.com/writer/zone",
  "newUrl": "",
  "minChars": 1000,
  "delay": 1200,
  "confirmEvery": 5,
  "confirmEach": false,
  "strictQuality": true
}
EOF

# 4. Dry-run test
node ~/fanqie-publisher-cli/fanqie-publisher.js --config /tmp/fanqie_config.json --cookie "YOUR_COOKIE" --dry-run

# 5. Real publish (when ready)
# node ~/fanqie-publisher-cli/fanqie-publisher.js --config /tmp/fanqie_config.json --cookie "YOUR_COOKIE"
```

## Quick Reference

| Task | Command |
|------|---------|
| Install CLI | `git clone https://github.com/funnaz/fanqie-publisher-cli ~/fanqie-publisher-cli && cd ~/fanqie-publisher-cli && npm install` |
| Get Cookie | Login 番茄作家后台 → DevTools → Application → Cookies → Copy all |
| Dry-run | `node ~/fanqie-publisher-cli/fanqie-publisher.js --config <config.json> --cookie "<COOKIE>" --dry-run` |
| Real publish | Same as dry-run but remove `--dry-run` |
| Check install | `node ~/fanqie-publisher-cli/fanqie-publisher.js --help` |

## Procedure

### 1. Install fanqie-publisher-cli

**Completion criterion**: `node ~/fanqie-publisher-cli/fanqie-publisher.js --help` shows usage.

```bash
# Use China npm mirror
npm config set registry https://registry.npmmirror.com

# Clone and install (npm publish may timeout/404)
git clone https://github.com/funnaz/fanqie-publisher-cli ~/fanqie-publisher-cli
cd ~/fanqie-publisher-cli
npm install

# Verify
node fanqie-publisher.js --help
# Should show: "Usage: fanqie-publisher [options]"
```

### 2. Obtain 番茄 Cookie

**Completion criterion**: Valid cookie string that authenticates to 番茄作家后台.

```bash
# Manual steps (do once, cookie expires ~30 days):
# 1. Open https://fanqienovel.com/writer/zone in browser
# 2. Login with your 番茄 author account
# 3. F12 → Application → Cookies → https://fanqienovel.com
# 4. Copy all cookie values as single string: "key1=val1; key2=val2; ..."
# 5. Save to secure location (e.g., ~/.hermes/fanqie_cookie.txt)
```

### 3. Prepare Chapter Files

**Completion criterion**: Chapters exist in InkOS project structure (`books/<title>/chapters/*.md`).

```bash
# Typical path from InkOS
ls -la /home/user01/novel-pipeline/my-novel/books/测试小说/chapters/
# Should show: 001.md, 002.md, 003.md, ...

# Each chapter should be 2000+ chars for quality
wc -c /home/user01/novel-pipeline/my-novel/books/测试小说/chapters/*.md
```

### 4. Create Publish Config

**Completion criterion**: Valid JSON config with correct paths.

```json
{
  "book": "测试小说",
  "chapters": "/home/user01/novel-pipeline/my-novel/books/测试小说/chapters",
  "url": "https://fanqienovel.com/writer/zone",
  "newUrl": "",
  "minChars": 1000,
  "delay": 1200,
  "confirmEvery": 5,
  "confirmEach": false,
  "strictQuality": true
}
```

### 5. Dry-Run Test

**Completion criterion**: Dry-run completes without errors, shows chapters to be published.

```bash
COOKIE=$(cat ~/.hermes/fanqie_cookie.txt)
node ~/fanqie-publisher-cli/fanqie-publisher.js \
  --config /tmp/fanqie_config.json \
  --cookie "$COOKIE" \
  --dry-run

# Expected output:
# 📖 准备发布: 测试小说
# 📁 章节目录: /home/user01/novel-pipeline/my-novel/books/测试小说/chapters
# 📋 找到 3 个章节文件
# ✅ Dry-run 完成，未实际发布
```

### 6. Real Publish (When Ready)

**Completion criterion**: Chapters appear in 番茄作家后台 "我的作品" → "章节管理".

```bash
# ⚠️ Only after dry-run succeeds and user confirms
node ~/fanqie-publisher-cli/fanqie-publisher.js \
  --config /tmp/fanqie_config.json \
  --cookie "$COOKIE"

# Monitor: check 番茄作家后台 for published chapters
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| **npm install 超时/404** | 用 `git clone` + `npm config set registry https://registry.npmmirror.com` 后 `npm install` |
| **Cookie 失效/错误** | 重新登录获取新 Cookie；确保复制完整 cookie 字符串 |
| **章节目录为空** | 检查 InkOS 生成输出路径；`inkos write next` 后章节在 `books/<title>/chapters/` |
| **字符数不足** | `minChars: 1000` 默认；短章会被跳过，用 `inkos write next --count 1` 多生成几章 |
| **发布太快被限流** | `delay: 1200` (ms) 间隔；`confirmEvery: 5` 每 5 章人工确认；调大 delay |
| **Node 路径问题** | cron/后台用绝对路径 `/home/user01/.nvm/versions/node/vXX/bin/node` |

## Verification

```bash
# 1. CLI installed
node ~/fanqie-publisher-cli/fanqie-publisher.js --help | grep -q "Usage" && echo "✅ CLI installed"

# 2. Cookie file exists
test -f ~/.hermes/fanqie_cookie.txt && echo "✅ Cookie saved"

# 3. Dry-run works
COOKIE=$(cat ~/.hermes/fanqie_cookie.txt)
node ~/fanqie-publisher-cli/fanqie-publisher.js --config /tmp/fanqie_config.json --cookie "$COOKIE" --dry-run 2>&1 | grep -q "Dry-run" && echo "✅ Dry-run OK"

# 4. Chapter files exist
ls /home/user01/novel-pipeline/my-novel/books/测试小说/chapters/*.md 2>/dev/null | wc -l | xargs -I{} test {} -gt 0 && echo "✅ Chapters ready"
```

---

*Distilled from session 20261004_100635_3c5af9a0 (Oct 4, 2026) — fanqie-publisher-cli needs git clone install (npm publish may timeout), Cookie configuration, and dry-run testing before real publish. Novel pipeline step 7 (发布). Occurs in novel pipeline runs.*