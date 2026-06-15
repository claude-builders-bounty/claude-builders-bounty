# generate-changelog

Generate a structured `CHANGELOG.md` from git commit history. Auto-categorizes commits by conventional commit prefix into Added / Fixed / Changed / Removed sections.

## Usage

```
/generate-changelog [--since <tag>] [--output <file>]
```

## What it does
1. Reads commits since the last git tag (or first commit if no tags exist)
2. Categorizes by conventional commit type:
   - `feat:` → Added
   - `fix:` → Fixed  
   - `refactor:`, `perf:`, `docs:`, `style:`, `test:`, `chore:` → Changed
   - `revert:` → Removed
3. Outputs a formatted `CHANGELOG.md`

## Setup
```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/tlyyxjz/claude-builders-bounty/main/changelog-skill/changelog.py

# 2. Make it executable  
chmod +x changelog.py

# 3. Run it
python changelog.py
```

## Example output
```markdown
# my-project Changelog

## Unreleased — 2026-06-15

### Added
- feat: add --json output mode
- feat: support dark mode toggle

### Fixed
- fix: login redirect loop on Safari
- fix: SQLite connection leak on hot reload
```
