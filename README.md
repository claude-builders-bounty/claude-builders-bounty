# CHANGELOG Skill — Setup Instructions

## Quick Start (3 steps)

### Step 1: Download
```bash
curl -O https://raw.githubusercontent.com/jiangyj545/claude-builders-bounty/feat/changelog-skill/changelog.sh
chmod +x changelog.sh
```

### Step 2: Run
```bash
bash changelog.sh
```

### Step 3: Done
A `CHANGELOG.md` file is generated in your project root.

## Advanced Usage

```bash
# Generate since a specific tag
bash changelog.sh -t v1.2.0

# Generate full changelog (all tags)
bash changelog.sh --all

# Output to a different file
bash changelog.sh -o docs/CHANGES.md

# Preview without writing
bash changelog.sh --dry-run

# Run on a different repo
bash changelog.sh -r /path/to/repo
```

## Requirements

- **git** (any recent version)
- **bash** (4.0+)
- No other dependencies

## How Commits Are Categorized

| Pattern | Category | Example |
|---------|----------|---------|
| `feat: ...` | Added | `feat: add user authentication` |
| `fix: ...` | Fixed | `fix: resolve timeout issue` |
| `refactor: ...` | Changed | `refactor: simplify query logic` |
| `chore: remove ...` | Removed | `chore: remove deprecated API` |
| Keywords: add/create/new | Added | `add login button` |
| Keywords: fix/resolve/patch | Fixed | `fix crash on startup` |
| Keywords: update/improve | Changed | `update dependencies` |
| Keywords: remove/delete | Removed | `delete unused files` |

## Sample Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## v2.1.0 (2026-05-20)

### Added
- User authentication with OAuth2 ([a1b2c3d](https://github.com/user/repo/commit/a1b2c3d))
- Dark mode support ([e4f5g6h](https://github.com/user/repo/commit/e4f5g6h))

### Fixed
- Resolve timeout on large file uploads ([i7j8k9l](https://github.com/user/repo/commit/i7j8k9l))

### Changed
- Improve error messages for API failures ([m0n1o2p](https://github.com/user/repo/commit/m0n1o2p))

### Removed
- Deprecated v1 API endpoints ([q3r4s5t](https://github.com/user/repo/commit/q3r4s5t))
```

## As a Claude Code Skill

Copy `SKILL.md` to your project's `.claude/skills/` directory. Then use `/generate-changelog` in Claude Code.
