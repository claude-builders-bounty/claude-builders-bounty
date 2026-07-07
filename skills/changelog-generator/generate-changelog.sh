#!/usr/bin/env bash
# generate-changelog.sh
# Generate a structured CHANGELOG.md from git history
# Usage: bash generate-changelog.sh [--repo PATH] [--output CHANGELOG.md]
#
# Fetches commits since the last git tag and auto-categorizes them
# into Added, Fixed, Changed, Removed, Security, Deprecated, and Other sections.

set -euo pipefail

# ─── Configuration ──────────────────────────────────────────────────────────
REPO_DIR="${1:-.}"
OUTPUT_FILE="${2:-CHANGELOG.md}"
TAG_PATTERN="${3:-v*}"
UNRELEASED_LABEL="Unreleased"

# ─── Colors for output ──────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ─── Helper Functions ───────────────────────────────────────────────────────

info()    { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; }
header()  { echo -e "\n${BLUE}━━━ $1 ━━━${NC}"; }

# ─── Validate ───────────────────────────────────────────────────────────────

if ! command -v git &>/dev/null; then
    error "Git is not installed. Please install git first."
    exit 1
fi

if [ ! -d "$REPO_DIR/.git" ] && [ ! -f "$REPO_DIR/.git" ]; then
    # Allow bare repos or submodules
    if ! git -C "$REPO_DIR" rev-parse --git-dir &>/dev/null; then
        error "Not a git repository: $REPO_DIR"
        exit 1
    fi
fi

cd "$REPO_DIR"

# ─── Detect Last Tag ────────────────────────────────────────────────────────

header "Detecting version"

LAST_TAG=""
# Portable version sort: try GNU sort -V first, fallback to numeric sort
if sort -V </dev/null 2>/dev/null; then
    LAST_TAG=$(git tag --list "$TAG_PATTERN" | sort -V | tail -1)
else
    # Portable fallback using sort -t. for dotted versions
    LAST_TAG=$(git tag --list "$TAG_PATTERN" | sort -t. -k1,1n -k2,2n -k3,3n 2>/dev/null | tail -1)
fi

if [ -n "$LAST_TAG" ]; then
    info "Last tag: $LAST_TAG"
    COMMIT_RANGE="$LAST_TAG..HEAD"
    # Portable version sort for previous tag
    if sort -V </dev/null 2>/dev/null; then
        PREVIOUS_TAG=$(git tag --list "$TAG_PATTERN" | sort -V | tail -2 | head -1)
    else
        PREVIOUS_TAG=$(git tag --list "$TAG_PATTERN" | sort -t. -k1,1n -k2,2n -k3,3n 2>/dev/null | tail -2 | head -1)
    fi
else
    warn "No tags found matching '$TAG_PATTERN'. Using all commits."
    COMMIT_RANGE="HEAD"
    LAST_TAG="v0.1.0"
    PREVIOUS_TAG=""
fi

# ─── Get Commits ────────────────────────────────────────────────────────────

header "Fetching commits"

# Get commit log: hash | subject | author | date
COMMITS=$(git log "$COMMIT_RANGE" \
    --pretty=format:"%H|||%s|||%an|||%ai" \
    --no-merges 2>/dev/null || true)

if [ -z "$COMMITS" ]; then
    warn "No commits found in range '$COMMIT_RANGE'"
    # Try fallback: all commits
    COMMITS=$(git log --pretty=format:"%H|||%s|||%an|||%ai" --no-merges 2>/dev/null | head -50 || true)
    if [ -z "$COMMITS" ]; then
        error "No commits found at all."
        exit 1
    fi
    info "Using last 50 commits as fallback"
fi

COMMIT_COUNT=$(echo "$COMMITS" | grep -c . || true)
info "Found $COMMIT_COUNT commits since last tag"

# Compute repo slug once for all commit links
REPO_NAME=$(git remote get-url origin 2>/dev/null | sed -E 's/.*github.com[:\/]([^/]+\/[^/]+)(\.git)?$/\1/' 2>/dev/null || echo "unknown/repo")

# ─── Categorize Commits ─────────────────────────────────────────────────────

header "Categorizing commits"

# Categories using conventional commit prefixes
categorize() {
    local subject="$1"
    local lower_subject
    lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

    # Remove conventional commit scope: feat(scope): message
    local clean_subject
    clean_subject=$(echo "$subject" | sed -E 's/^[a-z]+(\([^)]*\))?:\s*//i')

    # Detect breaking changes
    if echo "$lower_subject" | grep -q '!' && echo "$lower_subject" | grep -qE '^(feat|fix|refactor)!?'; then
        echo "Breaking|$clean_subject"
        return
    fi

    case "$lower_subject" in
        feat*|feature*)      echo "Added|$clean_subject" ;;
        fix*)                echo "Fixed|$clean_subject" ;;
        refactor*)           echo "Changed|$clean_subject" ;;
        chore*|build*|ci*)   echo "Changed|$clean_subject" ;;
        perf*)               echo "Changed|$clean_subject" ;;
        style*)              echo "Changed|$clean_subject" ;;
        remove*|revert*)     echo "Removed|$clean_subject" ;;
        sec*|audit*)         echo "Security|$clean_subject" ;;
        deprecat*)           echo "Deprecated|$clean_subject" ;;
        docs*)               echo "Documentation|$clean_subject" ;;
        test*)               echo "Testing|$clean_subject" ;;
        *)
            # Fallback: keyword-based matching
            if echo "$lower_subject" | grep -qE '^add|^new|^create|^implement|^support|^introduce'; then
                echo "Added|$subject"
            elif echo "$lower_subject" | grep -qE '^fix|^bug|^correct|^hotfix|^patch|^resolve'; then
                echo "Fixed|$subject"
            elif echo "$lower_subject" | grep -qE '^remove|^delete|^drop|^revert|^clean'; then
                echo "Removed|$subject"
            elif echo "$lower_subject" | grep -qE '^update|^change|^refactor|^improve|^migrate|^redesign'; then
                echo "Changed|$subject"
            elif echo "$lower_subject" | grep -qE '^bump|^upgrade|^downgrade'; then
                echo "Changed|$subject"
            elif echo "$lower_subject" | grep -qE '^doc|^readme'; then
                echo "Documentation|$subject"
            else
                echo "Other|$subject"
            fi
            ;;
    esac
}

# Initialize category arrays
BREAKING_CHANGES=()
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
SECURITY=()
DEPRECATED=()
DOCUMENTATION=()
TESTING=()
OTHER=()

while IFS= read -r line; do
    [ -z "$line" ] && continue
    # Extract using bash parameter expansion (||| separator from git log)
    rest="$line"
    hash="${rest%%|||*}"
    rest="${rest#*|||}"
    subject="${rest%%|||*}"
    rest="${rest#*|||}"
    author="${rest%%|||*}"
    rest="${rest#*|||}"
    date="${rest%% *}"

    result=$(categorize "$subject")
    category=$(echo "$result" | cut -d'|' -f1)
    message=$(echo "$result" | cut -d'|' -f2-)

    # Truncate hash for display
    short_hash=$(echo "$hash" | cut -c1-7)

    if [ "$REPO_NAME" = "unknown/repo" ]; then
        entry="- ${message} (${short_hash})"
    else
        entry="- ${message} ([${short_hash}](https://github.com/${REPO_NAME}/commit/${hash}))"
    fi

    case "$category" in
        "Breaking")
            if [ "$REPO_NAME" = "unknown/repo" ]; then
                entry="- **${message}** (${short_hash})"
            else
                entry="- **${message}** ([${short_hash}](https://github.com/${REPO_NAME}/commit/${hash}))"
            fi
            BREAKING_CHANGES+=("$entry") ;;
        "Added")      ADDED+=("$entry") ;;
        "Fixed")      FIXED+=("$entry") ;;
        "Changed")    CHANGED+=("$entry") ;;
        "Removed")    REMOVED+=("$entry") ;;
        "Security")   SECURITY+=("$entry") ;;
        "Deprecated") DEPRECATED+=("$entry") ;;
        "Documentation") DOCUMENTATION+=("$entry") ;;
        "Testing")    TESTING+=("$entry") ;;
        *)            OTHER+=("$entry") ;;
    esac
done <<< "$COMMITS"

info "Categorized: ${#ADDED[@]} Added | ${#FIXED[@]} Fixed | ${#CHANGED[@]} Changed | ${#REMOVED[@]} Removed"

# ─── Detect Version ─────────────────────────────────────────────────────────

NEXT_VERSION=""
if [ -n "$LAST_TAG" ]; then
    # Bump patch version
    NEXT_VERSION=$(echo "$LAST_TAG" | sed -E 's/v?([0-9]+)\.([0-9]+)\.([0-9]+).*$/v\1.\2.\3/' 2>/dev/null || echo "$LAST_TAG")
    if [[ "$NEXT_VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        minor=$(echo "$NEXT_VERSION" | cut -d'.' -f2)
        patch=$(echo "$NEXT_VERSION" | cut -d'.' -f3)
        patch=$((patch + 1))
        NEXT_VERSION="v$(echo "$NEXT_VERSION" | cut -d'.' -f1 | tr -d 'v').${minor}.${patch}"
    fi
else
    NEXT_VERSION="v0.1.0"
fi

# ─── Generate CHANGELOG.md ──────────────────────────────────────────────────

header "Generating CHANGELOG.md"

OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
[ "$OUTPUT_DIR" = "." ] && OUTPUT_DIR=""
TODAY=$(date +%Y-%m-%d)

cat > "$OUTPUT_FILE" << EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [${NEXT_VERSION}] - ${TODAY}

EOF

has_content=false

# Breaking Changes first (most important)
if [ ${#BREAKING_CHANGES[@]} -gt 0 ]; then
    {
        echo "### ⚠ Breaking Changes"
        echo ""
        for entry in "${BREAKING_CHANGES[@]}"; do
            echo "$entry"
        done
        echo ""
    } >> "$OUTPUT_FILE"
    has_content=true
fi

# Added
if [ ${#ADDED[@]} -gt 0 ]; then
    {
        echo "### Added"
        echo ""
        for entry in "${ADDED[@]}"; do
            echo "$entry"
        done
        echo ""
    } >> "$OUTPUT_FILE"
    has_content=true
fi

# Fixed
if [ ${#FIXED[@]} -gt 0 ]; then
    {
        echo "### Fixed"
        echo ""
        for entry in "${FIXED[@]}"; do
            echo "$entry"
        done
        echo ""
    } >> "$OUTPUT_FILE"
    has_content=true
fi

# Changed
if [ ${#CHANGED[@]} -gt 0 ]; then
    {
        echo "### Changed"
        echo ""
        for entry in "${CHANGED[@]}"; do
            echo "$entry"
        done
        echo ""
    } >> "$OUTPUT_FILE"
    has_content=true
fi

# Removed
if [ ${#REMOVED[@]} -gt 0 ]; then
    {
        echo "### Removed"
        echo ""
        for entry in "${REMOVED[@]}"; do
            echo "$entry"
        done
        echo ""
    } >> "$OUTPUT_FILE"
    has_content=true
fi

# Security
if [ ${#SECURITY[@]} -gt 0 ]; then
    {
        echo "### Security"
        echo ""
        for entry in "${SECURITY[@]}"; do
            echo "$entry"
        done
        echo ""
    } >> "$OUTPUT_FILE"
    has_content=true
fi

# Deprecated
if [ ${#DEPRECATED[@]} -gt 0 ]; then
    {
        echo "### Deprecated"
        echo ""
        for entry in "${DEPRECATED[@]}"; do
            echo "$entry"
        done
        echo ""
    } >> "$OUTPUT_FILE"
    has_content=true
fi

# Documentation
if [ ${#DOCUMENTATION[@]} -gt 0 ]; then
    {
        echo "### Documentation"
        echo ""
        for entry in "${DOCUMENTATION[@]}"; do
            echo "$entry"
        done
        echo ""
    } >> "$OUTPUT_FILE"
    has_content=true
fi

# Testing
if [ ${#TESTING[@]} -gt 0 ]; then
    {
        echo "### Testing"
        echo ""
        for entry in "${TESTING[@]}"; do
            echo "$entry"
        done
        echo ""
    } >> "$OUTPUT_FILE"
    has_content=true
fi

# Other
if [ ${#OTHER[@]} -gt 0 ]; then
    {
        echo "### Other"
        echo ""
        for entry in "${OTHER[@]}"; do
            echo "$entry"
        done
        echo ""
    } >> "$OUTPUT_FILE"
    has_content=true
fi

# If no content, add a note
if [ "$has_content" = false ]; then
    cat >> "$OUTPUT_FILE" << EOF
_No changes in this release._

EOF
fi

# Add link to previous version for comparison
if [ -n "$PREVIOUS_TAG" ] && [ -n "$NEXT_VERSION" ] && [ "$REPO_NAME" != "unknown/repo" ]; then
    cat >> "$OUTPUT_FILE" << EOF
[${NEXT_VERSION}]: https://github.com/${REPO_NAME}/compare/${PREVIOUS_TAG}...${NEXT_VERSION}
EOF
elif [ -n "$LAST_TAG" ] && [ "$REPO_NAME" != "unknown/repo" ]; then
    cat >> "$OUTPUT_FILE" << EOF
[${NEXT_VERSION}]: https://github.com/${REPO_NAME}/compare/${LAST_TAG}...${NEXT_VERSION}
EOF
fi

echo ""
info "CHANGELOG generated successfully → $(pwd)/${OUTPUT_FILE}"

# ─── Summary ────────────────────────────────────────────────────────────────

echo ""
header "Summary"
echo ""
printf "${GREEN}%-20s${NC} %s\n" "Version:" "$NEXT_VERSION"
printf "${GREEN}%-20s${NC} %s\n" "Date:" "$TODAY"
printf "${GREEN}%-20s${NC} %s\n" "Total commits:" "$COMMIT_COUNT"
printf "${GREEN}%-20s${NC} %s\n" "Added:" "${#ADDED[@]}"
printf "${GREEN}%-20s${NC} %s\n" "Fixed:" "${#FIXED[@]}"
printf "${GREEN}%-20s${NC} %s\n" "Changed:" "${#CHANGED[@]}"
printf "${GREEN}%-20s${NC} %s\n" "Removed:" "${#REMOVED[@]}"
echo ""
