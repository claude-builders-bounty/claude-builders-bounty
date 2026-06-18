# Generate CHANGELOG from Git History

A Claude Code skill that automatically produces a structured `CHANGELOG.md` from a project's git history. Categorizes commits into **Added / Fixed / Changed / Removed** based on conventional commit prefixes.

## What you get

- `CHANGELOG.md` with the most recent release section
- Auto-categorized subsections (no manual sorting)
- Works on any git repo with `feat:` / `fix:` / `BREAKING:` style commits
- Sample output included in this README

## Sample output

Running on a fictional project:

```
$ bash changelog.sh
CHANGELOG written to CHANGELOG.md (12 commits processed)
```

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0 - 2026-06-18]

### Added

- User profile page with avatar upload
- Dark mode toggle in settings

### Fixed

- Login redirect loop on Safari
- Memory leak in image cache

### Changed

- Upgraded React to 18.3
- Refactored authentication module

### Removed

- Deprecated v1 API endpoints
```

## Installation (3 steps)

### Step 1: Copy the skill

```bash
mkdir -p ~/.claude/skills/changelog
cp changelog.sh ~/.claude/skills/changelog/
cp SKILL.md ~/.claude/skills/changelog/
chmod +x ~/.claude/skills/changelog/changelog.sh
```

### Step 2: Register the skill

In Claude Code, the skill auto-loads from `~/.claude/skills/changelog/SKILL.md`. No registration needed if you place it there.

For project-local use, copy the folder into `<your-project>/.claude/skills/changelog/`.

### Step 3: Use it

- In Claude Code: type `/generate-changelog`
- From the shell: `bash ~/.claude/skills/changelog/changelog.sh`

Output defaults to `CHANGELOG.md`. Pass a path to override:

```bash
bash changelog.sh docs/CHANGELOG.md
```

## How it categorizes

| Commit prefix | Category |
|---|---|
| `feat:` | Added |
| `fix:` | Fixed |
| `docs:`, `style:`, `refactor:`, `perf:`, `test:`, `chore:`, `build:`, `ci:` | Changed |
| `BREAKING:`, `revert:`, subject contains "Remove" or "Delete" | Removed |
| Anything else | Changed (fallback) |

The script uses the **last tag** as the lower bound (`git describe --tags --abbrev=0`). If no tags exist, it includes the full history and labels the section `Unreleased`.

## Requirements

- `git` on PATH
- `bash` (4+ recommended for `case` glob)
- No other dependencies

## License

MIT
