---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git commit history. Use when the user asks to generate a changelog, update release notes, or document recent changes.
---

# Generate Changelog Skill

Generate a structured `CHANGELOG.md` from the project's git history.

## Trigger

When the user says any of:
- "generate changelog"
- "update changelog"  
- "create release notes"
- "what's changed since last release"
- `/generate-changelog`

## Workflow

### Step 1: Determine version range

Run the following to find the latest git tag and collect commits since:

```bash
# Get latest tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# If no tags exist, use all commits
if [ -z "$LATEST_TAG" ]; then
  RANGE="HEAD"
  VERSION="Unreleased"
else
  RANGE="${LATEST_TAG}..HEAD"
  VERSION="Unreleased (since ${LATEST_TAG})"
fi

# Get commits in range
COMMITS=$(git log --oneline --no-merges $RANGE 2>/dev/null)
```

### Step 2: Categorize commits

Categorize each commit into one of four sections by scanning the commit message prefix:

| Prefix Pattern | Category |
|---------------|----------|
| `feat:` `add:` `added:` `new:` | **Added** |
| `fix:` `bug:` `patch:` `hotfix:` `resolve:` | **Fixed** |
| `change:` `update:` `refactor:` `perf:` `style:` `improve:` `tweak:` | **Changed** |
| `remove:` `delete:` `drop:` `deprecate:` `revert:` | **Removed** |

Unrecognized commits go under **Changed** with a `[misc]` tag.

### Step 3: Generate CHANGELOG.md

Write `CHANGELOG.md` to the project root using this template:

```markdown
# Changelog

## {{VERSION}} — {{DATE}}

### Added
{{list of "Added" commits, one per line: "- commit message (hash)"}}
{{or "_None_" if empty}}

### Fixed
{{list of "Fixed" commits, one per line: "- commit message (hash)"}}
{{or "_None_" if empty}}

### Changed
{{list of "Changed" commits, one per line: "- commit message (hash)"}}
{{or "_None_" if empty}}

### Removed
{{list of "Removed" commits, one per line: "- commit message (hash)"}}
{{or "_None_" if empty}}
```

### Step 4: Report

After generating, tell the user:
- How many commits were included
- The version range
- The output file path
- A preview of the first 5 entries

## Edge Cases

- **No commits since last tag**: Write "No changes since {{LATEST_TAG}}" and exit cleanly
- **No tags exist**: Use "Unreleased" as the version header
- **Existing CHANGELOG.md**: Prepend the new entry above existing content (don't overwrite)
- **Merge commits**: Always skip merge commits (`--no-merges`)
- **Empty repository**: Exit with a helpful message: "No commits found. Make your first commit first!"
