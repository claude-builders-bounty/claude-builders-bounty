#!/usr/bin/env bash
# =============================================================================
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Categories commits by type using conventional commit prefixes:
#   feat:     → Added
#   fix:      → Fixed
#   refactor: → Changed
#   chore:    → Changed
#   docs:     → Changed
#   perf:     → Changed
#   breaking  → Changed (with ⚠️ marker)
#
# Usage:
#   ./changelog.sh                      Generate CHANGELOG.md
#   ./changelog.sh --dry-run            Preview without writing
#   ./changelog.sh --from v1.0.0        Only commits since tag
#   ./changelog.sh --output HISTORY.md  Custom output file
#   ./changelog.sh --help               Show usage
# =============================================================================

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
OUTPUT_FILE="CHANGELOG.md"
DRY_RUN=false
FROM_TAG=""
PROJECT_NAME=""

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── Functions ─────────────────────────────────────────────────────────────────
usage() {
    cat << 'EOF'
Usage: changelog.sh [OPTIONS]

Generate a structured CHANGELOG.md from git history.

Options:
  --dry-run         Print to stdout instead of writing to file
  --from TAG        Only include commits since this git tag
  --output FILE     Output file path (default: CHANGELOG.md)
  --help            Show this help message

Categories:
  feat:     → Added
  fix:      → Fixed
  refactor: → Changed
  chore:    → Changed
  docs:     → Changed
  perf:     → Changed
  BREAKING  → Changed (with ⚠️ marker)

Examples:
  ./changelog.sh
  ./changelog.sh --dry-run
  ./changelog.sh --from v1.0.0 --output HISTORY.md
EOF
    exit 0
}

log_info()  { echo -e "${CYAN}ℹ${NC} $*"; }
log_ok()    { echo -e "${GREEN}✓${NC} $*"; }
log_warn()  { echo -e "${YELLOW}⚠${NC} $*"; }
log_error() { echo -e "${RED}✗${NC} $*" >&2; }

# ── Parse arguments ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)    DRY_RUN=true; shift ;;
        --from)       FROM_TAG="$2"; shift 2 ;;
        --output)     OUTPUT_FILE="$2"; shift 2 ;;
        --help|-h)    usage ;;
        *)
            log_error "Unknown option: $1"
            echo "Run with --help for usage."
            exit 1
            ;;
    esac
done

# ── Pre-flight checks ───────────────────────────────────────────────────────
if ! command -v git &>/dev/null; then
    log_error "git is not installed or not in PATH"
    exit 1
fi

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    log_error "Not inside a git repository"
    exit 1
fi

# ── Determine git log range ──────────────────────────────────────────────────
GIT_RANGE=""
if [[ -n "$FROM_TAG" ]]; then
    if ! git rev-parse "$FROM_TAG" &>/dev/null; then
        log_error "Tag '$FROM_TAG' not found"
        exit 1
    fi
    GIT_RANGE="${FROM_TAG}..HEAD"
    log_info "Collecting commits since tag: $FROM_TAG"
else
    # Find the latest tag, if any
    LATEST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
    if [[ -n "$LATEST_TAG" ]]; then
        GIT_RANGE="${LATEST_TAG}..HEAD"
        log_info "Collecting commits since tag: $LATEST_TAG"
    else
        GIT_RANGE=""
        log_info "No tags found — collecting all commits"
    fi
fi

# ── Get project name ─────────────────────────────────────────────────────────
PROJECT_NAME="$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")"

# ── Collect and categorize commits ───────────────────────────────────────────
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
UNCATEGORIZED=0

while IFS= read -r line; do
    [[ -z "$line" ]] && continue

    # Parse hash and subject
    HASH="${line:0:7}"
    SUBJECT="${line:8}"

    # Skip merge commits
    if [[ "$SUBJECT" =~ ^Merge[[:space:]] ]]; then
        continue
    fi

    # Extract conventional prefix (case-insensitive)
    PREFIX=""
    BODY=""
    if [[ "$SUBJECT" =~ ^([a-zA-Z]+)(\(.+\))?(!)?:[[:space:]]*(.*) ]]; then
        PREFIX="${BASH_REMATCH[1],,}"  # lowercase
        BODY="${BASH_REMATCH[4]}"
    fi

    # Check for breaking change marker
    BREAKING=false
    if [[ "${BASH_REMATCH[3]:-}" == "!" ]] || [[ "$SUBJECT" == *"BREAKING CHANGE"* ]]; then
        BREAKING=true
    fi

    # Format the entry
    if $BREAKING; then
        ENTRY="- ⚠️ **BREAKING:** ${BODY:-$SUBJECT} (\`${HASH}\`)"
    else
        ENTRY="- ${BODY:-$SUBJECT} (\`${HASH}\`)"
    fi

    # Categorize
    case "$PREFIX" in
        feat|feature)
            ADDED+=("$ENTRY")
            ;;
        fix|bugfix|hotfix)
            FIXED+=("$ENTRY")
            ;;
        remove|rm|delete)
            REMOVED+=("$ENTRY")
            ;;
        refactor|chore|docs|doc|style|perf|ci|build|test|revert)
            CHANGED+=("$ENTRY")
            ;;
        "")
            # No conventional prefix — try keyword matching
            LOWER="${SUBJECT,,}"
            if   [[ "$LOWER" =~ ^(add|new|implement|introduce)[[:space:]] ]]; then
                ADDED+=("$ENTRY")
            elif [[ "$LOWER" =~ ^(fix|bug|patch|resolve|correct)[[:space:]] ]]; then
                FIXED+=("$ENTRY")
            elif [[ "$LOWER" =~ ^(remove|delete|drop|deprecate)[[:space:]] ]]; then
                REMOVED+=("$ENTRY")
            elif [[ "$LOWER" =~ ^(update|change|improve|rename|move|restructure)[[:space:]] ]]; then
                CHANGED+=("$ENTRY")
            else
                CHANGED+=("$ENTRY")
                ((UNCATEGORIZED++)) || true
            fi
            ;;
        *)
            CHANGED+=("$ENTRY")
            ((UNCATEGORIZED++)) || true
            ;;
    esac

done < <(git log --oneline ${GIT_RANGE} 2>/dev/null)

TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))

if [[ $TOTAL -eq 0 ]]; then
    log_warn "No commits found in range. Nothing to generate."
    exit 0
fi

log_ok "Found $TOTAL commits (${#ADDED[@]} added, ${#FIXED[@]} fixed, ${#CHANGED[@]} changed, ${#REMOVED[@]} removed)"

# ── Build the changelog ──────────────────────────────────────────────────────
TODAY="$(date +%Y-%m-%d)"
OUTPUT=""

OUTPUT+="## [Unreleased] — ${TODAY}"
OUTPUT+="\n"

if [[ ${#ADDED[@]} -gt 0 ]]; then
    OUTPUT+="\n### Added\n"
    for entry in "${ADDED[@]}"; do
        OUTPUT+="${entry}\n"
    done
fi

if [[ ${#FIXED[@]} -gt 0 ]]; then
    OUTPUT+="\n### Fixed\n"
    for entry in "${FIXED[@]}"; do
        OUTPUT+="${entry}\n"
    done
fi

if [[ ${#CHANGED[@]} -gt 0 ]]; then
    OUTPUT+="\n### Changed\n"
    for entry in "${CHANGED[@]}"; do
        OUTPUT+="${entry}\n"
    done
fi

if [[ ${#REMOVED[@]} -gt 0 ]]; then
    OUTPUT+="\n### Removed\n"
    for entry in "${REMOVED[@]}"; do
        OUTPUT+="${entry}\n"
    done
fi

OUTPUT+="\n---\n"
OUTPUT+="*Generated by [changelog.sh](https://github.com/claude-builders-bounty/claude-builders-bounty/tree/main/skills/generate-changelog) on ${TODAY}*\n"

# ── Output ────────────────────────────────────────────────────────────────────
if $DRY_RUN; then
    echo ""
    echo -e "${CYAN}═══ DRY RUN ═══${NC}"
    echo ""
    echo -e "$OUTPUT"
else
    # Prepend to existing changelog or create new
    if [[ -f "$OUTPUT_FILE" ]]; then
        # Find where the first ## heading is and insert before it
        EXISTING="$(cat "$OUTPUT_FILE")"
        {
            echo -e "$OUTPUT"
            echo "$EXISTING"
        } > "${OUTPUT_FILE}.tmp"
        mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
        log_ok "Prepended new entries to ${OUTPUT_FILE}"
    else
        {
            echo "# ${PROJECT_NAME} Changelog"
            echo ""
            echo -e "$OUTPUT"
        } > "$OUTPUT_FILE"
        log_ok "Created ${OUTPUT_FILE}"
    fi

    # Count how many sections have entries
    _sections=0
    [[ ${#ADDED[@]}   -gt 0 ]] && (( _sections++ )) || true
    [[ ${#FIXED[@]}   -gt 0 ]] && (( _sections++ )) || true
    [[ ${#CHANGED[@]} -gt 0 ]] && (( _sections++ )) || true
    [[ ${#REMOVED[@]} -gt 0 ]] && (( _sections++ )) || true
    log_info "${TOTAL} commits categorized into ${_sections} sections"
fi
