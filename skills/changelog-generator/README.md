# Changelog Generator

Automatically generates a structured `CHANGELOG.md` from your git commit history.

## Setup (3 Steps)

```bash
# 1. Copy changelog.sh to your project
curl -O https://raw.githubusercontent.com/daletyler1737/claude-builders-bounty/main/changelog.sh

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it
./changelog.sh
```

## Requirements

- Git repository
- Bash 4.0+

## How It Works

- Uses git tags to scope commits (shows changes since last tag)
- Categorizes commits by prefix: `feat/add` → Added, `fix` → Fixed, etc.
- Outputs in [Keep a Changelog](https://keepachangelog.com/) format

## Pro Tip

Tag releases before running to get clean per-release changelogs:

```bash
git tag v1.0.0
./changelog.sh
git add CHANGELOG.md
git commit -m "docs: update changelog for v1.0.0"
```
