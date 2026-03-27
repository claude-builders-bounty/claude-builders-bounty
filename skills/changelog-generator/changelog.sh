#!/usr/bin/env bash
# =============================================================================
# Generate CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag|commit>] [--output <file>]
# =============================================================================
set -euo pipefail

SINCE="${CHANGELOG_SINCE:-$(git describe --tags --abbrev=0 2>/dev/null || echo "")}"
OUTPUT="${CHANGELOG_OUTPUT:-CHANGELOG.md}"
UNRELEASED="${CHANGELOG_UNRELEASED:-true}"

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --since) SINCE="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Get commits
if [[ -n "$SINCE" ]]; then
    commits=$(git log "$SINCE"..HEAD --format="%s" 2>/dev/null || echo "")
else
    commits=$(git log --format="%s" 2>/dev/null || echo "")
fi

# Categorize
added=(); fixed=(); changed=(); removed=(); deprecated=(); breaking=()

while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$lower" == *"breaking"* ]]; then
        breaking+=("$line")
    elif [[ "$lower" == "feat:"* || "$lower" == "feat("* ]]; then
        added+=("$line")
    elif [[ "$lower" == "fix:"* || "$lower" == "fix("* ]]; then
        fixed+=("$line")
    elif [[ "$lower" == "deprecate"* ]]; then
        deprecated+=("$line")
    elif [[ "$lower" == "remove:"* || "$lower" == "delete:"* || "$lower" == *"removed"* ]]; then
        removed+=("$line")
    else
        changed+=("$line")
    fi
done <<< "$commits"

# Generate markdown
{
    echo "# Changelog"
    echo ""
    
    if [[ "${#unreleased[@]}" -gt 0 && "$UNRELEASED" == "true" && -n "$(git log --format=%s 2>/dev/null)" ]]; then
        echo "## [Unreleased]"
        echo ""
    fi
    
    if [[ ${#added[@]} -gt 0 ]]; then
        echo "### Added"
        echo ""
        for c in "${added[@]}"; do echo "- ${c#feat: }"; done
        echo ""
    fi
    
    if [[ ${#fixed[@]} -gt 0 ]]; then
        echo "### Fixed"
        echo ""
        for c in "${fixed[@]}"; do echo "- ${c#fix: }"; done
        echo ""
    fi
    
    if [[ ${#changed[@]} -gt 0 ]]; then
        echo "### Changed"
        echo ""
        for c in "${changed[@]}"; do echo "- ${c#*:}"; done
        echo ""
    fi
    
    if [[ ${#removed[@]} -gt 0 ]]; then
        echo "### Removed"
        echo ""
        for c in "${removed[@]}"; do echo "- ${c#remove: }"; done
        echo ""
    fi
    
    if [[ ${#deprecated[@]} -gt 0 ]]; then
        echo "### Deprecated"
        echo ""
        for c in "${deprecated[@]}"; do echo "- ${c#deprecate: }"; done
        echo ""
    fi
    
    if [[ ${#breaking[@]} -gt 0 ]]; then
        echo "### Breaking Changes"
        echo ""
        for c in "${breaking[@]}"; do echo "- ${c}"; done
        echo ""
    fi

} > "$OUTPUT"

echo "Changelog written to $OUTPUT ($(wc -l < "$OUTPUT") lines)"
