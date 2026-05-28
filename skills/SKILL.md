# Generate Changelog

Generate a structured `CHANGELOG.md` from your git history, auto-categorized by commit prefix.

## Usage

```
/generate-changelog
```

Or with options:

```bash
bash changelog.sh --since v1.2.0 --until HEAD --output CHANGELOG.md
bash changelog.sh --since 2026-01-01
```

## What It Does

1. Fetches commits since the last git tag (or a specified range)
2. Categorizes each commit by conventional commit prefix:
   - `feat:` → **Added**
   - `fix:` → **Fixed**
   - `refactor:` / `perf:` → **Changed**
   - `docs:` → **Documentation**
   - `test:` → **Tests**
   - `chore:` / `ci:` → **Maintenance**
   - `BREAKING CHANGE:` → **Breaking Changes**
3. Writes a dated section to `CHANGELOG.md`

## Example Output

```markdown
## [v1.3.0] — 2026-05-28

### Added
- Add dark mode toggle (a1b2c3d)
- Support CSV export in reports (e4f5g6h)

### Fixed
- Fix null pointer in auth middleware (i7j8k9l)

### Maintenance
- Upgrade dependencies to latest (m1n2o3p)
```

## Installation

```bash
curl -O https://raw.githubusercontent.com/Nova17000/claude-builders-bounty/bounty-1-changelog/skills/changelog.sh
chmod +x changelog.sh
```

Add to your `CLAUDE.md`:
```
## Available Skills
- `/generate-changelog` → runs `bash changelog.sh` in project root
```
