#!/usr/bin/env bash
#
# generate-changelog.sh — Generate structured CHANGELOG.md from git history
# Part of the claude-builders-bounty/generate-changelog skill
#
# Usage:
#   ./changelog.sh                    # Since last tag
#   ./changelog.sh --all              # Full history
#   ./changelog.sh -o docs/CHANGELOG.md  # Custom output
#   ./changelog.sh --format json      # JSON output
#   ./changelog.sh --dry-run          # Preview without writing
#

set -euo pipefail

# ─── Defaults ──────────────────────────────────────────────────────────────
OUTPUT_FILE="CHANGELOG.md"
FORMAT="markdown"
DRY_RUN=false
ALL_HISTORY=false
FROM_TAG=""
TO_TAG="HEAD"
TAG_PATTERN="v*"
CONFIG_FILE=".changelogrc"

# ─── Colors (for terminal output) ──────────────────────────────────────────
if [[ -t 1 ]] && [[ "${TERM:-}" != "dumb" ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED='' GREEN='' YELLOW='' BLUE='' NC=''
fi

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }

# ─── Help ──────────────────────────────────────────────────────────────────
show_help() {
    cat <<'EOF'
Usage: changelog.sh [OPTIONS]

Generate a structured CHANGELOG.md from git history.

Options:
  -o, --output FILE       Output file path (default: CHANGELOG.md)
  -f, --format FORMAT     Output format: markdown, json, text (default: markdown)
  --all                   Generate from full history (ignore tags)
  --from TAG              Start from this tag (inclusive)
  --to TAG                End at this tag (default: HEAD)
  --tag-pattern PATTERN   Git tag pattern to find last tag (default: v*)
  -c, --config FILE       Config file path (default: .changelogrc)
  --dry-run               Preview output without writing to file
  -h, --help              Show this help

Examples:
  changelog.sh                           # Since last v* tag
  changelog.sh --all                     # Full history
  changelog.sh -o docs/CHANGELOG.md      # Custom output
  changelog.sh --format json             # JSON for tooling
  changelog.sh --dry-run                 # Preview
  changelog.sh --from v1.0.0 --to v2.0.0 # Specific range

Config file (.changelogrc):
  [output]
  path = CHANGELOG.md
  format = markdown

  [categories]
  custom_added = feat,feature,add
  custom_fixed = fix,bugfix,hotfix
  custom_changed = refactor,perf,style,improve
  custom_removed = remove,del,delete

  [git]
  tag_pattern = v*
  range = auto
EOF
}

# ─── Parse Args ────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output) OUTPUT_FILE="$2"; shift 2 ;;
        -f|--format) FORMAT="$2"; shift 2 ;;
        --all) ALL_HISTORY=true; shift ;;
        --from) FROM_TAG="$2"; shift 2 ;;
        --to) TO_TAG="$2"; shift 2 ;;
        --tag-pattern) TAG_PATTERN="$2"; shift 2 ;;
        -c|--config) CONFIG_FILE="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        -h|--help) show_help; exit 0 ;;
        *) log_error "Unknown option: $1"; show_help; exit 1 ;;
    esac
done

# ─── Load Config ───────────────────────────────────────────────────────────
if [[ -f "$CONFIG_FILE" ]]; then
    log_info "Loading config from $CONFIG_FILE"
    while IFS='=' read -r key value; do
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        case "$key" in
            path) OUTPUT_FILE="$value" ;;
            format) FORMAT="$value" ;;
            custom_added) CUSTOM_ADDED="$value" ;;
            custom_fixed) CUSTOM_FIXED="$value" ;;
            custom_changed) CUSTOM_CHANGED="$value" ;;
            custom_removed) CUSTOM_REMOVED="$value" ;;
            tag_pattern) TAG_PATTERN="$value" ;;
        esac
    done < <(grep -E '^\s*[^#;]' "$CONFIG_FILE" | sed 's/\s*[#;].*$//' | grep '=')
fi

# ─── Category Patterns (Conventional Commits) ──────────────────────────────
ADDED_PREFIXES="${CUSTOM_ADDED:-feat,feature,add}"
FIXED_PREFIXES="${CUSTOM_FIXED:-fix,bugfix,hotfix}"
CHANGED_PREFIXES="${CUSTOM_CHANGED:-refactor,perf,style,improve}"
REMOVED_PREFIXES="${CUSTOM_REMOVED:-remove,del,delete}"

to_regex() { echo "$1" | sed 's/,/|/g'; }
ADDED_RE="^($(to_regex "$ADDED_PREFIXES")):"
FIXED_RE="^($(to_regex "$FIXED_PREFIXES")):"
CHANGED_RE="^($(to_regex "$CHANGED_PREFIXES")):"
REMOVED_RE="^($(to_regex "$REMOVED_PREFIXES")):"

# ─── Git Helpers ──────────────────────────────────────────────────────────

get_last_tag() {
    git describe --tags --match "$TAG_PATTERN" --abbrev=0 2>/dev/null || echo ""
}

get_commits() {
    local range="$1"
    git log "$range" --pretty=format:"%h|%s|%b" --no-merges
}

categorize_commit() {
    local subject="$1"
    if [[ "$subject" =~ $ADDED_RE ]]; then
        echo "Added"
    elif [[ "$subject" =~ $FIXED_RE ]]; then
        echo "Fixed"
    elif [[ "$subject" =~ $REMOVED_RE ]]; then
        echo "Removed"
    else
        echo "Changed"
    fi
}

# ─── Determine Commit Range ────────────────────────────────────────────────
if [[ -n "$FROM_TAG" ]]; then
    RANGE="${FROM_TAG}..${TO_TAG}"
    log_info "Using explicit range: $RANGE"
elif [[ "$ALL_HISTORY" == true ]]; then
    RANGE="${TO_TAG}"
    log_info "Using full history"
else
    LAST_TAG=$(get_last_tag)
    if [[ -n "$LAST_TAG" ]]; then
        RANGE="${LAST_TAG}..${TO_TAG}"
        log_info "Last tag: $LAST_TAG -> Range: $RANGE"
    else
        RANGE="${TO_TAG}"
        log_warn "No tags found matching '$TAG_PATTERN' -- using full history"
    fi
fi

# ─── Fetch and Categorize Commits ─────────────────────────────────────────
log_info "Fetching commits..."

declare -a ADDED_COMMITS=()
declare -a FIXED_COMMITS=()
declare -a CHANGED_COMMITS=()
declare -a REMOVED_COMMITS=()

while IFS='|' read -r hash subject body; do
    [[ -z "$hash" ]] && continue
    category=$(categorize_commit "$subject")
    remote_url=$(git remote get-url origin 2>/dev/null | sed -E 's|^https://github\.com/||; s|^git@github\.com:||; s|\.git$||')
    entry="  - $subject ([$hash](https://github.com/$remote_url/commit/$hash))"
    case "$category" in
        Added) ADDED_COMMITS+=("$entry") ;;
        Fixed) FIXED_COMMITS+=("$entry") ;;
        Changed) CHANGED_COMMITS+=("$entry") ;;
        Removed) REMOVED_COMMITS+=("$entry") ;;
    esac
done < <(get_commits "$RANGE")

TOTAL_COMMITS=$((${#ADDED_COMMITS[@]} + ${#FIXED_COMMITS[@]} + ${#CHANGED_COMMITS[@]} + ${#REMOVED_COMMITS[@]}))
log_ok "Processed $TOTAL_COMMITS commits"

# ─── Generate Version Header ───────────────────────────────────────────────
if [[ -n "$FROM_TAG" ]]; then
    VERSION="$TO_TAG"
elif [[ "$ALL_HISTORY" == true ]] || [[ -z "$LAST_TAG" ]]; then
    VERSION="Unreleased"
else
    VERSION="$TO_TAG"
fi

DATE=$(date '+%Y-%m-%d')
HEADER="## [$VERSION] - $DATE"

# ─── Format Output ─────────────────────────────────────────────────────────
generate_markdown() {
    cat <<EOF
# CHANGELOG

$HEADER

EOF

    if [[ ${#ADDED_COMMITS[@]} -gt 0 ]]; then
        echo "### Added"
        printf '%s\n' "${ADDED_COMMITS[@]}"
        echo
    fi

    if [[ ${#FIXED_COMMITS[@]} -gt 0 ]]; then
        echo "### Fixed"
        printf '%s\n' "${FIXED_COMMITS[@]}"
        echo
    fi

    if [[ ${#CHANGED_COMMITS[@]} -gt 0 ]]; then
        echo "### Changed"
        printf '%s\n' "${CHANGED_COMMITS[@]}"
        echo
    fi

    if [[ ${#REMOVED_COMMITS[@]} -gt 0 ]]; then
        echo "### Removed"
        printf '%s\n' "${REMOVED_COMMITS[@]}"
        echo
    fi

    if [[ ${#ADDED_COMMITS[@]} -eq 0 && ${#FIXED_COMMITS[@]} -eq 0 && ${#CHANGED_COMMITS[@]} -eq 0 && ${#REMOVED_COMMITS[@]} -eq 0 ]]; then
        echo "*No changes in this range.*"
        echo
    fi

    echo "---"
    echo "Generated by [generate-changelog](https://github.com/claude-builders-bounty/claude-builders-bounty/tree/main/skills/generate-changelog) on $DATE"
}

generate_json() {
    python3 -c "
import json, sys
added = [c.strip() for c in '''${ADDED_COMMITS[*]}'''.split('\n') if c.strip()]
fixed = [c.strip() for c in '''${FIXED_COMMITS[*]}'''.split('\n') if c.strip()]
changed = [c.strip() for c in '''${CHANGED_COMMITS[*]}'''.split('\n') if c.strip()]
removed = [c.strip() for c in '''${REMOVED_COMMITS[*]}'''.split('\n') if c.strip()]
data = {'version': '$VERSION', 'date': '$DATE', 'added': added, 'fixed': fixed, 'changed': changed, 'removed': removed}
json.dump(data, sys.stdout, indent=2)
"
}

generate_text() {
    echo "CHANGELOG"
    echo "========"
    echo
    echo "$HEADER"
    echo
    if [[ ${#ADDED_COMMITS[@]} -gt 0 ]]; then
        echo "Added:"
        printf '  %s\n' "${ADDED_COMMITS[@]}"
    fi
    if [[ ${#FIXED_COMMITS[@]} -gt 0 ]]; then
        echo "Fixed:"
        printf '  %s\n' "${FIXED_COMMITS[@]}"
    fi
    if [[ ${#CHANGED_COMMITS[@]} -gt 0 ]]; then
        echo "Changed:"
        printf '  %s\n' "${CHANGED_COMMITS[@]}"
    fi
    if [[ ${#REMOVED_COMMITS[@]} -gt 0 ]]; then
        echo "Removed:"
        printf '  %s\n' "${REMOVED_COMMITS[@]}"
    fi
}

# ─── Output ────────────────────────────────────────────────────────────────
if [[ "$DRY_RUN" == true ]]; then
    log_info "DRY RUN - Preview ($FORMAT):"
    echo "------------------------------"
    case "$FORMAT" in
        markdown) generate_markdown ;;
        json) generate_json ;;
        text) generate_text ;;
        *) log_error "Unknown format: $FORMAT"; exit 1 ;;
    esac
    echo "------------------------------"
    log_info "Would write to: $OUTPUT_FILE"
    exit 0
fi

mkdir -p "$(dirname "$OUTPUT_FILE")"

case "$FORMAT" in
    markdown) generate_markdown > "$OUTPUT_FILE" ;;
    json) generate_json > "$OUTPUT_FILE" ;;
    text) generate_text > "$OUTPUT_FILE" ;;
    *) log_error "Unknown format: $FORMAT"; exit 1 ;;
esac

log_ok "Changelog written to $OUTPUT_FILE"