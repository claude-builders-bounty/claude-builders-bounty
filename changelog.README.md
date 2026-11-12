# changelog.sh — structured CHANGELOG.md from git history

Generates a properly formatted `CHANGELOG.md` from your project's git history,
auto-categorized into Added / Fixed / Changed / Removed.

## Install & use (2 steps)
```bash
cp changelog.sh ./changelog.sh && chmod +x changelog.sh
bash changelog.sh v1.0.0 > CHANGELOG.md
```

## What it does
- Fetches commits since the **last git tag** (`git describe --tags --abbrev=0`)
- Auto-categorizes by conventional-commit prefix:
  - `feat`/`add` → **Added**
  - `fix`/`bug` → **Fixed**
  - `remove`/`drop`/`delete` → **Removed**
  - everything else → **Changed**
- Outputs a `## [version] - date` header with sections

## Sample output (tested on a real repo)
```markdown
## [v1.0.0] - 2026-11-12

### Added
- Add PR-review sub-agent (claude-review CLI)
- Add pre-tool-use hook blocking destructive bash commands
- feat: initial README with bounty board
```
