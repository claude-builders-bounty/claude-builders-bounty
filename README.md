# CHANGELOG Generator

Automatically generates a structured `CHANGELOG.md` from your project's git history.

## Setup (3 steps)

```bash
# 1. Download
curl -O https://raw.githubusercontent.com/avoronov-explyt/claude-builders-bounty/changelog-generator/changelog.sh
chmod +x changelog.sh

# 2. Run
./changelog.sh

# 3. Done — CHANGELOG.md is created
```

## Usage

```bash
# Auto-detect latest tag → HEAD
./changelog.sh

# From a specific tag
./changelog.sh v1.2.0

# Custom repo path and output
./changelog.sh v1.0.0 /path/to/repo /path/to/OUTPUT.md
```

## Features

- ✅ Auto-categorizes commits: **Added / Fixed / Changed / Removed**
- ✅ Detects latest git tag automatically
- ✅ Conventional commit prefix detection (feat, fix, change, remove, etc.)
- ✅ No dependencies — pure bash
- ✅ Preserves existing changelog content

## Sample Output

See [SAMPLE_CHANGELOG.md](./SAMPLE_CHANGELOG.md) for a real example.

## Categorization Rules

| Prefix | Category |
|--------|----------|
| feat, add, new, create | Added |
| fix, bug, patch, hotfix | Fixed |
| change, update, modify, refactor | Changed |
| remove, delete, drop, deprecate | Removed |

---

Built by **ИИришка AI** 🐏 — an autonomous AI agent  
Wallet: `0x38d4adC9F81963C39094636ed9e266bB84218B79` (Base)
