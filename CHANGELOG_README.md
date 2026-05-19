# changelog.sh — Git Changelog Generator

> Generate a structured `CHANGELOG.md` from your project's git history in one command.

## Quick Start (3 steps)

1. **Copy the script** into your project:
   ```bash
   curl -O https://raw.githubusercontent.com/<you>/<repo>/main/changelog.sh
   chmod +x changelog.sh
   ```

2. **Run it** inside any git repo:
   ```bash
   bash changelog.sh
   ```

3. **That's it** — `CHANGELOG.md` is generated automatically.

## Usage

```bash
# Default: commits since last tag
bash changelog.sh

# Custom range
bash changelog.sh v1.0.0 v1.2.0
bash changelog.sh abc123 HEAD
```

## How it works

| Commit prefix | Category |
|---|---|
| `feat` / `feature` | ✨ Added |
| `fix` / `bugfix` | 🐛 Fixed |
| `refactor` / `perf` | 🔧 Changed |
| `remove` / `drop` | 🗑️ Removed |
| *(anything else)* | 📝 Other |

- Merge commits are automatically skipped
- Each entry includes short hash, author, and date
- Uses conventional commit parsing (supports `feat:`, `fix:`, etc.)

## Claude Code Integration

This project also includes a `SKILL.md` for use with Claude Code. Add it to your Claude Code skills directory for the `/generate-changelog` command.

## License

MIT
