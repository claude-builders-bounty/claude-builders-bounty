# CHANGELOG Generator — Claude Code Skill

Generate a structured `CHANGELOG.md` from your project's git history in one command.

## Setup (3 steps)

1. **Download** — Place `changelog.sh` in your project root
2. **Run** — `bash changelog.sh`
3. **Review** — Open the generated `CHANGELOG.md`

## Usage

```bash
# Basic usage (outputs to CHANGELOG.md)
bash changelog.sh

# Custom output file
bash changelog.sh HISTORY.md

# Specify repo directory
bash changelog.sh CHANGELOG.md /path/to/project
```

## How it works

- Fetches all commits since the last git tag (or since the first commit)
- Auto-categorizes into: **Added**, **Fixed**, **Changed**, **Removed**
- Supports [Conventional Commits](https://www.conventionalcommits.org/) parsing
- Outputs a clean, structured `CHANGELOG.md` file

## Sample output

```markdown
# Changelog

### Added
- 2026-08-18 Implement user authentication (abc1234)
- 2026-08-17 Add API rate limiting (def5678)

### Fixed
- 2026-08-16 Fix login redirect loop (ghi9012)

### Changed
- 2026-08-15 Upgrade dependencies to latest (jkl3456)

### Removed
- 2026-08-14 Drop deprecated v1 endpoints (mno7890)
```

## Requirements

- `git` (installed by default with most dev environments)
- Bash shell (Linux, macOS, WSL, or Git Bash on Windows)
