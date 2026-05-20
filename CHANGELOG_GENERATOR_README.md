# CHANGELOG Generator

Auto-generate a structured `CHANGELOG.md` from your git commit history.

## Features

- ✅ Fetches commits since last git tag
- ✅ Auto-categorizes into: `Added` / `Fixed` / `Changed` / `Removed`
- ✅ Outputs properly formatted `CHANGELOG.md`
- ✅ Works with any git repository

## Setup (3 steps)

1. **Download the script:**
   ```bash
   curl -O https://raw.githubusercontent.com/tankotan/claude-builders-bounty/main/changelog.sh
   chmod +x changelog.sh
   ```

2. **Run in your git repo:**
   ```bash
   bash changelog.sh
   ```

3. **Done!** Check `CHANGELOG.md` in your project root.

## Usage

```bash
# Generate CHANGELOG.md (default)
bash changelog.sh

# Custom output file
bash changelog.sh HISTORY.md
```

## How it works

The script:
1. Finds the last git tag (or uses all commits if no tags exist)
2. Fetches commits since that tag
3. Categorizes commits based on prefixes:
   - `feat:`, `add:` → **Added**
   - `fix:`, `bugfix:` → **Fixed**
   - `refactor:`, `perf:`, `style:` → **Changed**
   - `remove:`, `delete:` → **Removed**
   - Everything else → **Changed**
4. Outputs a formatted `CHANGELOG.md`

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [2026.05.20] - 2026-05-20

### Added
- feat: add user authentication
- add: implement payment gateway

### Fixed
- fix: resolve login bug
- bugfix: correct API timeout

### Changed
- refactor: optimize database queries
- Update README documentation
```

## Requirements

- Git installed
- Bash shell (Linux/macOS/WSL)

## License

MIT
