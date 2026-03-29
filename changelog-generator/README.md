# generate-changelog

Produce a structured `CHANGELOG.md` from git history, zero config needed.

## Usage

```bash
# From last tag to HEAD
bash generate-changelog

# Custom range
bash generate-changelog v1.0.0..HEAD

# Full history (first commit)
bash generate-changelog --init
```

## How it works

1. Reads `git log` between the last tag and `HEAD`
2. Parses conventional commit prefixes (`feat:`, `fix:`, `refactor:`, `remove:`)
3. Falls back to keyword heuristics for unprefixed commits
4. Outputs categorized `CHANGELOG.md`

## Categories

| Prefix / Keyword | Category |
|---|---|
| `feat:`, `feature:`, `add`, `new` | Added |
| `fix:`, `fix`, `resolve`, `patch` | Fixed |
| `refactor:`, `update`, `change`, `improve` | Changed |
| `remove:`, `delete`, `deprecate` | Removed |

## Install (2 steps)

```bash
# 1. Download
curl -O https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/changelog-generator/generate-changelog
chmod +x generate-changelog

# 2. Run
./generate-changelog
```

Also available as a Claude Code skill: copy `SKILL.md` into `.claude/skills/generate-changelog/`.

## Sample Output

```markdown
# Changelog

## [0.2.0] - 2026-03-29

### Added
- feat: add user authentication endpoint
- feat: implement dark mode toggle
- new dashboard analytics page

### Fixed
- fix: resolve login redirect loop
- patch memory leak in data processor

### Changed
- refactor: simplify database query builder

### Removed
- remove deprecated v1 API endpoints
```

## Requirements

- Git
- Bash 3+
- `perl` (for version bump — macOS/Linux default)

## License

MIT
