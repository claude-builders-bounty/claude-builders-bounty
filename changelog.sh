#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage: bash changelog.sh [OPTIONS]
#
# Options:
#   -o, --output FILE    Output file (default: CHANGELOG.md)
#   -t, --tag TAG        Tag to start from (default: latest tag)
#   -r, --repo PATH      Git repository path (default: current directory)
#   -d, --date DATE      Release date (default: today)
#   -f, --format FORMAT  Output format: markdown|json (default: markdown)
#   -h, --help           Show this help
#
# Conventional commit mapping:
#   feat:     -> Added
#   fix:      -> Fixed
#   refactor: -> Changed
#   remove:   -> Removed
#   delete:   -> Removed
#   Other     -> Changed (default)
#

set -euo pipefail

# --- Defaults ---
OUTPUT_FILE="CHANGELOG.md"
TARGET_TAG=""
REPO_PATH="."
RELEASE_DATE="$(date +%Y-%m-%d)"
FORMAT="markdown"

# --- Colors for terminal output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- Helper functions ---
die() { echo -e "${RED}Error: $1${NC}" >&2; exit 1; }
info() { echo -e "${GREEN}$1${NC}" >&2; }
warn() { echo -e "${YELLOW}Warning: $1${NC}" >&2; }

usage() {
    sed -n '/^# Usage:/,/^[^#]/p' "$0" | sed 's/^# \?//' | head -n -1
    exit 0
}

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        -o|--output)  OUTPUT_FILE="$2"; shift 2 ;;
        -t|--tag)     TARGET_TAG="$2"; shift 2 ;;
        -r|--repo)    REPO_PATH="$2"; shift 2 ;;
        -d|--date)    RELEASE_DATE="$2"; shift 2 ;;
        -f|--format)  FORMAT="$2"; shift 2 ;;
        -h|--help)    usage ;;
        *)            die "Unknown option: $1" ;;
    esac
done

# --- Validate repo ---
cd "$REPO_PATH" || die "Cannot cd to $REPO_PATH"
git rev-parse --is-inside-work-tree &>/dev/null || die "Not a git repository: $REPO_PATH"

# --- Find the latest tag if none specified ---
if [[ -z "$TARGET_TAG" ]]; then
    TARGET_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
fi

# --- Build the commit range ---
if [[ -n "$TARGET_TAG" ]]; then
    RANGE="${TARGET_TAG}..HEAD"
    TAG_NAME="$TARGET_TAG"
    info "Generating changelog since tag: $TARGET_TAG"
else
    RANGE=""
    TAG_NAME=""
    warn "No tags found — including entire history"
fi

# --- Fetch commits ---
if [[ -n "$RANGE" ]]; then
    COMMITS=$(git log "$RANGE" --pretty=format:"%H||%s||%an" --no-merges 2>/dev/null || true)
else
    COMMITS=$(git log --pretty=format:"%H||%s||%an" --no-merges 2>/dev/null || true)
fi

if [[ -z "$COMMITS" ]]; then
    warn "No commits found in range."
    exit 0
fi

# --- Category arrays ---
declare -a ADDED=() FIXED=() CHANGED=() REMOVED=()

# --- Categorize each commit ---
while IFS=$'\n' read -r line; do
    hash="${line%%||*}"
    remainder="${line#*||}"
    subject="${remainder%%||*}"
    author="${remainder#*||}"
    # Sanitize
    subject="$(echo "$subject" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$subject" ]] && continue

    # Lowercase prefix detection
    lower_subject="$(echo "$subject" | tr '[:upper:]' '[:lower:]')"

    entry="- ${subject} (\`${hash:0:7}\`)"

    case "$lower_subject" in
        feat:*|feat\(*\):*)
            ADDED+=("$entry") ;;
        fix:*|fix\(*\):*)
            FIXED+=("$entry") ;;
        refactor:*|refactor\(*\):*)
            CHANGED+=("$entry") ;;
        remove:*|remove\(*\):*|delete:*|delete\(*\):*)
            REMOVED+=("$entry") ;;
        # Handle breaking changes / chores / docs / style / test / ci / perf
        perf:*|perf\(*\):*)
            CHANGED+=("$entry") ;;
        style:*|style\(*\):*)
            CHANGED+=("$entry") ;;
        docs:*|docs\(*\):*)
            CHANGED+=("$entry") ;;
        test:*|test\(*\):*)
            CHANGED+=("$entry") ;;
        ci:*|ci\(*\):*)
            CHANGED+=("$entry") ;;
        build:*|build\(*\):*)
            CHANGED+=("$entry") ;;
        chore:*|chore\(*\):*)
            CHANGED+=("$entry") ;;
        *)
            CHANGED+=("$entry") ;;
    esac
done <<< "$COMMITS"

# --- JSON output ---
if [[ "$FORMAT" == "json" ]]; then
    json_array() {
        local arr=("$@")
        if [[ ${#arr[@]} -eq 0 ]]; then
            echo "[]"
            return
        fi
        echo "["
        for i in "${!arr[@]}"; do
            local item="${arr[$i]}"
            # Extract the commit message (strip leading "- " and trailing backtick hash)
            local msg
            msg="$(echo "$item" | sed 's/^- //;s/ (`[a-f0-9]*`)$//')"
            printf '    {"message": "%s"}' "$(echo "$msg" | sed 's/"/\\"/g')"
            [[ $i -lt $((${#arr[@]} - 1)) ]] && echo "," || echo ""
        done
        echo "  ]"
    }

    echo "{"
    echo "  \"version\": \"$TAG_NAME\","
    echo "  \"date\": \"$RELEASE_DATE\","
    echo "  \"added\": $(json_array "${ADDED[@]+"${ADDED[@]}"}"),"
    echo "  \"fixed\": $(json_array "${FIXED[@]+"${FIXED[@]}"}"),"
    echo "  \"changed\": $(json_array "${CHANGED[@]+"${CHANGED[@]}"}"),"
    echo "  \"removed\": $(json_array "${REMOVED[@]+"${REMOVED[@]}"}")"
    echo "}"
    exit 0
fi

# --- Markdown output ---
{
    if [[ -n "$TAG_NAME" ]]; then
        echo "# Changelog"
        echo ""
        echo "## [$TAG_NAME] — $RELEASE_DATE"
    else
        echo "# Changelog"
        echo ""
        echo "## [Unreleased] — $RELEASE_DATE"
    fi
    echo ""

    if [[ ${#ADDED[@]} -gt 0 ]]; then
        echo "### Added"
        printf '%s\n' "${ADDED[@]}"
        echo ""
    fi

    if [[ ${#FIXED[@]} -gt 0 ]]; then
        echo "### Fixed"
        printf '%s\n' "${FIXED[@]}"
        echo ""
    fi

    if [[ ${#CHANGED[@]} -gt 0 ]]; then
        echo "### Changed"
        printf '%s\n' "${CHANGED[@]}"
        echo ""
    fi

    if [[ ${#REMOVED[@]} -gt 0 ]]; then
        echo "### Removed"
        printf '%s\n' "${REMOVED[@]}"
        echo ""
    fi

} > "$OUTPUT_FILE"

# --- Report results ---
TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))
info "✅ Generated $OUTPUT_FILE with $TOTAL commits:"
[[ ${#ADDED[@]}   -gt 0 ]] && echo "   Added:   ${#ADDED[@]}" || true
[[ ${#FIXED[@]}   -gt 0 ]] && echo "   Fixed:   ${#FIXED[@]}" || true
[[ ${#CHANGED[@]} -gt 0 ]] && echo "   Changed: ${#CHANGED[@]}" || true
[[ ${#REMOVED[@]} -gt 0 ]] && echo "   Removed: ${#REMOVED[@]}" || true
