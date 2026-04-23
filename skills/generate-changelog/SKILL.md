---
name: generate-changelog
description: Generate structured CHANGELOG.md from git history with automatic categorization
---

# Generate Changelog

Automatically generates a `CHANGELOG.md` file from your git commit history, categorizing commits into Added, Changed, Fixed, and Removed sections.

## How to Use

Run this command in any git repository:

```
/generate-changelog
```

The skill will:
1. Find the last git tag (or use first commit if no tags exist)
2. Extract all commits since that tag
3. Automatically categorize commits based on conventional commit prefixes and keywords
4. Generate a properly formatted CHANGELOG.md file

## Categorization Rules

- **Added**: Commits with `feat:`, `add:`, `new:` or containing keywords like "add", "new", "feature", "implement"
- **Fixed**: Commits with `fix:`, `bugfix:`, `bug:` or containing keywords like "fix", "bug", "resolve", "patch"
- **Changed**: Commits with `change:`, `update:`, `refactor:`, `improve:`, `chore:` or containing keywords like "update", "change", "refactor", "improve", "modify"
- **Removed**: Commits with `remove:`, `delete:`, `deprecate:` or containing keywords like "remove", "delete", "deprecate"
- **Other**: Any commits that don't match the above patterns

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-04-23

### Added

- feat: Add user authentication (a1b2c3d)
- Add webhook support for notifications (e4f5g6h)

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

## Implementation

The skill runs the following bash script:

```bash
#!/bin/bash
set -e

# Get the last git tag (or first commit if no tags)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

# Get current date
CURRENT_DATE=$(date +%Y-%m-%d)

# Get commits since last tag
COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%h|%s" --reverse)

# Initialize category arrays
declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()
declare -a other=()

# Categorize commits
while IFS='|' read -r hash message; do
    lower_message=$(echo "$message" | tr '[:upper:]' '[:lower:]')

    # Match conventional commit prefixes
    if [[ "$lower_message" =~ ^(feat|add|new): ]]; then
        added+=("- $message ($hash)")
    elif [[ "$lower_message" =~ ^(fix|bugfix|bug): ]]; then
        fixed+=("- $message ($hash)")
    elif [[ "$lower_message" =~ ^(change|update|refactor|improve|chore): ]]; then
        changed+=("- $message ($hash)")
    elif [[ "$lower_message" =~ ^(remove|delete|deprecate): ]]; then
        removed+=("- $message ($hash)")
    else
        # Keyword-based fallback
        if [[ "$lower_message" =~ (add|new|feature|implement) ]]; then
            added+=("- $message ($hash)")
        elif [[ "$lower_message" =~ (fix|bug|resolve|patch) ]]; then
            fixed+=("- $message ($hash)")
        elif [[ "$lower_message" =~ (update|change|refactor|improve|modify) ]]; then
            changed+=("- $message ($hash)")
        elif [[ "$lower_message" =~ (remove|delete|deprecate) ]]; then
            removed+=("- $message ($hash)")
        else
            other+=("- $message ($hash)")
        fi
    fi
done <<< "$COMMITS"

# Generate CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [Unreleased] - $CURRENT_DATE"
    echo ""

    [ ${#added[@]} -gt 0 ] && {
        echo "### Added"
        echo ""
        printf '%s\n' "${added[@]}"
        echo ""
    }

    [ ${#changed[@]} -gt 0 ] && {
        echo "### Changed"
        echo ""
        printf '%s\n' "${changed[@]}"
        echo ""
    }

    [ ${#fixed[@]} -gt 0 ] && {
        echo "### Fixed"
        echo ""
        printf '%s\n' "${fixed[@]}"
        echo ""
    }

    [ ${#removed[@]} -gt 0 ] && {
        echo "### Removed"
        echo ""
        printf '%s\n' "${removed[@]}"
        echo ""
    }

    [ ${#other[@]} -gt 0 ] && {
        echo "### Other"
        echo ""
        printf '%s\n' "${other[@]}"
        echo ""
    }

    total_commits=$((${#added[@]} + ${#changed[@]} + ${#fixed[@]} + ${#removed[@]} + ${#other[@]}))
    echo "---"
    echo ""
    echo "**Summary:** $total_commits commits since ${LAST_TAG}"
    echo ""
    echo "Generated on: $CURRENT_DATE"
} > CHANGELOG.md

echo "✓ CHANGELOG.md generated successfully"
echo "  Commits analyzed: $total_commits"
echo "  Since: ${LAST_TAG}"
```

## Requirements

- Git repository with commit history
- Bash shell (available on macOS, Linux, WSL)
- Write permissions in current directory

## Notes

- The script looks for the last git tag as the starting point
- If no tags exist, it uses the first commit in the repository
- Supports both conventional commit format and keyword-based detection
- Output follows the Keep a Changelog format
- Each entry includes the commit hash for traceability
