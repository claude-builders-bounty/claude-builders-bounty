# Generate Changelog

Auto-generate a structured `CHANGELOG.md` from git history, categorizing commits into **Added**, **Fixed**, **Changed**, and **Removed** sections.

## Setup (3 steps)

1. **Copy** `changelog.sh` and `SKILL.md` into your project root
2. **Make executable**: `chmod +x changelog.sh`
3. **Run**: `bash changelog.sh`

## Usage

### As a bash script

```bash
# Generate CHANGELOG.md in the current directory
bash changelog.sh

# Specify a custom output file
bash changelog.sh my-changelog.md
```

### As a Claude Code skill

Place `SKILL.md` in your project's `.claude/skills/` directory, then invoke:

```
/generate-changelog
```

## How It Works

- Detects the most recent git tag and fetches all commits since then
- If no tags exist, processes the entire commit history
- Categorizes using **conventional commit prefixes** first (`feat:`, `fix:`, `refactor:`, etc.)
- Falls back to **keyword matching** for non-conventional messages
- Strips prefixes for clean, readable entries
- Includes short commit hashes for traceability
- Preserves existing changelog entries when prepending new sections

## Categories

| Category | Conventional Prefixes | Keyword Triggers |
|----------|----------------------|------------------|
| Added | `feat:` | add, new, introduce, implement, create |
| Fixed | `fix:` | fix, bug, patch, resolve, correct |
| Changed | `refactor:`, `perf:`, `style:`, `docs:`, `build:`, `ci:`, `chore:`, `test:` | update, change, improve, enhance |
| Removed | `revert:` | remove, delete, deprecate, drop |

## Example Output

```markdown
# Changelog

## [Unreleased] — 2026-03-28

### Added
- add user authentication flow (a1b2c3d)
- implement dark mode toggle (d4e5f6a)

### Fixed
- fix memory leak in WebSocket handler (b7c8d9e)

### Changed
- update dependency versions (f0a1b2c)
- refactor database connection pooling (c3d4e5f)
```

## License

MIT
