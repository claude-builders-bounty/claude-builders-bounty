# generate-changelog

A Claude Code skill that generates a structured `CHANGELOG.md` from git history.

## Usage

```
/generate-changelog [--since <tag|ref>] [--output FILE]
```

Or standalone:

```bash
./generate-changelog
./generate-changelog --since v1.0.0 -o docs/CHANGELOG.md
```

## What it does

1. Fetches commits since the last git tag (or a custom ref)
2. Auto-categorizes commits into:
   - ✨ **Added** — new features (`feat:`, `add:`, `implement:`)
   - 🐛 **Fixed** — bug fixes (`fix:`, `bugfix:`, `patch:`)
   - 🔄 **Changed** — refactors, updates, improvements (`refactor:`, `update:`, `perf:`)
   - 🗑 **Removed** — deleted or deprecated features (`remove:`, `deprecate:`)
   - 📦 **Other** — everything else
3. Writes a properly formatted `CHANGELOG.md`

## Setup

### Step 1: Install

```bash
# Copy the script to your project
cp generate-changelog /path/to/your-project/
chmod +x /path/to/your-project/generate-changelog
```

### Step 2: Configure Claude Code (optional)

Add to your `CLAUDE.md`:

```markdown
## Changelog
Run \`./generate-changelog\` to auto-generate or update CHANGELOG.md before tagging a release.
```

### Step 3: Generate

```bash
cd /path/to/your-project
./generate-changelog
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CHANGELOG_FILE` | `CHANGELOG.md` | Output file path |

## Sample Output

```markdown
# Changelog

## [v1.2.0] - 2026-07-08

### ✨ Added
- Dark mode support ([abc1234](https://github.com/user/repo/commit/abc1234))
- API rate limiting ([def5678](https://github.com/user/repo/commit/def5678))

### 🐛 Fixed
- Login redirect loop ([ghi9012](https://github.com/user/repo/commit/ghi9012))

### 🔄 Changed
- Upgrade dependencies to latest ([jkl3456](https://github.com/user/repo/commit/jkl3456))
```

## Technical Notes

- Uses conventional commit prefixes (`feat:`, `fix:`, etc.) for categorization
- Falls back to last annotated tag, then initial commit if no tags exist
- Generates clickable commit links when an `origin` remote is detected
- Compatible with Bash 3.2+ (macOS default) and zsh
