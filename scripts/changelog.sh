#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--tag v1.0.0] [--since <ref>]
#        ./changelog.sh [--write] (overwrites CHANGELOG.md)

set -euo pipefail

# ── Config ──────────────────────────────────────────────────────────────────
SINCE=""
UNTIL="HEAD"
OUTPUT_FILE=""
CATEGORIES="Added,Fixed,Changed,Removed,Deprecated,Security"

# ── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}ℹ${NC}  $*"; }
success() { echo -e "${GREEN}✓${NC}  $*"; }
warn()    { echo -e "${YELLOW}⚠${NC}  $*"; }
error()   { echo -e "${RED}✗${NC}  $*" >&2; }

# ── Help ─────────────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
Changelog Generator — Auto-categorize git commits into structured CHANGELOG.md

Usage:
    bash changelog.sh                    Print changelog to stdout
    bash changelog.sh --write            Overwrite CHANGELOG.md in project root
    bash changelog.sh --since v1.0.0     Changelog from tag v1.0.0 to HEAD
    bash changelog.sh --since HEAD~10    Last 10 commits
    bash changelog.sh --tag v1.1.0       Set the new version tag in the header
    bash changelog.sh --output FILE      Write to specific file
    bash changelog.sh --help             Show this message

Examples:
    bash changelog.sh --write
    bash changelog.sh --since v0.5.0 --tag v0.6.0 --write
    bash changelog.sh --since $(git describe --tags --abbrev=0) --write
EOF
    exit 0
}

# ── Parse args ──────────────────────────────────────────────────────────────
NEW_TAG=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage ;;
        --since) SINCE="$2"; shift 2 ;;
        --tag) NEW_TAG="$2"; shift 2 ;;
        --write) OUTPUT_FILE="CHANGELOG.md"; shift ;;
        --output) OUTPUT_FILE="$2"; shift 2 ;;
        --until) UNTIL="$2"; shift 2 ;;
        *)
            if [[ -z "$SINCE" ]]; then
                SINCE="$1"
            elif [[ -z "$UNTIL" || "$UNTIL" == "HEAD" ]]; then
                UNTIL="$1"
            else
                error "Unknown argument: $1"
                exit 1
            fi
            shift
            ;;
    esac
done

# ── Detect project info ──────────────────────────────────────────────────────
PROJECT_NAME=""
if [[ -f package.json ]]; then
    PROJECT_NAME=$(python3 -c "import json; print(json.load(open('package.json')).get('name',''))" 2>/dev/null || echo "")
elif [[ -f pyproject.toml ]]; then
    PROJECT_NAME=$(python3 -c "
try:
    with open('pyproject.toml') as f:
        for line in f:
            if line.strip().startswith('name'):
                print(line.split('=')[1].strip().strip('\"').strip(\"'\"))
                break
except: pass
" 2>/dev/null || echo "")
elif [[ -f Cargo.toml ]]; then
    PROJECT_NAME=$(python3 -c "
try:
    with open('Cargo.toml') as f:
        for line in f:
            if line.strip().startswith('name'):
                print(line.split('=')[1].strip().strip('\"').strip(\"'\"))
                break
except: pass
" 2>/dev/null || echo "")
fi

if [[ -z "$PROJECT_NAME" ]]; then
    PROJECT_NAME=$(basename "$(pwd)")
fi

# ── Determine version ────────────────────────────────────────────────────────
if [[ -z "$NEW_TAG" ]]; then
    NEW_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.1.0")
fi

# ── Determine since ref ──────────────────────────────────────────────────────
if [[ -z "$SINCE" ]]; then
    # Find the previous tag, or use first commit
    PREV_TAG=$(git tag --sort=-version:refname | head -2 | tail -1 2>/dev/null || echo "")
    if [[ -n "$PREV_TAG" ]]; then
        SINCE="$PREV_TAG"
    else
        SINCE=$(git log --reverse --format="%H" | head -1)
    fi
fi

# ── Validate ─────────────────────────────────────────────────────────────────
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    error "Not a git repository"
    exit 1
fi

# ── Get commits ──────────────────────────────────────────────────────────────
if [[ "$SINCE" == "HEAD~"* ]]; then
    RANGE="${SINCE}..${UNTIL}"
elif [[ -n "$SINCE" ]]; then
    RANGE="${SINCE}..${UNTIL}"
else
    RANGE="HEAD"
fi

COMMITS=$(git log "$RANGE" --format="%H|%s|%an|%ai" --no-merges 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
    warn "No new commits found in range: $RANGE"
    exit 0
fi

# ── Categorize commits ──────────────────────────────────────────────────────
declare -A CAT_MAP=(
    ["Added"]=""
    ["Fixed"]=""
    ["Changed"]=""
    ["Removed"]=""
    ["Deprecated"]=""
    ["Security"]=""
)

CLASSIFY_PATTERNS=(
    "Added:^(feat|feature|add|implement|create|introduce|new):? "
    "Fixed:^(fix|bugfix|bug|patch|correct|resolve|hotfix):? "
    "Changed:^(refactor|update|change|migrate|redesign|improve|bump|upgrade|deps):? "
    "Removed:^(remove|delete|drop|deprecate):? "
    "Security:^(security|secure|auth|cve|vuln|xsrf|xss|csrf):? "
)

classify_commit() {
    local msg="$1"
    
    # Try conventional commit patterns first
    for entry in "${CLASSIFY_PATTERNS[@]}"; do
        local cat="${entry%%:*}"
        local pat="${entry#*:}"
        if [[ "$msg" =~ $pat ]]; then
            echo "$cat"
            return
        fi
    done
    
    # Keyword-based fallback
    local lmsg="${msg,,}"
    if [[ "$lmsg" =~ (add|new|feat|feature|implement|create|introduce|support) ]]; then
        echo "Added"
    elif [[ "$lmsg" =~ (fix|bug|correct|resolve|hotfix|repair|error|crash) ]]; then
        echo "Fixed"
    elif [[ "$lmsg" =~ (remove|delete|drop|deprecat|cleanup) ]]; then
        echo "Removed"
    elif [[ "$lmsg" =~ (refactor|update|change|migrate|improve|bump|upgrade|chore|move) ]]; then
        echo "Changed"
    elif [[ "$lmsg" =~ (security|vuln|cve|auth|xss|csrf|injection) ]]; then
        echo "Security"
    else
        echo "Changed"
    fi
}

# ── Process commits ──────────────────────────────────────────────────────────
while IFS='|' read -r hash msg author date; do
    [[ -z "$hash" ]] && continue
    category=$(classify_commit "$msg")
    short_hash="${hash:0:7}"
    
    # Clean up commit message (remove prefix)
    clean_msg=$(echo "$msg" | sed -E 's/^(feat|feature|fix|bugfix|refactor|chore|docs|style|test|perf|ci|build|revert)(\([^)]*\))?: //' | sed -E 's/^[A-Z][a-z]+: //')
    
    # Only add if there's a meaningful message
    if [[ -n "$clean_msg" ]]; then
        entry="- $clean_msg ([${short_hash}]($(git remote get-url origin 2>/dev/null | sed 's/\.git$//')/commit/$hash))"
        CAT_MAP["$category"]="${CAT_MAP[$category]}${entry}\n"
    fi
done <<< "$COMMITS"

# ── Get date ─────────────────────────────────────────────────────────────────
DATE=$(date +"%Y-%m-%d")

# ── Build CHANGELOG ──────────────────────────────────────────────────────────
build_changelog() {
    echo "# Changelog"
    echo ""
    echo "## [$NEW_TAG] - $DATE"
    echo ""
    
    IFS=',' read -ra cats <<< "$CATEGORIES"
    has_content=false
    
    for cat in "${cats[@]}"; do
        local content="${CAT_MAP[$cat]}"
        if [[ -n "$content" ]]; then
            has_content=true
            echo "### $cat"
            echo ""
            echo -e "$content" | sed '/^$/d'
            echo ""
        fi
    done
    
    if [[ "$has_content" == false ]]; then
        echo "_No significant changes in this release._"
        echo ""
    fi
    
    # Stats
    local total=0
    for cat in "${cats[@]}"; do
        local c="${CAT_MAP[$cat]}"
        if [[ -n "$c" ]]; then
            total=$((total + $(echo -e "$c" | grep -c '^- ')))
        fi
    done
    echo "---"
    echo "*${total} changes in this release*"
}

RESULT=$(build_changelog)

# ── Output ───────────────────────────────────────────────────────────────────
if [[ -n "$OUTPUT_FILE" ]]; then
    if [[ -f "$OUTPUT_FILE" ]]; then
        warn "$OUTPUT_FILE already exists. Appending to top..."
        # Prepend new entries to existing CHANGELOG
        local tmpfile
        tmpfile=$(mktemp)
        {
            echo "$RESULT"
            echo ""
            tail -n +4 "$OUTPUT_FILE" 2>/dev/null || true
        } > "$tmpfile"
        mv "$tmpfile" "$OUTPUT_FILE"
    else
        echo "$RESULT" > "$OUTPUT_FILE"
    fi
    success "Wrote $OUTPUT_FILE ($(echo "$RESULT" | wc -l) lines)"
else
    echo "$RESULT"
fi
