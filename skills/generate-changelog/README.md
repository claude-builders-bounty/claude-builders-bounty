# Generate Changelog

A Claude Code skill and bash script that generates a structured `CHANGELOG.md` from git history.

## Setup (3 Steps)

1. **Copy the `skills/generate-changelog/` folder** into your project
2. **Make the script executable**: `chmod +x skills/generate-changelog/changelog.sh`
3. **Run it**: `bash skills/generate-changelog/changelog.sh`

That's it. The script auto-detects your last git tag and categorizes commits.

## Usage

### Bash

```bash
# Default: writes CHANGELOG.md to current directory
bash skills/generate-changelog/changelog.sh

# Custom output path
bash skills/generate-changelog/changelog.sh --output docs/CHANGELOG.md
```

### Claude Code

Place `SKILL.md` in your `.claude/skills/` directory, then invoke `/generate-changelog` in Claude Code.

## How It Works

- Finds the latest git tag (or uses all commits if no tags exist)
- Scans commits with `git log --no-merges`
- Categorizes by prefix into **Added** / **Fixed** / **Changed** / **Removed**
- Unrecognized prefixes default to **Changed**
- Outputs a markdown file with commit hashes for traceability

## Supported Commit Prefixes

| Prefix | Category |
|--------|----------|
| `add:`, `feat:`, `new:`, `feature:` | Added |
| `fix:`, `bug:`, `bugfix:` | Fixed |
| `remove:`, `delete:`, `drop:` | Removed |
| `change:`, `update:`, `refactor:`, `chore:`, `ci:`, `build:`, `style:`, `perf:` | Changed |
| _(none)_ | Changed (default) |

## Requirements

- Git repository with commit history
- Bash 4+
