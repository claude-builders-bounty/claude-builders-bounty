# Bounty #1: Generate a structured CHANGELOG from git history

**Prize:** $50  
**Status:** Reference Implementation

## Overview

A Claude Code skill that parses conventional commits from git history and generates a structured `CHANGELOG.md` grouped by version tags or date ranges.

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Claude Code skill definition — enables `/generate-changelog` |
| `generate-changelog.sh` | Bash script that does the actual parsing and generation |
| `README.md` | This file |

## Quick Start

```bash
# 1. Make the script executable
chmod +x generate-changelog.sh

# 2. Run from any git repo with conventional commits
./generate-changelog.sh

# 3. Or use options
./generate-changelog.sh --from v1.0.0 --to v2.0.0 --output docs/CHANGELOG.md --group-by scope
```

## In Claude Code

Place `SKILL.md` in your project root. Then run:

```
/generate-changelog
/generate-changelog --from v1.0.0 --to HEAD --group-by scope
```

## Conventional Commit Format

```
<type>(<scope>): <description>

feat: add user login
fix(auth): handle token expiry
feat(api)!: drop v1 endpoints
docs(readme): update installation
```

## Output Example

```markdown
# Changelog

## [v1.2.0] - 2025-06-15

### ✨ Features

- Add user login ([abc1234])
- Add dark mode ([def5678])

### 🐛 Bug Fixes

- Fix token refresh ([ghi9012])

## [v1.1.0] - 2025-05-01

### 📝 Documentation

- Update API docs ([jkl3456])
```

## Edge Cases Handled

- **No tags**: Treats entire history as one "Unreleased" version
- **Empty commits**: Skipped via `--no-merges` and regex filtering
- **Merge commits**: Excluded via `--no-merges`
- **Non-conventional commits**: Silently filtered out
- **Existing CHANGELOG.md**: New entries prepended, old header replaced
- **No commits in range**: Produces empty output gracefully
- **Breaking changes**: Marked with `**BREAKING:**` prefix
