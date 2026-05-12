# changelog.sh

Generate a structured `CHANGELOG.md` from git history. Works with conventional commits and auto-categorizes into **Added / Fixed / Changed / Removed / Other**.

## Setup (3 steps)

```bash
# 1. Download
curl -sO https://raw.githubusercontent.com/mrzhangkris/claude-builders-bounty/main/changelog.sh

# 2. Make executable
chmod +x changelog.sh

# 3. Run in any git repo
./changelog.sh
```

## Usage

```bash
# Generate since last tag (default)
./changelog.sh

# Generate from a specific tag
./changelog.sh --from v1.0.0

# Generate between two tags
./changelog.sh --range v1.0.0..v2.0.0

# Custom output file
./changelog.sh --output RELEASE_NOTES.md
```

## How it works

1. Finds commits since the last git tag (or uses `--from`/`--range`)
2. Categorizes each commit by **conventional commit type** (`feat:`, `fix:`, `refactor:`, etc.)
3. Falls back to **keyword matching** for non-conventional commits
4. Outputs a clean `CHANGELOG.md` with emoji section headers

### Categories

| Section | Conventional Commits | Keyword Fallback |
|---------|---------------------|------------------|
| ✨ Added | `feat`, `feature` | add, new, implement, create, introduce, support |
| 🐛 Fixed | `fix`, `bugfix`, `hotfix` | fix, resolve, patch, correct, bug |
| 🔧 Changed | `refactor`, `style`, `perf`, `change`, `update` | update, refactor, improve, optimize, rename |
| 🗑️ Removed | `remove`, `deprecate` | remove, delete, deprecate, drop |
| 📝 Other | `chore`, `ci`, `build`, `docs` | (everything else) |

## Sample Output

```markdown
# Changelog

## [Unreleased] — 2026-05-12

### ✨ Added

- GitHub OAuth integration for user authentication
- Toast notification system with auto-dismiss

### 🐛 Fixed

- Resolve crash when loading empty state
- Fix memory leak in WebSocket connection handler

### 🔧 Changed

- Refactor database connection pooling logic
- Update dependencies to latest versions
- Improve mobile responsive layout for dashboard

### 🗑️ Removed

- Deprecate legacy v1 API endpoints

### 📝 Other

- Bump CI runner to Ubuntu 24.04
- Add contributing guidelines
```

## Requirements

- `git` (macOS & Linux compatible, no extra dependencies)

## License

MIT
