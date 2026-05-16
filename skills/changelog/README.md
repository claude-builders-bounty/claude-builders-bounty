# changelog.sh — Generate CHANGELOG.md from git history

A bash script that auto-generates a structured `CHANGELOG.md` from conventional commits.

**Bounty**: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1 ($50)

## Quick Start

```bash
# In your project directory
bash changelog.sh

# Or specify a repo
bash changelog.sh --repo /path/to/project

# Custom output file
bash changelog.sh --repo /path/to/project --output CHANGES.md

# Custom header
bash changelog.sh --header "# My Project Changelog"
```

## Output

Commits are auto-categorized using Conventional Commits prefixes:

| Commit Type | Section |
|------------|---------|
| `feat:`, `feature:`, `add:` | Added |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `refactor:`, `perf:`, `chore:`, `build:`, `ci:` | Changed |
| `remove:`, `delete:` | Removed |
| `deprecate:` | Deprecated |
| `security:`, `audit:` | Security |
| `docs:`, `readme:` | Documentation |
| anything else | 其他 |

## Sample Output

See [sample-output.md](sample-output.md) for a real example.

## Requirements

- bash 4+
- git
