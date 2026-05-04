# CHANGELOG Generator

Generate a structured `CHANGELOG.md` from your git commit history, auto-categorized into **Added / Fixed / Changed / Removed** sections.

## Setup (3 steps)

1. `git clone <this-repo>`
2. `chmod +x changelog.sh`
3. `./changelog.sh`

The script outputs `CHANGELOG.md` in the current directory.

## Usage

```bash
# Run in any git repo
cd /path/to/your/repo
bash /path/to/changelog.sh

# Or pass a repo path as argument
bash changelog.sh /path/to/your/repo
```

## How It Works

- Finds the **last git tag** and collects all commits since then
- If no tags exist, uses **all commits**
- Categorizes commits by prefix:
  - `feat:`, `add:`, `new:` → **Added**
  - `fix:`, `bugfix:`, `hotfix:` → **Fixed**
  - `update:`, `refactor:`, `chore:`, `docs:`, `perf:` → **Changed**
  - `remove:`, `delete:`, `deprecate:` → **Removed**
  - Everything else → **Other**
- Supports conventional commits with scopes, e.g. `feat(auth): add login`

## Example Output

```markdown
# Changelog

## [v1.2.0] - 2025-05-04

### Added

- feat: add user authentication (a1b2c3d)

### Fixed

- fix: resolve login timeout (e4f5g6h)

### Changed

- refactor: improve API response time (i7j8k9l)
```
