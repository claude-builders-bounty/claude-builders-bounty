# Auto CHANGELOG Generator 🚀

Generate a structured `CHANGELOG.md` from your git history — automatically.

## Setup (3 steps)

1. **Place** `changelog.py` and `changelog.sh` in your project root
2. **Run:**
   ```bash
   bash changelog.sh
   ```
3. **Check:** `CHANGELOG.md` appears with categorized commits

## Commands

| Command | Description |
|---------|-------------|
| `bash changelog.sh` | Generate in current directory |
| `bash changelog.sh --since v1.0.0` | Start from a specific tag |
| `bash changelog.sh --repo /path --output docs/CHANGELOG.md` | Custom paths |
| `/generate-changelog` | Run via Claude Code (with SKILL.md) |

## Requirements

- Python 3.8+
- Git CLI

## How It Categorizes

| Commit prefix | Section |
|---------------|---------|
| `feat:`, `add:`, `create:`, `implement:` | **Added** |
| `fix:`, `bugfix:`, `patch:`, `correct:`, `resolve:` | **Fixed** |
| `refactor:`, `chore:`, `update:`, `perf:`, `improve:` | **Changed** |
| `remove:`, `delete:`, `deprecate:`, `drop:` | **Removed** |
| Anything else | **Changed** (fallback) |
