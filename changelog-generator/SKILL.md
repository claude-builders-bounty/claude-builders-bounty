---
name: generate-changelog
description: "Generate a structured CHANGELOG.md from git history, auto-categorizing commits into Added/Fixed/Changed/Removed sections."
tags: ["git", "changelog", "release", "documentation"]
---

# Generate Changelog

Generate a structured `CHANGELOG.md` from your project's git history. Commits are auto-categorized by their conventional commit prefix.

## Usage

### As a Claude Code Skill

```
/generate-changelog
```

### As a Bash Script

```bash
bash changelog.sh              # Output to CHANGELOG.md
bash changelog.sh RELEASE.md   # Output to custom file
```

## How It Works

1. Finds the latest git tag (or uses full history if no tags exist)
2. Extracts all commits since that tag
3. Categorizes each commit by its prefix:

| Prefix Pattern | Category |
|---|---|
| `feat`, `add`, `new`, `create`, `implement`, `introduce` | **Added** |
| `fix`, `bugfix`, `patch`, `resolve`, `correct` | **Fixed** |
| `refactor`, `change`, `update`, `modify`, `improve`, `perf`, `optimize`, `style`, `chore`, `build`, `ci`, `docs`, `test` | **Changed** |
| `remove`, `delete`, `deprecate`, `drop`, `eliminate` | **Removed** |

4. Outputs a formatted Markdown changelog

## Example Output

```markdown
# Changelog

## [Unreleased] — since v1.0.0

_Generated on 2026-05-21_

### Added
- feat: add user authentication (`a1b2c3d`) — Alice (2026-05-20)
- implement dark mode toggle (`e4f5g6h`) — Bob (2026-05-19)

### Fixed
- fix: resolve login timeout issue (`i7j8k9l`) — Alice (2026-05-20)

### Changed
- docs: update API reference (`m0n1o2p`) — Charlie (2026-05-18)
- refactor: simplify auth middleware (`q3r4s5t`) — Alice (2026-05-17)

### Removed
- remove deprecated v1 endpoints (`u6v7w8x`) — Bob (2026-05-16)
```

## Setup (3 steps)

1. Copy `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `bash changelog.sh`

## Requirements

- Git repository with at least one commit
- Bash 4.0+
- No external dependencies (uses only `git`, `grep`, `sed`)

## Tips

- Use [Conventional Commits](https://www.conventionalcommits.org/) for best categorization results
- Create a git tag before generating: `git tag v1.0.0`
- Add to your release workflow: `bash changelog.sh && git add CHANGELOG.md`
