# Changelog Generator Skill

A Claude Code skill that automatically generates a structured CHANGELOG.md from a project's git history.

## Features

- Auto-categorizes commits into Added / Fixed / Changed / Removed
- Supports conventional commit messages (feat, fix, refactor, etc.)
- Works with or without git tags
- Outputs properly formatted CHANGELOG.md

## Setup (3 steps or fewer)

1. Copy `changelog.sh` to your project root
2. Make it executable: `chmod +x changelog.sh`
3. Run it: `bash changelog.sh`

## Usage

### Basic usage
```bash
bash changelog.sh
```

### With options
```bash
bash changelog.sh --output CUSTOM_CHANGELOG.md --since v1.0.0
```

### As a Claude Code skill
Use the `/generate-changelog` command in Claude Code.

## Commit Message Convention

The generator uses conventional commits:
- `feat: ...` → **Added**
- `fix: ...` → **Fixed**
- `refactor: ...`, `perf: ...`, `style: ...` → **Changed**
- `remove: ...`, `delete: ...` → **Removed**

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- feat: add user authentication (a1b2c3d)
- feat: implement dark mode toggle (e4f5g6h)

### Fixed
- fix: resolve login timeout issue (i7j8k9l)
- fix: correct date formatting (m0n1o2p)

### Changed
- refactor: optimize database queries (q3r4s5t)
- style: update color scheme (u6v7w8x)
```

## Requirements

- Bash 4.0+
- Git

## License

MIT
