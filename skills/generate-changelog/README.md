# Generate CHANGELOG Skill

A Claude Code skill that automatically generates a structured `CHANGELOG.md` from your project's git history.

## Features

- Generates changelog from commits since the last git tag
- Auto-categorizes into: Added, Fixed, Changed, Removed, Other
- Zero dependencies (pure bash)
- Works as both a standalone script and a Claude Code skill

## Installation (3 steps)

### Option 1: Claude Code Skill

1. Copy `changelog.sh` and `SKILL.md` to your project's `skills/` directory:
   ```bash
   mkdir -p skills && cp changelog.sh skills/ && cp SKILL.md skills/
   ```

2. Make the script executable:
   ```bash
   chmod +x skills/changelog.sh
   ```

3. Use inside Claude Code:
   ```
   /generate-changelog
   ```

### Option 2: Standalone Bash Script

1. Place `changelog.sh` in your project root
2. Make executable: `chmod +x changelog.sh`
3. Run: `./changelog.sh`

## Output Format

The generated `CHANGELOG.md` follows standard conventions:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New features

### Fixed
- Bug fixes

### Changed
- Modifications and improvements

### Removed
- Deprecated features

### Other
- Commits that don't fit the above categories
```

## Categorization Rules

The script uses conventional commit prefixes:

| Category  | Keywords                                      |
|-----------|-----------------------------------------------|
| Added     | add, feat, new, introduce, implement, support, create |
| Fixed     | fix, bug, hotfix, patch, correct, resolve, repair |
| Changed   | change, update, refactor, improve, modify, enhance, adjust, optimize, upgrade |
| Removed   | remove, delete, drop, discard, eliminate, deprecate |
| Other     | commits that don't match any above (including docs, tests, chores, releases) |

## Customization

Edit the `TAG_PATTERN` variable in `changelog.sh` if your release tags follow a different pattern (default: `v*`).

To include only commits since a specific tag:

```bash
git tag -l  # list all tags
# The script automatically detects the latest tag
```

## Testing

The bounty submission includes test output from a real repository with 154 commits. Sample output is available in the PR.

## Requirements

- Bash 4.0+
- Git
- A standard git repository with commit history

## License

MIT
