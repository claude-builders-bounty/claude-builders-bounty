# [BOUNTY $50] CHANGELOG Generator

A simple bash script that generates a structured `CHANGELOG.md` from your git history.

> **Bounty Submission for Issue #1** — by @cendd

## Setup (3 steps)

1. **Download** the script:
   ```bash
   curl -O https://raw.githubusercontent.com/cendd/claude-builders-bounty/main/changelog.sh
   ```

2. **Make executable**:
   ```bash
   chmod +x changelog.sh
   ```

3. **Run it** in your project:
   ```bash
   bash changelog.sh
   ```

## Usage

```bash
# Default: generates CHANGELOG.md in current directory
bash changelog.sh

# Custom output file
bash changelog.sh CHANGELOG.md

# From a different repo directory
bash changelog.sh CHANGELOG.md /path/to/repo
```

## Output

Auto-categorizes commits into:
| Category | Prefixes |
|----------|----------|
| **Added**  | `feat:`, `add:`, `feature:`, `new:` |
| **Changed** | everything else (refactor, chore, docs, etc.) |
| **Fixed**  | `fix:`, `bugfix:`, `hotfix:`, `bug:` |
| **Removed** | `remove:`, `delete:`, `drop:`, `deprecate:` |

Uses the latest git tag as baseline. Falls back to first commit if no tags exist.

## Sample Output

```markdown
# Changelog

## [v1.2.0] - 2026-05-24

### Added
- feat: add user authentication flow (a1b2c3d)

### Changed
- refactor: optimize database queries (i7j8k9l)

### Fixed
- fix: correct pagination offset (q3r4s5t)
```
