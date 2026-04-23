# Changelog Generator

Automatically generate a structured `CHANGELOG.md` from your git commit history with intelligent categorization.

## Quick Start

### Option 1: Claude Code Skill

```bash
# Install the skill
cp SKILL.md ~/.claude/skills/generate-changelog.md

# Use it in any git repo
/generate-changelog
```

### Option 2: Standalone Script

```bash
# Make executable
chmod +x changelog.sh

# Run in any git repo
./changelog.sh > CHANGELOG.md
```

### Option 3: Direct Use

```bash
bash changelog.sh > CHANGELOG.md
```

## Features

✅ **Automatic Categorization** - Groups commits into Added/Changed/Fixed/Removed  
✅ **Smart Detection** - Recognizes conventional commits AND keywords  
✅ **Tag-Based** - Shows changes since last git tag  
✅ **Commit Hashes** - Includes hash for traceability  
✅ **Keep a Changelog Format** - Industry-standard format  

## How It Works

1. Finds the last git tag (or first commit if no tags)
2. Extracts all commits since that point
3. Categorizes each commit:
   - **Added**: `feat:`, `add:`, `new:` or keywords "add", "new", "feature", "implement"
   - **Fixed**: `fix:`, `bug:` or keywords "fix", "bug", "resolve", "patch"
   - **Changed**: `update:`, `refactor:` or keywords "update", "change", "improve"
   - **Removed**: `remove:`, `delete:` or keywords "remove", "delete", "deprecate"
4. Generates formatted CHANGELOG.md

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-04-23

### Added

- feat: Add user authentication (a1b2c3d)
- Implement webhook support (e4f5g6h)

### Changed

- refactor: Improve database query performance (i7j8k9l)
- Update API response format (m0n1o2p)

### Fixed

- fix: Resolve race condition in async handler (q3r4s5t)
- Bug fix for null pointer exception (u6v7w8x)

### Removed

- Remove deprecated legacy API endpoints (y9z0a1b)

---

**Summary:** 7 commits since v1.0.0

Generated on: 2026-04-23
```

## Testing

Tested on this repository:

```bash
cd /tmp/changelog-generator
git init
git add .
git commit -m "feat: Add changelog generator tool"
git commit -m "fix: Handle repositories with no tags"
git commit -m "Update README with examples"
git tag v1.0.0
git commit -m "refactor: Improve categorization logic"
bash changelog.sh > SAMPLE_CHANGELOG.md
```

See `SAMPLE_CHANGELOG.md` for real output.

## Requirements

- Git repository
- Bash shell
- Write permissions

## License

MIT
