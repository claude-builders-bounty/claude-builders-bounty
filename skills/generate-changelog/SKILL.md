# Generate Changelog

Generate a structured `CHANGELOG.md` from the project's git history.

Commits are automatically categorized into:
- ✨ **Added** — new features
- 🐛 **Fixed** — bug fixes
- 🔧 **Changed** — refactors, perf, chore
- ⚠️ **Deprecated** — deprecation notices
- 🗑️ **Removed** — removed features
- 🔒 **Security** — security fixes
- 📝 **Documentation** — docs only
- 🧪 **Testing** — test changes

## Usage

```
/generate-changelog
```

Or from bash:

```bash
bash changelog.sh
```

## Options

| Flag | Description |
|------|-------------|
| `-o FILE` | Write to FILE instead of stdout |
| `-t TAG` | Start from TAG (default: latest) |
| `-v VER` | Version string (default: tag or "Unreleased") |
| `-r URL` | Repository URL (auto-detected from git remote) |
| `-c DIR` | Git repo path (default: current dir) |

## Examples

```bash
# Generate from latest tag
python scripts/generate_changelog.py -o CHANGELOG.md

# Generate from specific tag
python scripts/generate_changelog.py -t v1.0.0 -o CHANGELOG.md

# Preview without writing
python scripts/generate_changelog.py
```
