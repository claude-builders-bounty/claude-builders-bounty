# Generate Changelog

Generate a structured `CHANGELOG.md` from git history, auto-categorizing commits into **Added**, **Fixed**, **Changed**, and **Removed** sections.

## Setup (3 steps)

1. **Clone or copy** `changelog.sh` into your repository root
2. **Make it executable**: `chmod +x changelog.sh`
3. **Run it**: `bash changelog.sh`

That's it! Your `CHANGELOG.md` will be generated in the current directory.

## Usage

```bash
# Default: writes to CHANGELOG.md
bash changelog.sh

# Custom output file
bash changelog.sh docs/RELEASE_NOTES.md
```

## How commits are categorized

| Prefix | Category |
|--------|----------|
| `feat:`, `add:`, `new:`, `feature:` | Added |
| `fix:`, `bugfix:`, `hotfix:`, `patch:` | Fixed |
| `refactor:`, `update:`, `chore:`, `improve:`, `docs:`, `test:`, `ci:`, `build:`, `style:`, `perf:` | Changed |
| `remove:`, `delete:`, `drop:` | Removed |
| Anything else | Other |

## Requirements

- `git` (any modern version)
- `bash` 4+
- Repository with at least one commit

## Claude Code Integration

Add to `.claude/commands/generate-changelog.md`:

```markdown
---
description: Generate CHANGELOG.md from git history
---
!bash changelog.sh
```

Then run `/generate-changelog` in Claude Code.

## Sample output

See `CHANGELOG.md` in this repository for an example generated from this repo's own commit history.
