#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# generate-changelog.sh — Structured CHANGELOG generator from git history
# =============================================================================
# Usage: bash changelog.sh [--repo PATH] [--output FILE] [--from TAG] [--to REF]
# =============================================================================

VERSION="1.0.0"
REPO_PATH="."
OUTPUT_FILE="CHANGELOG.md"
FROM_TAG=""
TO_REF="HEAD"
VERBOSE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    cat <<EOF
generate-changelog v${VERSION}

Usage:
  bash changelog.sh [OPTIONS]

Options:
  --repo PATH       Path to git repository (default: current directory)
  --output FILE     Output file path (default: CHANGELOG.md)
  --from TAG        Start from this tag (default: auto-detect last tag)
  --to REF          End at this ref (default: HEAD)
  --all             Include all commits (no tag filter)
  --version VER     Version header for the changelog
  --verbose         Show detailed output
  -h, --help        Show this help message

Examples:
  bash changelog.sh
  bash changelog.sh --repo /path/to/project --output CHANGES.md
  bash changelog.sh --from v1.0.0 --to v2.0.0
  bash changelog.sh --all --version "2.0.0"

Conventional Commit Types:
  feat:     New feature (Added)
  fix:      Bug fix (Fixed)
  docs:     Documentation only (Changed)
  style:    Formatting, no code change (Changed)
  refactor: Code change that neither fixes a bug nor adds a feature (Changed)
  perf:     Performance improvement (Changed)
  test:     Adding or updating tests (Changed)
  build:    Build system or dependencies (Changed)
  ci:       CI configuration (Changed)
  chore:    Other changes (Changed)
  revert:   Reverts a previous commit (Removed)

Non-conventional commits are categorized as "Changed".
EOF
}

log_info() {
    $VERBOSE && echo -e "${BLUE}[INFO]${NC} $1" || true
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

die() {
    log_error "$1"
    exit 1
}

# Parse arguments
VERSION_HEADER=""
INCLUDE_ALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --repo)
            REPO_PATH="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --from)
            FROM_TAG="$2"
            shift 2
            ;;
        --to)
            TO_REF="$2"
            shift 2
            ;;
        --all)
            INCLUDE_ALL=true
            shift
            ;;
        --version)
            VERSION_HEADER="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown option: $1. Use --help for usage."
            ;;
    esac
done

# Validate repository
cd "$REPO_PATH" || die "Cannot access directory: $REPO_PATH"
[[ -d .git ]] || die "Not a git repository: $REPO_PATH"

# Get repo name
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
log_info "Repository: $REPO_NAME"

# Auto-detect from tag if not specified
if [[ -z "$FROM_TAG" ]] && ! $INCLUDE_ALL; then
    FROM_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -z "$FROM_TAG" ]]; then
        log_warn "No tags found. Including all commits."
        INCLUDE_ALL=true
    else
        log_info "Latest tag: $FROM_TAG"
    fi
fi

# Determine date range
if [[ -n "$FROM_TAG" ]]; then
    FROM_DATE=$(git log -1 --format="%as" "$FROM_TAG" 2>/dev/null || echo "")
    RANGE_DESC="since $FROM_TAG"
else
    FROM_DATE=""
    RANGE_DESC="(all time)"
fi

log_info "Generating changelog $RANGE_DESC..."

# Get commits
if $INCLUDE_ALL; then
    COMMITS=$(git log --pretty=format:"%H|%s|%an|%ad" --date=short "$TO_REF" 2>/dev/null || echo "")
elif [[ -n "$FROM_TAG" ]]; then
    COMMITS=$(git log --pretty=format:"%H|%s|%an|%ad" --date=short "${FROM_TAG}..${TO_REF}" 2>/dev/null || echo "")
else
    COMMITS=$(git log --pretty=format:"%H|%s|%an|%ad" --date=short "$TO_REF" 2>/dev/null || echo "")
fi

if [[ -z "$COMMITS" ]]; then
    log_warn "No commits found in the specified range."
    echo "# Changelog" > "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "No changes recorded." >> "$OUTPUT_FILE"
    log_success "Empty changelog written to $OUTPUT_FILE"
    exit 0
fi

# Initialize arrays for categorized commits
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

# Categorize commits
while IFS='|' read -r hash message author date; do
    [[ -z "$hash" ]] && continue

    short_hash="${hash:0:7}"
    entry="- $message ($short_hash, $author, $date)"

    # Parse conventional commit prefix
    if [[ "$message" =~ ^feat(\(.+\))?!?:\ (.+)$ ]]; then
        ADDED+=("$entry")
    elif [[ "$message" =~ ^fix(\(.+\))?!?:\ (.+)$ ]]; then
        FIXED+=("$entry")
    elif [[ "$message" =~ ^revert(\(.+\))?!?:\ (.+)$ ]]; then
        REMOVED+=("$entry")
    elif [[ "$message" =~ ^(docs|style|refactor|perf|test|build|ci|chore)(\(.+\))?!?:\ (.+)$ ]]; then
        CHANGED+=("$entry")
    else
        CHANGED+=("$entry")
    fi
done <<< "$COMMITS"

# Generate date for header
GENERATED_DATE=$(date +%Y-%m-%d)

# Determine version header
if [[ -n "$VERSION_HEADER" ]]; then
    HEADER="## [$VERSION_HEADER] - $GENERATED_DATE"
elif [[ -n "$FROM_TAG" ]]; then
    HEADER="## [Unreleased] - $GENERATED_DATE"
else
    HEADER="## [Initial] - $GENERATED_DATE"
fi

# Write changelog
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),"
    echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
    echo ""
    echo "$HEADER"
    echo ""

    if [[ ${#ADDED[@]} -gt 0 ]]; then
        echo "### Added"
        echo ""
        for entry in "${ADDED[@]}"; do
            echo "$entry"
        done
        echo ""
    fi

    if [[ ${#FIXED[@]} -gt 0 ]]; then
        echo "### Fixed"
        echo ""
        for entry in "${FIXED[@]}"; do
            echo "$entry"
        done
        echo ""
    fi

    if [[ ${#CHANGED[@]} -gt 0 ]]; then
        echo "### Changed"
        echo ""
        for entry in "${CHANGED[@]}"; do
            echo "$entry"
        done
        echo ""
    fi

    if [[ ${#REMOVED[@]} -gt 0 ]]; then
        echo "### Removed"
        echo ""
        for entry in "${REMOVED[@]}"; do
            echo "$entry"
        done
        echo ""
    fi

    # Summary
    total=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]}))
    echo "---"
    echo ""
    echo "*Generated on $GENERATED_DATE by generate-changelog v${VERSION}*"
    echo "*Total commits: $total (Added: ${#ADDED[@]}, Fixed: ${#FIXED[@]}, Changed: ${#CHANGED[@]}, Removed: ${#REMOVED[@]})*"

} > "$OUTPUT_FILE"

log_success "Changelog generated: $OUTPUT_FILE"
log_info "  Added:    ${#ADDED[@]} commits"
log_info "  Fixed:    ${#FIXED[@]} commits"
log_info "  Changed:  ${#CHANGED[@]} commits"
log_info "  Removed:  ${#REMOVED[@]} commits"
log_info "  Total:    $total commits"
