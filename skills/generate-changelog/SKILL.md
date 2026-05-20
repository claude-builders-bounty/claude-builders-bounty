---
name: generate-changelog
description: Generate a structured CHANGELOG.md from git history
---

# Generate CHANGELOG Skill

## Instructions

You are a changelog generation assistant. When the user runs `/generate-changelog`, follow these steps:

### Step 1: Detect Git Repository
```bash
# Check if we're in a git repository
git rev-parse --is-inside-work-tree
```

If not in a git repository, inform the user and exit.

### Step 2: Fetch Commits Since Last Tag

```bash
# Get the latest tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LATEST_TAG" ]; then
    # Get commits since the latest tag
    COMMITS=$(git log $LATEST_TAG..HEAD --pretty=format:"%s" --no-merges)
else
    # No tags exist, get all commits
    COMMITS=$(git log --pretty=format:"%s" --no-merges)
fi
```

### Step 3: Categorize Commits

Parse each commit message and categorize based on conventional commit prefixes or keywords:

**Categories:**
- **Added**: `feat:`, `feature:`, `add:`, `new:`, `+`
- **Fixed**: `fix:`, `bugfix:`, `bug:`, `hotfix:`
- **Changed**: `change:`, `update:`, `refactor:`, `improve:`, `modify:`
- **Removed**: `remove:`, `delete:`, `deprecate:`, `-`

### Step 4: Generate CHANGELOG.md

Create a `CHANGELOG.md` file with the following structure:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- [commit message 1]
- [commit message 2]

### Fixed
- [commit message 3]

### Changed
- [commit message 4]

### Removed
- [commit message 5]
```

### Step 5: Preserve Existing CHANGELOG

If a `CHANGELOG.md` already exists:
1. Read the existing content
2. Prepend the new entries to the `[Unreleased]` section
3. Keep all existing version sections intact

## Bash Alternative Script

If the user prefers a bash script, create `changelog.sh`:

```bash
#!/bin/bash

# CHANGELOG Generator
# Usage: ./changelog.sh [output_file]

OUTPUT_FILE="${1:-CHANGELOG.md}"

# Check if in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "Error: Not a git repository"
    exit 1
fi

# Get the latest tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

# Get commits
if [ -n "$LATEST_TAG" ]; then
    COMMITS=$(git log "$LATEST_TAG"..HEAD --pretty=format:"%s" --no-merges)
    VERSION="Unreleased (since $LATEST_TAG)"
else
    COMMITS=$(git log --pretty=format:"%s" --no-merges -100)
    VERSION="Unreleased"
fi

# Initialize categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

# Categorize commits
while IFS= read -r commit; do
    lower=$(echo "$commit" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$lower" =~ ^(feat|feature|add|new)(\(.+\))?: ]] || [[ "$lower" =~ ^\[?\+ ]]; then
        ADDED+="- $commit\n"
    elif [[ "$lower" =~ ^(fix|bugfix|bug|hotfix)(\(.+\))?: ]]; then
        FIXED+="- $commit\n"
    elif [[ "$lower" =~ ^(change|update|refactor|improve|modify|perf)(\(.+\))?: ]]; then
        CHANGED+="- $commit\n"
    elif [[ "$lower" =~ ^(remove|delete|deprecate)(\(.+\))?: ]] || [[ "$lower" =~ ^\[?\- ]]; then
        REMOVED+="- $commit\n"
    else
        # Default to Changed for unrecognized commits
        CHANGED+="- $commit\n"
    fi
done <<< "$COMMITS"

# Generate CHANGELOG content
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [$VERSION]"
    echo ""
    
    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo -e "$ADDED"
    fi
    
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo -e "$FIXED"
    fi
    
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo -e "$CHANGED"
    fi
    
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo -e "$REMOVED"
    fi
} > "$OUTPUT_FILE"

echo "✓ Generated $OUTPUT_FILE"
```

## Make the script executable:
```bash
chmod +x changelog.sh
./changelog.sh
```

## Example Run

After running `/generate-changelog` or `./changelog.sh`:

```
✓ Generated CHANGELOG.md

Preview:
--------
# Changelog

## [Unreleased]

### Added
- feat: Add changelog generation skill
- new: Support for conventional commits

### Fixed
- fix: Correct date formatting in logs

### Changed
- update: Improve git log parsing performance

### Removed
- remove: Deprecated API endpoints
```

---

Execute this skill when the user runs `/generate-changelog`.