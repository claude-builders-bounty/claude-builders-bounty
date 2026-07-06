#!/bin/bash
# CHANGELOG Generator — Claude Code / Hermes Skill
# Usage: ./changelog.sh [from_tag] [to_tag]
#        ./changelog.sh --since v1.0.0
#        ./changelog.sh --help

set -euo pipefail

VERSION="1.0.0"
CHANGELOG_FILE="CHANGELOG.md"

show_help() {
    cat <<'HELP'
Usage: changelog.sh [options]
Generate a structured CHANGELOG.md from conventional commit messages.

Options:
  --since <ref>      Generate changelog from this git ref (tag/branch/commit)
  --to <ref>         Generate changelog up to this git ref (default: HEAD)
  --output <file>    Output file (default: CHANGELOG.md)
  --tag-pattern <p>  Semver tag pattern (default: "v*")
  --help             Show this help

Examples:
  ./changelog.sh
  ./changelog.sh --since v1.0.0
  ./changelog.sh --since v1.0.0 --to v2.0.0 --output CHANGES-v2.md
HELP
    exit 0
}

# Parse arguments
SINCE=""
TO="HEAD"
TAG_PATTERN="v*"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --since) SINCE="$2"; shift 2 ;;
        --to) TO="$2"; shift 2 ;;
        --output) CHANGELOG_FILE="$2"; shift 2 ;;
        --tag-pattern) TAG_PATTERN="$2"; shift 2 ;;
        --help) show_help ;;
        *) echo "Unknown option: $1"; show_help ;;
    esac
done

# Ensure we're in a git repo
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Detect if there are tags
HAS_TAGS=false
if git tag -l "$TAG_PATTERN" | grep -q .; then
    HAS_TAGS=true
fi

generate_changelog() {
    local since_ref="$1"
    local to_ref="$2"
    local file="$3"
    local version_name="$4"

    echo "## [$version_name]" > "$file"
    echo "" >> "$file"

    # Feature commits
    features=$(git log "$since_ref..$to_ref" --oneline --grep="^feat" 2>/dev/null || true)
    # Fix commits
    fixes=$(git log "$since_ref..$to_ref" --oneline --grep="^fix" 2>/dev/null || true)
    # Breaking changes
    breaking=$(git log "$since_ref..$to_ref" --oneline --grep="BREAKING" 2>/dev/null || true)
    # All conventional commits for categorization
    all_commits=$(git log "$since_ref..$to_ref" --oneline --no-decorate 2>/dev/null || true)

    if [ -z "$all_commits" ]; then
        echo "No commits found in range." >> "$file"
        return
    fi

    # Breaking changes first
    if [ -n "$breaking" ]; then
        echo "### ⚠ Breaking Changes" >> "$file"
        echo "$breaking" | while read -r line; do
            echo "- $line" >> "$file"
        done
        echo "" >> "$file"
    fi

    # Features
    if [ -n "$features" ]; then
        echo "### ✨ Features" >> "$file"
        echo "$features" | while read -r line; do
            echo "- $line" >> "$file"
        done
        echo "" >> "$file"
    fi

    # Bug Fixes
    if [ -n "$fixes" ]; then
        echo "### 🐛 Bug Fixes" >> "$file"
        echo "$fixes" | while read -r line; do
            echo "- $line" >> "$file"
        done
        echo "" >> "$file"
    fi

    # Other categorized
    for category in "docs" "refactor" "perf" "test" "chore" "style"; do
        label=""
        case "$category" in
            docs) label="📚 Documentation" ;;
            refactor) label="♻️ Refactoring" ;;
            perf) label="⚡ Performance" ;;
            test) label="🧪 Tests" ;;
            chore) label="🔧 Maintenance" ;;
            style) label="💄 Style" ;;
        esac
        commits=$(git log "$since_ref..$to_ref" --oneline --grep="^$category" 2>/dev/null || true)
        if [ -n "$commits" ]; then
            echo "### $label" >> "$file"
            echo "$commits" | while read -r line; do
                echo "- $line" >> "$file"
            done
            echo "" >> "$file"
        fi
    done

    # Uncategorized
    categorized=$(git log "$since_ref..$to_ref" --oneline --grep="^(feat|fix|docs|refactor|perf|test|chore|style|BREAKING)" 2>/dev/null || true)
    uncategorized=$(git log "$since_ref..$to_ref" --oneline --no-decorate 2>/dev/null | grep -v "^(feat|fix|docs|refactor|perf|test|chore|style)" || true)
    if [ -n "$uncategorized" ] && [ "$(echo "$uncategorized" | wc -l)" -gt 0 ]; then
        echo "### 📝 Other Changes" >> "$file"
        echo "$uncategorized" | while read -r line; do
            echo "- $line" >> "$file"
        done
        echo "" >> "$file"
    fi
}

# Main logic
if [ -n "$SINCE" ]; then
    # Generate for a specific range
    generate_changelog "$SINCE" "$TO" "$CHANGELOG_FILE" "$(git describe --tags "$TO" 2>/dev/null || echo "$TO")"
    echo "✅ CHANGELOG generated: $CHANGELOG_FILE ($SINCE..$TO)"
elif [ "$HAS_TAGS" = true ]; then
    # Generate per-tag changelog
    tags=$(git tag -l "$TAG_PATTERN" --sort=-v:refname 2>/dev/null | head -10)
    prev=""
    first_tag=""
    
    # Build full CHANGELOG
    echo "# Changelog" > "$CHANGELOG_FILE"
    echo "" >> "$CHANGELOG_FILE"
    
    for tag in $tags; do
        if [ -z "$first_tag" ]; then
            first_tag="$tag"
            # First tag - show all commits before it
            echo "## [$tag]" >> "$CHANGELOG_FILE"
            echo "" >> "$CHANGELOG_FILE"
            git log "$tag" --oneline --no-decorate 2>/dev/null | head -50 | while read -r line; do
                echo "- $line" >> "$CHANGELOG_FILE"
            done
            echo "" >> "$CHANGELOG_FILE"
            prev="$tag"
        else
            echo "## [$tag]" >> "$CHANGELOG_FILE"
            echo "" >> "$CHANGELOG_FILE"
            generate_changelog_inline "$tag" "$prev" "$CHANGELOG_FILE" append
            prev="$tag"
        fi
    done
    
    # Unreleased
    if [ -n "$first_tag" ]; then
        unreleased=$(git log "$first_tag..HEAD" --oneline --no-decorate 2>/dev/null || true)
        if [ -n "$unreleased" ]; then
            echo "## [Unreleased]" >> "$CHANGELOG_FILE"
            echo "" >> "$CHANGELOG_FILE"
            echo "$unreleased" | while read -r line; do
                echo "- $line" >> "$CHANGELOG_FILE"
            done
            echo "" >> "$CHANGELOG_FILE"
        fi
    fi
    
    echo "✅ CHANGELOG generated: $CHANGELOG_FILE (based on $TAG_PATTERN tags)"
else
    # No tags - generate single section from all commits
    echo "# Changelog" > "$CHANGELOG_FILE"
    echo "" >> "$CHANGELOG_FILE"
    
    # Get last 100 commits
    commits=$(git log HEAD~100..HEAD --oneline --no-decorate 2>/dev/null || git log --oneline -100 2>/dev/null || echo "")
    if [ -z "$commits" ]; then
        echo "No commits found." >> "$CHANGELOG_FILE"
    else
        echo "## [Current]" >> "$CHANGELOG_FILE"
        echo "" >> "$CHANGELOG_FILE"
        echo "$commits" | while read -r line; do
            echo "- $line" >> "$CHANGELOG_FILE"
        done
    fi
    
    echo "✅ CHANGELOG generated: $CHANGELOG_FILE (no tags found — full log)"
fi

echo ""
echo "📊 Stats:"
if [ -f "$CHANGELOG_FILE" ]; then
    lines=$(wc -l < "$CHANGELOG_FILE")
    echo "  Lines: $lines"
    echo "  Sections: $(grep -c '^##' "$CHANGELOG_FILE" || true)"
fi
