#!/usr/bin/env bash
# ============================================================
# changelog.sh — Structured CHANGELOG generator from git history
# Part of the `generate-changelog` Claude Code skill
# ============================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

OUTPUT_FILE="CHANGELOG.md"
DRY_RUN="false"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run|-n)
            DRY_RUN="true"
            ;;
        -o|--output)
            if [ "${2:-}" = "" ]; then
                log_error "Missing output file after $1"
                exit 1
            fi
            OUTPUT_FILE="$2"
            shift
            ;;
        -*)
            log_error "Unknown option: $1"
            exit 1
            ;;
        *)
            OUTPUT_FILE="$1"
            ;;
    esac
    shift
done

# -----------------------------------------------------------
# Check prerequisites
# -----------------------------------------------------------
if ! command -v git &> /dev/null; then
    log_error "Git is not installed. Please install git first."
    exit 1
fi

if ! git rev-parse --git-dir &> /dev/null; then
    log_error "Not a git repository. Run this script inside a git project."
    exit 1
fi

# -----------------------------------------------------------
# Determine version range
# -----------------------------------------------------------
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LATEST_TAG" ]; then
    RANGE=""
    VERSION="Unreleased"
    log_warn "No git tags found. Generating changelog from all commits."
else
    # Check if there are commits after the latest tag
    COMMIT_COUNT=$(git rev-list --count "${LATEST_TAG}..HEAD" 2>/dev/null || echo "0")
    if [ "$COMMIT_COUNT" -eq 0 ]; then
        log_info "No changes since $LATEST_TAG"
        exit 0
    fi
    RANGE="${LATEST_TAG}..HEAD"
    VERSION="Unreleased (since ${LATEST_TAG})"
fi

# -----------------------------------------------------------
# Collect commits (skip merges)
# -----------------------------------------------------------
COMMITS=$(git log --oneline --no-merges $RANGE 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
    log_info "No commits found. Make your first commit first!"
    exit 0
fi

TOTAL=$(echo "$COMMITS" | wc -l | tr -d ' ')
log_info "Found $TOTAL commits to process"

# -----------------------------------------------------------
# Categorize commits
# -----------------------------------------------------------
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
    [ -z "$line" ] && continue

    HASH=$(echo "$line" | awk '{print $1}')
    MSG=$(echo "$line" | cut -d' ' -f2-)

    # Lowercase and normalize conventional commit prefixes:
    # "feat(ui)!: message" -> "feat"
    PREFIX=$(echo "$MSG" | awk -F':' '{print tolower($1)}')
    PREFIX=$(echo "$PREFIX" | sed -E 's/\(.*\)//; s/!$//')

    case "$PREFIX" in
        feat|add|added|new)
            ADDED="${ADDED}- ${MSG#*: } (${HASH})\n"
            ;;
        fix|bug|patch|hotfix|resolve)
            FIXED="${FIXED}- ${MSG#*: } (${HASH})\n"
            ;;
        change|changed|update|updated|refactor|perf|style|improve|tweak|chore)
            CHANGED="${CHANGED}- ${MSG#*: } (${HASH})\n"
            ;;
        remove|delete|drop|deprecate|revert)
            REMOVED="${REMOVED}- ${MSG#*: } (${HASH})\n"
            ;;
        *)
            # Strip conventional commit prefix if present
            if echo "$MSG" | grep -q ':'; then
                CHANGED="${CHANGED}- ${MSG#*: } (${HASH})\n"
            else
                CHANGED="${CHANGED}- ${MSG} (${HASH})\n"
            fi
            ;;
    esac
done <<< "$COMMITS"

# -----------------------------------------------------------
# Generate changelog entry
# -----------------------------------------------------------
DATE=$(date +%Y-%m-%d)

# Build the new entry
ENTRY="## ${VERSION} — ${DATE}

### Added
"
if [ -n "$ADDED" ]; then
    ENTRY+=$(echo -e "$ADDED")
else
    ENTRY+="_None_"
fi

ENTRY+="
### Fixed
"
if [ -n "$FIXED" ]; then
    ENTRY+=$(echo -e "$FIXED")
else
    ENTRY+="_None_"
fi

ENTRY+="
### Changed
"
if [ -n "$CHANGED" ]; then
    ENTRY+=$(echo -e "$CHANGED")
else
    ENTRY+="_None_"
fi

ENTRY+="
### Removed
"
if [ -n "$REMOVED" ]; then
    ENTRY+=$(echo -e "$REMOVED")
else
    ENTRY+="_None_"
fi

# -----------------------------------------------------------
# Write output (prepend to existing CHANGELOG)
# -----------------------------------------------------------
if [ "$DRY_RUN" = "true" ]; then
    echo -e "$ENTRY"
    echo ""
    log_info "Dry run complete. Use 'bash changelog.sh' to write the file."
    exit 0
fi

if [ -f "$OUTPUT_FILE" ]; then
    # Prepend: keep existing content below the new entry
    EXISTING=$(cat "$OUTPUT_FILE")
    # Check if it already has a header
    if echo "$EXISTING" | head -1 | grep -q "^# Changelog"; then
        # Has header — insert new entry after the header line
        HEADER=$(echo "$EXISTING" | head -1)
        BODY=$(echo "$EXISTING" | tail -n +2)
        echo -e "$HEADER\n\n$ENTRY\n$BODY" > "$OUTPUT_FILE"
    else
        # No header — wrap everything
        echo -e "# Changelog\n\n$ENTRY\n$EXISTING" > "$OUTPUT_FILE"
    fi
else
    echo -e "# Changelog\n\n$ENTRY" > "$OUTPUT_FILE"
fi

# -----------------------------------------------------------
# Report
# -----------------------------------------------------------
log_info "Changelog written to $OUTPUT_FILE"
log_info "Version: $VERSION"
log_info "Commits: $TOTAL"

echo ""
echo "Preview (first 5 entries):"
echo "--------------------------"
echo -e "$ENTRY" | grep "^- " | head -5 || echo "  (no categorized commits)"

exit 0
