#!/usr/bin/env bash
# ==============================================================================
# changelog.sh - Production Git Changelog Generator
# Generates structured, Keep-a-Changelog compliant CHANGELOG.md entries from git history.
# Works via direct CLI or Claude Code slash command: /generate-changelog
# ==============================================================================

set -euo pipefail
shopt -s nocasematch

VERSION="Unreleased"
TARGET_FILE=""
WRITE_FILE=false
SINCE_REF=""
UNTIL_REF="HEAD"
INCLUDE_ALL=false
REPO_PATH="."

usage() {
    cat << 'EOF'
Usage: changelog.sh [options]

Options:
  -v, --version <name>    Version header (default: "Unreleased" or current date)
  -o, --output <file>     Write to specified file instead of stdout
  -w, --write             Prepend/write entry into CHANGELOG.md in current repo
  -s, --since <ref>       Git reference/tag/date to start from
  -u, --until <ref>       Git reference/tag to end at (default: HEAD)
  -a, --all               Include all commit history from repository creation
  -C <dir>                Path to git repository (default: current directory)
  -h, --help              Show this help message

Examples:
  ./changelog.sh
  ./changelog.sh -v "v1.2.0" -w
  ./changelog.sh --since "v1.1.0" --until "HEAD"
EOF
    exit 0
}

# Parse Arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -o|--output)
            TARGET_FILE="$2"
            shift 2
            ;;
        -w|--write)
            WRITE_FILE=true
            TARGET_FILE="CHANGELOG.md"
            shift
            ;;
        -s|--since)
            SINCE_REF="$2"
            shift 2
            ;;
        -u|--until)
            UNTIL_REF="$2"
            shift 2
            ;;
        -a|--all)
            INCLUDE_ALL=true
            shift
            ;;
        -C)
            REPO_PATH="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Error: Unknown option $1" >&2
            usage
            ;;
    esac
done

cd "$REPO_PATH"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: $(pwd) is not a git repository." >&2
    exit 1
fi

# Determine git commit range
GIT_RANGE=""
if [ "$INCLUDE_ALL" = true ]; then
    GIT_RANGE="$UNTIL_REF"
elif [ -n "$SINCE_REF" ]; then
    GIT_RANGE="${SINCE_REF}..${UNTIL_REF}"
else
    # Automatically detect latest git tag
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
    if [ -n "$LATEST_TAG" ]; then
        GIT_RANGE="${LATEST_TAG}..${UNTIL_REF}"
        if [ "$VERSION" = "Unreleased" ]; then
            VERSION="Unreleased (since ${LATEST_TAG})"
        fi
    else
        GIT_RANGE="$UNTIL_REF"
    fi
fi

CURRENT_DATE=$(date -u +"%Y-%m-%d")

# Temporary files for categorized entries
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

ADDED_FILE="$TMP_DIR/added.txt"
FIXED_FILE="$TMP_DIR/fixed.txt"
CHANGED_FILE="$TMP_DIR/changed.txt"
REMOVED_FILE="$TMP_DIR/removed.txt"
SECURITY_FILE="$TMP_DIR/security.txt"
OTHER_FILE="$TMP_DIR/other.txt"

touch "$ADDED_FILE" "$FIXED_FILE" "$CHANGED_FILE" "$REMOVED_FILE" "$SECURITY_FILE" "$OTHER_FILE"

# Extract commits (format: hash|subject)
git log "$GIT_RANGE" --no-merges --pretty=format:"%h|%s" | while IFS="|" read -r HASH SUBJECT || [ -n "$HASH" ]; do
    [ -z "$HASH" ] && continue

    # Categorize commit based on conventional prefixes while preserving casing
    if [[ "$SUBJECT" =~ ^(feat|feature|add)(\([^\)]+\))?:[[:space:]]*(.*) ]]; then
        SCOPE="${BASH_REMATCH[2]}"
        CLEAN_MSG="${BASH_REMATCH[3]}"
        if [ -n "$SCOPE" ]; then
            SCOPE_CLEAN="${SCOPE#(}"
            SCOPE_CLEAN="${SCOPE_CLEAN%)}"
            CLEAN_MSG="**${SCOPE_CLEAN}**: $CLEAN_MSG"
        fi
        echo "- ${CLEAN_MSG:-$SUBJECT} (\`$HASH\`)" >> "$ADDED_FILE"

    elif [[ "$SUBJECT" =~ ^(fix|bug|patch)(\([^\)]+\))?:[[:space:]]*(.*) ]]; then
        SCOPE="${BASH_REMATCH[2]}"
        CLEAN_MSG="${BASH_REMATCH[3]}"
        if [ -n "$SCOPE" ]; then
            SCOPE_CLEAN="${SCOPE#(}"
            SCOPE_CLEAN="${SCOPE_CLEAN%)}"
            CLEAN_MSG="**${SCOPE_CLEAN}**: $CLEAN_MSG"
        fi
        echo "- ${CLEAN_MSG:-$SUBJECT} (\`$HASH\`)" >> "$FIXED_FILE"

    elif [[ "$SUBJECT" =~ ^(refactor|perf|style|update|change)(\([^\)]+\))?:[[:space:]]*(.*) ]]; then
        SCOPE="${BASH_REMATCH[2]}"
        CLEAN_MSG="${BASH_REMATCH[3]}"
        if [ -n "$SCOPE" ]; then
            SCOPE_CLEAN="${SCOPE#(}"
            SCOPE_CLEAN="${SCOPE_CLEAN%)}"
            CLEAN_MSG="**${SCOPE_CLEAN}**: $CLEAN_MSG"
        fi
        echo "- ${CLEAN_MSG:-$SUBJECT} (\`$HASH\`)" >> "$CHANGED_FILE"

    elif [[ "$SUBJECT" =~ ^(remove|delete|drop|revert)(\([^\)]+\))?:[[:space:]]*(.*) ]]; then
        SCOPE="${BASH_REMATCH[2]}"
        CLEAN_MSG="${BASH_REMATCH[3]}"
        if [ -n "$SCOPE" ]; then
            SCOPE_CLEAN="${SCOPE#(}"
            SCOPE_CLEAN="${SCOPE_CLEAN%)}"
            CLEAN_MSG="**${SCOPE_CLEAN}**: $CLEAN_MSG"
        fi
        echo "- ${CLEAN_MSG:-$SUBJECT} (\`$HASH\`)" >> "$REMOVED_FILE"

    elif [[ "$SUBJECT" =~ ^(sec|security)(\([^\)]+\))?:[[:space:]]*(.*) ]]; then
        SCOPE="${BASH_REMATCH[2]}"
        CLEAN_MSG="${BASH_REMATCH[3]}"
        if [ -n "$SCOPE" ]; then
            SCOPE_CLEAN="${SCOPE#(}"
            SCOPE_CLEAN="${SCOPE_CLEAN%)}"
            CLEAN_MSG="**${SCOPE_CLEAN}**: $CLEAN_MSG"
        fi
        echo "- ${CLEAN_MSG:-$SUBJECT} (\`$HASH\`)" >> "$SECURITY_FILE"

    elif [[ "$SUBJECT" =~ ^(docs|chore|build|ci|test)(\([^\)]+\))?:[[:space:]]*(.*) ]]; then
        SCOPE="${BASH_REMATCH[2]}"
        CLEAN_MSG="${BASH_REMATCH[3]}"
        if [ -n "$SCOPE" ]; then
            SCOPE_CLEAN="${SCOPE#(}"
            SCOPE_CLEAN="${SCOPE_CLEAN%)}"
            CLEAN_MSG="**${SCOPE_CLEAN}**: $CLEAN_MSG"
        fi
        echo "- ${CLEAN_MSG:-$SUBJECT} (\`$HASH\`)" >> "$OTHER_FILE"
    else
        # Non-conventional commit fallback
        echo "- $SUBJECT (\`$HASH\`)" >> "$OTHER_FILE"
    fi
done

# Build changelog entry buffer
ENTRY_FILE="$TMP_DIR/entry.md"
{
    echo "## [$VERSION] - $CURRENT_DATE"
    echo ""

    if [ -s "$ADDED_FILE" ]; then
        echo "### Added"
        cat "$ADDED_FILE"
        echo ""
    fi

    if [ -s "$CHANGED_FILE" ]; then
        echo "### Changed"
        cat "$CHANGED_FILE"
        echo ""
    fi

    if [ -s "$FIXED_FILE" ]; then
        echo "### Fixed"
        cat "$FIXED_FILE"
        echo ""
    fi

    if [ -s "$REMOVED_FILE" ]; then
        echo "### Removed"
        cat "$REMOVED_FILE"
        echo ""
    fi

    if [ -s "$SECURITY_FILE" ]; then
        echo "### Security"
        cat "$SECURITY_FILE"
        echo ""
    fi

    if [ -s "$OTHER_FILE" ]; then
        echo "### Maintenance & Chores"
        cat "$OTHER_FILE"
        echo ""
    fi
} > "$ENTRY_FILE"

# If no changes were found
if ! grep -q "^- " "$ENTRY_FILE"; then
    echo "No commits found in range: ${GIT_RANGE}" >&2
    exit 0
fi

# Output handling
if [ "$WRITE_FILE" = true ] || [ -n "$TARGET_FILE" ]; then
    TARGET="${TARGET_FILE:-CHANGELOG.md}"
    if [ -f "$TARGET" ]; then
        # Prepend to existing changelog after header
        HEADER_FILE="$TMP_DIR/header.md"
        REST_FILE="$TMP_DIR/rest.md"
        
        # Check if file has # Changelog title
        if head -n 1 "$TARGET" | grep -qi "^# "; then
            head -n 2 "$TARGET" > "$HEADER_FILE"
            tail -n +3 "$TARGET" > "$REST_FILE"
            cat "$HEADER_FILE" "$ENTRY_FILE" "$REST_FILE" > "$TARGET"
        else
            cat "$ENTRY_FILE" "$TARGET" > "$TARGET.tmp" && mv "$TARGET.tmp" "$TARGET"
        fi
        echo "Successfully updated $TARGET"
    else
        {
            echo "# Changelog"
            echo ""
            echo "All notable changes to this project will be documented in this file."
            echo "The format is based on [Keep a Changelog](https://keepachangelog.com/)."
            echo ""
            cat "$ENTRY_FILE"
        } > "$TARGET"
        echo "Successfully generated $TARGET"
    fi
else
    cat "$ENTRY_FILE"
fi
