# Generate Changelog

Generates a structured CHANGELOG.md from a project's git history.

## Usage

Run this skill by executing:

```bash
bash changelog.sh
```

Or use the `/generate-changelog` command in Claude Code.

## What it does

1. Fetches all commits since the last git tag
2. Categorizes commits into: Added, Fixed, Changed, Removed
3. Generates a properly formatted CHANGELOG.md
4. Supports conventional commit prefixes (feat:, fix:, chore:, etc.)

## Output

Creates `CHANGELOG.md` in the project root with sections:

- **Added** — new features (feat: commits)
- **Fixed** — bug fixes (fix: commits)
- **Changed** — updates (update:, change:, refactor:, style: commits)
- **Removed** — removed features (remove:, delete: commits)

## Requirements

- Git must be installed
- Must be run inside a git repository
- Works best with conventional commits

## Example

```bash
cd your-project
bash changelog.sh
# CHANGELOG.md is generated
```
