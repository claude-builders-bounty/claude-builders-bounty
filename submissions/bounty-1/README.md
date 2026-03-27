# CHANGELOG Generator

Generate a structured `CHANGELOG.md` from git commit history — as a bash script and Claude Code skill.

## Setup (3 steps)

1. Copy `changelog.sh` to your project root (or anywhere on `$PATH`)
2. `chmod +x changelog.sh`
3. Run: `bash changelog.sh`

## Usage

```bash
# Generate from last git tag to HEAD (default)
bash changelog.sh

# From a specific tag
bash changelog.sh -t v1.2.0

# Custom output file
bash changelog.sh -o RELEASE_NOTES.md

# All options
bash changelog.sh --tag v1.0.0 --output CHANGES.md --title "Release Notes" --date 2026-03-27
```

## As a Claude Code Skill

Copy `SKILL.md` to your `.claude/skills/` directory. Then invoke via `/generate-changelog` in Claude Code.

## How It Works

Parses [Conventional Commits](https://www.conventionalcommits.org/) prefixes:

| Prefix | Section |
|--------|---------|
| `feat:` | Added |
| `fix:` | Fixed |
| `refactor:`, `perf:`, `docs:`, `chore:`, `style:`, `test:`, `build:`, `ci:` | Changed |
| `revert:`, `remove:`, `delete:` | Removed |
| `breaking:` or `BREAKING` keyword | ⚠️ Breaking Changes |
| Everything else | Other |

### Features

- ✅ Auto-detects latest tag — no config needed
- ✅ Supports scoped commits: `feat(auth):`
- ✅ Detects breaking changes by prefix or keyword
- ✅ CLI flags for customization
- ✅ Handles repos with no tags gracefully
- ✅ Non-conventional commits grouped in "Other"

## Sample Output

```markdown
# Changelog

## [Unreleased] since v1.0.0 — 2026-03-27

### Added
- user authentication with JWT tokens
- dark mode toggle

### Fixed
- crash when config file missing

### Changed
- extract validation to utils module

### Other
- initial commit
```

## Requirements

- `git` (tested on 2.30+)
- `bash` 4+
- Works on Linux, macOS, and WSL
