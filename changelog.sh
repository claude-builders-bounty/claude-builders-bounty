#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   ./changelog.sh                    # Generate since last tag
#   ./changelog.sh --from v1.0.0      # Generate from specific tag/commit
#   ./changelog.sh --range v1.0.0..v2.0.0  # Generate between two tags
#   ./changelog.sh --output FILE.md   # Custom output file (default: CHANGELOG.md)
#
# Requirements: git (macOS & Linux compatible)
# License: MIT

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
COMMIT_RANGE=""

# ─── Parse arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --from)   COMMIT_RANGE="${2}..HEAD"; shift 2 ;;
        --range)  COMMIT_RANGE="$2"; shift 2 ;;
        --output) OUTPUT_FILE="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: ./changelog.sh [--from TAG] [--range TAG1..TAG2] [--output FILE]"
            exit 0 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# ─── Validate git repo ───────────────────────────────────────────────────────
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Not inside a git repository" >&2
    exit 1
fi

# ─── Determine commit range ──────────────────────────────────────────────────
if [[ -z "$COMMIT_RANGE" ]]; then
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
    if [[ -n "$LATEST_TAG" ]]; then
        COMMIT_RANGE="${LATEST_TAG}..HEAD"
    else
        COMMIT_RANGE=""  # no tags — use all commits
    fi
fi

# ─── Fetch commits ───────────────────────────────────────────────────────────
# Format: short_hash<TAB>subject
TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

if [[ -n "$COMMIT_RANGE" ]]; then
    git log "$COMMIT_RANGE" --pretty='format:%h|%s' --no-merges > "$TMPFILE" 2>/dev/null || true
else
    git log --pretty='format:%h|%s' --no-merges > "$TMPFILE" 2>/dev/null || true
fi

if [[ ! -s "$TMPFILE" ]]; then
    echo "No commits found in range."
    exit 0
fi

# ─── Categorize commits ─────────────────────────────────────────────────────
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

while IFS='|' read -r hash subject || [[ -n "$subject" ]]; do
    [[ -z "$subject" ]] && continue

    # Try conventional commit type prefix first
    cc_type=""
    clean_msg="$subject"
    cc_regex='^([a-zA-Z]+)(\([^)]*\))?:\ *(.*)'
    if [[ "$subject" =~ $cc_regex ]]; then
        cc_type=$(echo "${BASH_REMATCH[1]}" | tr '[:upper:]' '[:lower:]')  # lowercase
        clean_msg="${BASH_REMATCH[3]}"
    fi

    if [[ -n "$cc_type" ]]; then
        case "$cc_type" in
            feat|feature)         ADDED+=("$clean_msg") ;;
            fix|bugfix|hotfix)    FIXED+=("$clean_msg") ;;
            refactor|style|perf)  CHANGED+=("$clean_msg") ;;
            chore|ci|build|docs)  OTHER+=("$clean_msg") ;;
            remove|deprecate)     REMOVED+=("$clean_msg") ;;
            change|update)        CHANGED+=("$clean_msg") ;;
            *)                    OTHER+=("$clean_msg") ;;
        esac
    else
        # No conventional commit prefix — fallback to keyword matching
        lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
        if [[ "$lower_subject" =~ ^(add|new|implement|create|introduce|support|enable) ]] || \
           [[ "$lower_subject" == *"add "* ]] || [[ "$lower_subject" == *"new "* ]]; then
            ADDED+=("$subject")
        elif [[ "$lower_subject" =~ ^(fix|resolve|patch|correct|repair) ]] || \
             [[ "$lower_subject" == *"fix "* ]] || [[ "$lower_subject" == *"bug "* ]]; then
            FIXED+=("$subject")
        elif [[ "$lower_subject" =~ ^(change|update|refactor|improve|optimize|restructure|rename|move) ]] || \
             [[ "$lower_subject" == *"update "* ]] || [[ "$lower_subject" == *"refactor "* ]]; then
            CHANGED+=("$subject")
        elif [[ "$lower_subject" =~ ^(remove|delete|deprecate|drop) ]] || \
             [[ "$lower_subject" == *"remove "* ]] || [[ "$lower_subject" == *"delete "* ]]; then
            REMOVED+=("$subject")
        else
            OTHER+=("$subject")
        fi
    fi
done < "$TMPFILE"

# ─── Version header ─────────────────────────────────────────────────────────
if [[ "$COMMIT_RANGE" == *".."* ]]; then
    range_to="${COMMIT_RANGE#*..}"
    if [[ "$range_to" == "HEAD" ]] || [[ -z "$range_to" ]]; then
        VERSION="Unreleased"
    else
        VERSION="$range_to"
    fi
else
    VERSION="Unreleased"
fi
TODAY=$(date +%Y-%m-%d)

# ─── Generate CHANGELOG.md ──────────────────────────────────────────────────
{
    echo "# Changelog"
    echo ""
    echo "## [$VERSION] — $TODAY"
    echo ""

    if [[ ${#ADDED[@]} -gt 0 ]]; then
        echo "### ✨ Added"
        echo ""
        for item in "${ADDED[@]}"; do echo "- $item"; done
        echo ""
    fi

    if [[ ${#FIXED[@]} -gt 0 ]]; then
        echo "### 🐛 Fixed"
        echo ""
        for item in "${FIXED[@]}"; do echo "- $item"; done
        echo ""
    fi

    if [[ ${#CHANGED[@]} -gt 0 ]]; then
        echo "### 🔧 Changed"
        echo ""
        for item in "${CHANGED[@]}"; do echo "- $item"; done
        echo ""
    fi

    if [[ ${#REMOVED[@]} -gt 0 ]]; then
        echo "### 🗑️ Removed"
        echo ""
        for item in "${REMOVED[@]}"; do echo "- $item"; done
        echo ""
    fi

    if [[ ${#OTHER[@]} -gt 0 ]]; then
        echo "### 📝 Other"
        echo ""
        for item in "${OTHER[@]}"; do echo "- $item"; done
        echo ""
    fi
} > "$OUTPUT_FILE"

# ─── Summary ─────────────────────────────────────────────────────────────────
TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#OTHER[@]} ))
echo "✅ CHANGELOG generated: $OUTPUT_FILE"
echo "   Version: $VERSION | Date: $TODAY | Commits: $TOTAL"
echo "     Added:   ${#ADDED[@]}  Fixed:   ${#FIXED[@]}"
echo "     Changed: ${#CHANGED[@]}  Removed: ${#REMOVED[@]}  Other:   ${#OTHER[@]}"
