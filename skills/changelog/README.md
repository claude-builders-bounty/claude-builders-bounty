# 📝 Changelog Generator

Auto-generate structured `CHANGELOG.md` from git history.

## Usage (2 steps)

```bash
# 1. Run the script
bash changelog.sh

# 2. Optionally, since a specific tag
bash changelog.sh --since v1.0.0 --output CHANGELOG.md
```

## What it does

- Fetches commits since the last git tag (or full history)
- Auto-categorizes into: ✨ Added / 🐛 Fixed / 🔄 Changed / 🗑 Removed
- Uses conventional commit prefixes (`feat:`, `fix:`, etc.) for smart categorization
- Outputs a clean, Markdown-formatted `CHANGELOG.md`

## Requirements

- `bash` 4+
- `git` (any recent version)
