# generate-changelog

A bash script and Claude Code skill that generates a structured `CHANGELOG.md`
from your git history — no dependencies, no config files.

## Setup

1. Copy `changelog.sh` and `SKILL.md` to your project root.
2. Make the script executable: `chmod +x changelog.sh`
3. Run it: `bash changelog.sh`

That's it. Works on macOS, Linux, and Windows (Git Bash / WSL).

## Usage

```bash
# Generate CHANGELOG.md from commits since the last tag
bash changelog.sh

# Write to a custom file
bash changelog.sh docs/CHANGELOG.md

# Specify an explicit range
bash changelog.sh CHANGELOG.md --from v1.0.0 --to v2.0.0
```

Inside **Claude Code**, use the slash command:

```
/generate-changelog
```

## Output format

```markdown
# Changelog

## [Unreleased] — 2026-07-20

> Changes since `v0.1.0`

### Added
- feat: implement /users endpoint with pagination (`c85cc77`)

### Fixed
- fix: correct SQL injection vulnerability in search (`20757e9`)

### Changed
- perf: optimise database query for user lookup (`48d7ed8`)
- chore: bump dependency versions (`a4c766a`)

### Removed
- remove: deprecated v1 API endpoints (`a5fc48a`)
```

## How it categorises commits

Commits are matched by conventional-commit prefix or keyword — first match wins:

| Category | Detected keywords |
|----------|--------------------|
| **Added** | `feat`, `add`, `implement`, `new feature` |
| **Fixed** | `fix`, `bug`, `patch`, `hotfix`, `resolve`, `repair` |
| **Removed** | `remove`, `drop`, `delete`, `deprecat` |
| **Changed** | `refactor`, `chore`, `style`, `perf`, `ci`, `build`, `docs`, `test`, `update`, `change`, `improve`, `bump`, `rename` |
| **Other** | anything else |

## Requirements

- `bash` 3+ (the default on macOS works)
- `git` in PATH
- A git repository with at least one commit
