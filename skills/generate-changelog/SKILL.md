# Generate Structured CHANGELOG

## Description
Generate a structured CHANGELOG.md from the current project's git history. Automatically categorizes commits into Added, Fixed, Changed, and Removed sections based on conventional commit prefixes and keyword analysis.

## Instructions

When the user asks to generate a changelog (e.g., `/generate-changelog`), follow these steps:

### Step 1: Determine the range
```bash
# Check for the last git tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
echo "Last tag: ${LAST_TAG:-'none found'}"
```

### Step 2: Fetch commits
```bash
# If a tag exists, get commits since that tag; otherwise get all commits
if [ -n "$LAST_TAG" ]; then
    git log "${LAST_TAG}..HEAD" --pretty=format:"%H|||%s|||%an|||%as" --no-merges
else
    git log --pretty=format:"%H|||%s|||%an|||%as" --no-merges
fi
```

### Step 3: Categorize each commit
Use these rules to categorize:

**Added** — commits matching:
- Prefixes: `feat:`, `add:`, `new:`, `implement`, `create`, `introduce`
- Keywords: add, new, create, implement, introduce, support

**Fixed** — commits matching:
- Prefixes: `fix:`, `bugfix`, `hotfix`, `patch:`, `resolve`
- Keywords: fix, bug, resolve, repair, patch, correct

**Changed** — commits matching:
- Prefixes: `refactor:`, `update:`, `improve:`, `chore:`, `build:`, `ci:`, `docs:`, `test:`, `style:`, `perf:`
- Keywords: update, modify, improve, enhance, optimize, rename, move, migrate, upgrade, bump

**Removed** — commits matching:
- Prefixes: `remove`, `delete`, `deprecate`, `drop`
- Keywords: remove, delete, deprecate, drop, strip

### Step 4: Generate CHANGELOG.md
Write the output following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — YYYY-MM-DD

### Added
- Commit message (`short_hash`) — *Author*

### Fixed
- Commit message (`short_hash`) — *Author*

### Changed
- Commit message (`short_hash`) — *Author*

### Removed
- Commit message (`short_hash`) — *Author*
```

### Step 5: Report summary
After generating, tell the user:
- Total commits processed
- Count per category (Added/Fixed/Changed/Removed)
- File location

## Alternatively
You can run the bash script directly:
```bash
bash skills/generate-changelog/changelog.sh
```

Options:
- `--all` — Generate from entire git history
- `--since TAG` — Generate from a specific tag
- `--output FILE` — Write to custom file (default: CHANGELOG.md)
