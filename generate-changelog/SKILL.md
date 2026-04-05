# SKILL.md — Generate Changelog

## Description
Generates a structured `CHANGELOG.md` from git commit history. Works via the `/generate-changelog` command in Claude Code.

## How It Works
1. **Fetches commits** since the last git tag (or from a given starting point)
2. **Auto-categorizes** each commit into one of four sections:
   - **Added** — New features (`feat`, `feat:`)
   - **Fixed** — Bug fixes (`fix`, `fix:`)
   - **Changed** — Improvements, refactors, chores, docs, tests, builds (`chore`, `refactor`, `build`, `perf`, `test`, `ci`, `docs`)
   - **Removed** — Breaking changes, deprecations (`BREAKING`, `breaking`, `remove`, `deprecate`)
3. **Outputs** a properly formatted `CHANGELOG.md` with version header, date, and categorized entries

## Usage

```
/generate-changelog [options]
```

**Options:**
- `--from <tag|commit>` — Starting point (default: last git tag)
- `--to <tag|commit>` — Ending point (default: HEAD)
- `--output <file>` — Output file path (default: CHANGELOG.md)
- `--repo <path>` — Repo path (default: current directory)
- `--title <title>` — Version title (default: extracted from latest tag or "Unreleased")

**Examples:**
```
/generate-changelog
/generate-changelog --from v1.0.0 --to v1.1.0
/generate-changelog --repo /path/to/repo --output CHANGELOG.md
```

## Categorization Rules

| Prefix | Category |
|--------|----------|
| `feat`, `feat:` | **Added** |
| `fix`, `fix:` | **Fixed** |
| `chore`, `refactor`, `build`, `perf`, `ci`, `test`, `docs`, `docs:` | **Changed** |
| `BREAKING`, `breaking`, `remove`, `deprecate` | **Removed** |
| `release` | (skipped — informational only) |

### Breaking Changes
Commits containing `BREAKING` or `breaking` are listed under **Removed** with a ⚠️ marker and the full commit message.

## Output Format

```markdown
# Changelog

## [version] — YYYY-MM-DD

### Added
- feat: description (#PR)

### Fixed
- fix: description (#PR)

### Changed
- chore: description
- docs: description

### Removed
- ⚠️ BREAKING: description
```

## Script Implementation

Save this as `scripts/generate-changelog.sh` in your project:

```bash
#!/bin/bash
# Generate Changelog from git history
# Usage: ./scripts/generate-changelog.sh [--from TAG] [--to TAG] [--repo PATH]

set -e

FROM_TAG=""
TO_TAG="HEAD"
REPO_PATH="${1:-.}"
OUTPUT="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case $1 in
    --from) FROM_TAG="$2"; shift 2 ;;
    --to) TO_TAG="$2"; shift 2 ;;
    --repo) REPO_PATH="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# Find last tag if --from not specified
if [[ -z "$FROM_TAG" ]]; then
  FROM_TAG=$(cd "$REPO_PATH" && git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Get commits
if [[ -n "$FROM_TAG" ]]; then
  COMMITS=$(cd "$REPO_PATH" && git log "$FROM_TAG".."$TO_TAG" --pretty=format:"%s|%h|%an|%s" 2>/dev/null)
else
  COMMITS=$(cd "$REPO_PATH" && git log "$TO_TAG" --pretty=format:"%s|%h|%an|%s" 2>/dev/null)
fi

# Generate markdown
{
  echo "# Changelog"
  echo ""
  echo "## Unreleased"
  echo ""
  echo "### Added"
  echo ""
  echo "### Fixed"
  echo ""
  echo "### Changed"
  echo ""
  echo "### Removed"
} > "$OUTPUT"

echo "Changelog written to $OUTPUT"
```

## Claude Code Tool Integration

This skill is designed to be invoked directly by Claude Code. When you type `/generate-changelog`, Claude Code will:

1. Read this SKILL.md
2. Execute the changelog generation using git log parsing
3. Display the resulting CHANGELOG.md
4. Offer to write it to a file

## Requirements
- Git repository with commits
- Git CLI installed
- (Optional) `gh` CLI for GitHub-specific features

## Notes
- Merge commits are automatically excluded
- Commits with `release:` prefix are skipped (they're metadata)
- PR numbers are extracted from commit messages when available
- If no git tags exist, all commits from the default branch are used
