# 📋 CHANGELOG Generator

A Claude Code skill + bash script that auto-generates structured CHANGELOG.md from git history.

[BOUNTY $50] claude-builders-bounty #1

## Installation (3 steps)

```bash
# 1. Copy files into your project
cp changelog.sh SKILL.md YOUR_PROJECT/

# 2. Make executable
chmod +x YOUR_PROJECT/changelog.sh

# 3. Run
bash changelog.sh
```

## Usage

### In Claude Code

Just type `/generate-changelog` — Claude will run the script and output a formatted CHANGELOG.md.

### Standalone

```bash
# Generate for current directory
bash changelog.sh

# Generate for a specific repo
bash changelog.sh /path/to/repo
```

## How It Works

1. Finds the latest git tag for version number
2. Collects all commits since that tag
3. Auto-categorizes by commit prefix:
   - `feat:` / `add:` → **Added**
   - `fix:` / `bug:` / `hotfix:` → **Fixed**
   - `refactor:` / `perf:` / `style:` / `docs:` / `chore:` / `ci:` → **Changed**
   - `remove:` / `drop:` / `revert:` → **Removed**
   - Everything else → **Changed**
4. Outputs properly formatted `CHANGELOG.md`

## Sample Output

```markdown
# Changelog

## [v1.2.0] - 2026-05-18

### Added
- feat: add user authentication system
- add: implement dark mode toggle

### Fixed
- fix: resolve login timeout on slow connections

### Changed
- refactor: migrate API calls to use async/await
- chore: update dependencies

### Removed
- remove: drop deprecated /v1/ endpoint
```

## Tested On

Tested on a real git repo with 5 commits across all 4 categories:

```
✅ CHANGELOG.md generated (5 commits → v1.0.0)

- feat: initial commit → Added
- fix: resolve login timeout → Fixed
- add: implement dark mode → Added
- refactor: migrate to async/await → Changed
- remove: drop legacy API → Removed
- some random change without prefix → Changed
```

## Requirements

- bash
- git

## License

MIT
