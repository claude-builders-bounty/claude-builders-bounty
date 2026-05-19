# Generate Changelog

Generate a structured `CHANGELOG.md` from a project's git history.

## Usage

Run this command in any git repository:

```
bash changelog.sh
```

Or with a custom range:

```
bash changelog.sh <since> <until>
```

## What it does

- Fetches commits since the **last git tag** (or all commits if no tags exist)
- Auto-categorizes by conventional commit prefix:
  - `feat` / `feature` → **Added**
  - `fix` / `bugfix` → **Fixed**
  - `refactor` / `perf` → **Changed**
  - `remove` / `drop` → **Removed**
  - Everything else → **Other**
- Skips merge commits
- Outputs a clean `CHANGELOG.md` with commit hash, author, and date

## Output format

```markdown
# Changelog

## v1.2.3 — 2026-05-19

### ✨ Added
- New login endpoint (abc1234) — Alice, 2026-05-18

### 🐛 Fixed
- Memory leak in worker pool (def5678) — Bob, 2026-05-17
```

## Requirements

- Git repository with at least one commit
- Bash shell (Linux, macOS, Git Bash on Windows)
