#!/usr/bin/env bash
# =============================================================================
# generate-changelog.sh — Auto-generate CHANGELOG.md from conventional commits
# =============================================================================
#
# Scans git history since the last tag, categorizes commits by conventional
# commit prefixes, and produces a formatted CHANGELOG.md.
#
# Usage:
#   ./generate-changelog.sh [OPTIONS] [REPO_PATH]
#
# Options:
#   -o, --output FILE     Write changelog to FILE (default: CHANGELOG.md)
#   -t, --tag TAG         Start from TAG instead of the latest tag
#   -r, --range RANGE     Custom git revision range (e.g. v1.0..HEAD)
#   -h, --help            Show this help message
#
# Mapping (Conventional Commit → Changelog Section):
#   feat     → Added
#   fix      → Fixed
#   chore, perf, refactor, docs, style, test, ci, build → Changed
#   ! suffix or BREAKING CHANGE footer              → Removed (also appears in
#                                                      its primary section)
#
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Colors & formatting
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { printf "${CYAN}[INFO]${NC} %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${NC} %s\n" "$*" >&2; }
err()   { printf "${RED}[ERROR]${NC} %s\n" "$*" >&2; }

# -----------------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------
show_help() {
    cat <<'EOF_USAGE'
generate-changelog.sh — Auto-generate CHANGELOG.md from conventional commits

Scans git history since the last tag, categorizes commits by conventional
commit prefixes, and produces a formatted CHANGELOG.md.

Usage:
  ./generate-changelog.sh [OPTIONS] [REPO_PATH]

Options:
  -o, --output FILE     Write changelog to FILE (default: CHANGELOG.md)
  -t, --tag TAG         Start from TAG instead of the latest tag
  -r, --range RANGE     Custom git revision range (e.g. v1.0..HEAD)
  -h, --help            Show this help message

Mapping (Conventional Commit → Changelog Section):
  feat     → Added
  fix      → Fixed
  chore, perf, refactor, docs, style, test, ci, build → Changed
  ! suffix or BREAKING CHANGE footer                  → Removed

EOF_USAGE
    exit 0
}

# -----------------------------------------------------------------------------
# Parse arguments
# -----------------------------------------------------------------------------
OUTPUT_FILE="CHANGELOG.md"
START_TAG=""
RANGE=""
REPO_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -t|--tag)
            START_TAG="$2"
            shift 2
            ;;
        -r|--range)
            RANGE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        -*)
            err "Unknown option: $1"
            show_help
            ;;
        *)
            REPO_PATH="$1"
            shift
            ;;
    esac
done

# -----------------------------------------------------------------------------
# Validate environment
# -----------------------------------------------------------------------------
if ! command -v git &>/dev/null; then
    err "git is not installed or not in PATH"
    exit 1
fi

if [[ -n "$REPO_PATH" ]]; then
    if [[ ! -d "$REPO_PATH/.git" ]]; then
        err "Not a git repository: $REPO_PATH"
        exit 1
    fi
    cd "$REPO_PATH"
else
    # Use current directory
    if ! git rev-parse --git-dir &>/dev/null; then
        err "Not inside a git repository (and no REPO_PATH given)."
        exit 1
    fi
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
info "Repository: $REPO_ROOT"
cd "$REPO_ROOT"

# -----------------------------------------------------------------------------
# Determine revision range
# -----------------------------------------------------------------------------
if [[ -n "$RANGE" ]]; then
    REV_RANGE="$RANGE"
    info "Using custom range: $REV_RANGE"
elif [[ -n "$START_TAG" ]]; then
    if git rev-parse "$START_TAG" &>/dev/null; then
        REV_RANGE="${START_TAG}..HEAD"
    else
        err "Tag not found: $START_TAG"
        exit 1
    fi
    info "Using tag range: $REV_RANGE"
else
    # Get the latest tag reachable from HEAD
    LATEST_TAG="$(git describe --tags --abbrev=0 HEAD 2>/dev/null || true)"

    if [[ -z "$LATEST_TAG" ]]; then
        warn "No tags found in this repository. Using full history."
        REV_RANGE=""
    else
        REV_RANGE="${LATEST_TAG}..HEAD"
        info "Latest tag: ${LATEST_TAG}"
        # Check if there are any commits since the tag
        COMMIT_COUNT="$(git rev-list --count "$REV_RANGE" 2>/dev/null || echo 0)"
        if [[ "$COMMIT_COUNT" -eq 0 ]]; then
            warn "No commits since tag ${LATEST_TAG}. Changelog will be empty."
        fi
    fi
fi

# -----------------------------------------------------------------------------
# Fetch commits
# -----------------------------------------------------------------------------
if [[ -n "$REV_RANGE" ]]; then
    info "Fetching commits in range: $REV_RANGE"
    COMMITS="$(git log "$REV_RANGE" --pretty=format:'%s' 2>/dev/null || true)"
else
    info "Fetching all commits (no range specified)."
    COMMITS="$(git log --pretty=format:'%s' 2>/dev/null || true)"
fi

if [[ -z "$COMMITS" ]]; then
    warn "No commits found."
fi

# -----------------------------------------------------------------------------
# Categorization helpers
# -----------------------------------------------------------------------------
# We collect commits into associative arrays per section.
# We also track breaking changes separately.

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

# Conventional-commit regex explanation:
#   ^(type)(optional-scope)?!(optional): description
#
#   type: feat, fix, chore, perf, refactor, docs, style, test, ci, build, revert
#   scope: (something)  — optional
#   !     — marks breaking change
#   :     — separator

TYPE_REGEX='^(feat|fix|chore|perf|refactor|docs|style|test|ci|build|revert)(\([^)]*\))?!?:\s*(.*)$'

# Map conventional commit type to section
map_type_to_section() {
    local type="$1"
    case "$type" in
        feat)   echo "ADDED"    ;;
        fix)    echo "FIXED"    ;;
        *)
            # chore, perf, refactor, docs, style, test, ci, build, revert
            echo "CHANGED"
            ;;
    esac
}

# Format a commit line: strip the prefix to make it human-readable
format_commit_line() {
    local raw="$1"
    local type="$2"
    local description="$3"

    # Start with the raw subject, then strip the conventional prefix
    local formatted="$raw"

    # Try to extract just the description part (after colon + space)
    if [[ "$raw" =~ $TYPE_REGEX ]]; then
        local scope="${BASH_REMATCH[2]:-}"
        local desc="${BASH_REMATCH[3]}"
        if [[ -n "$scope" ]]; then
            # Keep scope for clarity: type(scope): description → **scope:** description
            formatted="**${scope//[()]/}:** ${desc}"
        else
            formatted="$desc"
        fi
    fi

    echo "- $formatted"
}

# -----------------------------------------------------------------------------
# Process commits
# -----------------------------------------------------------------------------
while IFS= read -r line; do
    [[ -z "$line" ]] && continue

    is_breaking=false

    # Check for breaking change marker: ! before : or BREAKING CHANGE in full message
    if [[ "$line" =~ !: ]]; then
        is_breaking=true
    fi

    if [[ "$line" =~ $TYPE_REGEX ]]; then
        local_type="${BASH_REMATCH[1]}"
        local_desc="${BASH_REMATCH[3]}"
        section="$(map_type_to_section "$local_type")"

        # Full message check for BREAKING CHANGE footer (if we had the body)
        # We only have the subject line from `git log --pretty=format:'%s'`,
        # but we also check the ! marker above.

        formatted="$(format_commit_line "$line" "$local_type" "$local_desc")"

        case "$section" in
            ADDED)   ADDED+=("$formatted")   ;;
            FIXED)   FIXED+=("$formatted")   ;;
            CHANGED) CHANGED+=("$formatted") ;;
        esac

        if [[ "$is_breaking" == true ]]; then
            REMOVED+=("$formatted ⚠️ **Breaking**")
        fi
    else
        # Non-conventional commit — put in Changed
        CHANGED+=("- $line")
    fi
done <<< "$COMMITS"

# Also scan full commit bodies for BREAKING CHANGE footer
if [[ -n "$REV_RANGE" ]]; then
    BREAKING_COMMITS="$(git log "$REV_RANGE" --pretty=format:'%H|%s' 2>/dev/null || true)"
elif [[ -n "$COMMITS" ]]; then
    BREAKING_COMMITS="$(git log --pretty=format:'%H|%s' 2>/dev/null || true)"
else
    BREAKING_COMMITS=""
fi

if [[ -n "$BREAKING_COMMITS" ]]; then
    while IFS='|' read -r hash subject; do
        body="$(git log -1 --pretty=format:'%b' "$hash" 2>/dev/null || true)"
        if echo "$body" | grep -qi 'BREAKING[ -]CHANGE'; then
            # Check if already added via ! marker
            already=false
            for item in "${REMOVED[@]}"; do
                if [[ "$item" == *"$subject"* ]]; then
                    already=true
                    break
                fi
            done
            if [[ "$already" == false ]]; then
                # Re-format the subject
                formatted=""
                if [[ "$subject" =~ $TYPE_REGEX ]]; then
                    local_scope="${BASH_REMATCH[2]:-}"
                    local_desc="${BASH_REMATCH[3]}"
                    if [[ -n "$local_scope" ]]; then
                        formatted="- **${local_scope//[()]/}:** ${local_desc} ⚠️ **Breaking**"
                    else
                        formatted="- ${local_desc} ⚠️ **Breaking**"
                    fi
                else
                    formatted="- ${subject} ⚠️ **Breaking**"
                fi
                REMOVED+=("$formatted")
            fi
        fi
    done <<< "$BREAKING_COMMITS"
fi

# -----------------------------------------------------------------------------
# Determine version / tag header
# -----------------------------------------------------------------------------
DATE="$(date +%Y-%m-%d)"
if [[ -n "$LATEST_TAG" && -z "$START_TAG" && -z "$RANGE" ]]; then
    HEADER_TAG="$LATEST_TAG → HEAD"
else
    CURRENT_TAG="$(git describe --tags --abbrev=0 HEAD 2>/dev/null || true)"
    if [[ -n "$CURRENT_TAG" ]]; then
        HEADER_TAG="$CURRENT_TAG"
    else
        HEADER_TAG="Unreleased"
    fi
fi

# -----------------------------------------------------------------------------
# Generate markdown
# -----------------------------------------------------------------------------
OUTPUT_DIR="$(dirname "$OUTPUT_FILE")"
if [[ "$OUTPUT_DIR" != "." ]]; then
    mkdir -p "$OUTPUT_DIR"
fi

{
    echo "# Changelog"
    echo ""
    echo "## ${HEADER_TAG} (${DATE})"
    echo ""

    # --- Added ---
    if [[ ${#ADDED[@]} -gt 0 ]]; then
        echo "### Added"
        for item in "${ADDED[@]}"; do
            echo "$item"
        done
        echo ""
    fi

    # --- Fixed ---
    if [[ ${#FIXED[@]} -gt 0 ]]; then
        echo "### Fixed"
        for item in "${FIXED[@]}"; do
            echo "$item"
        done
        echo ""
    fi

    # --- Changed ---
    if [[ ${#CHANGED[@]} -gt 0 ]]; then
        echo "### Changed"
        for item in "${CHANGED[@]}"; do
            echo "$item"
        done
        echo ""
    fi

    # --- Removed ---
    if [[ ${#REMOVED[@]} -gt 0 ]]; then
        echo "### Removed"
        for item in "${REMOVED[@]}"; do
            echo "$item"
        done
        echo ""
    fi

    # --- Empty fallback ---
    if [[ ${#ADDED[@]} -eq 0 && ${#FIXED[@]} -eq 0 && ${#CHANGED[@]} -eq 0 && ${#REMOVED[@]} -eq 0 ]]; then
        echo "_No significant changes in this release._"
        echo ""
    fi

    echo "---"
    echo ""
    echo "_Generated by [generate-changelog.sh](https://github.com/nousresearch/hermes-agent) on ${DATE}_"
} > "$OUTPUT_FILE"

info "Changelog written to: ${OUTPUT_FILE}"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
total=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))
echo ""
printf "${GREEN}=== Summary ===${NC}\n"
printf "  Added:   %d\n" "${#ADDED[@]}"
printf "  Fixed:   %d\n" "${#FIXED[@]}"
printf "  Changed: %d\n" "${#CHANGED[@]}"
printf "  Removed: %d\n" "${#REMOVED[@]}"
printf "  Total:   %d\n" "$total"
echo ""

exit 0
