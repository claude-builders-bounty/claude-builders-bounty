#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since-tag TAG] [--output FILE]
#
# Fetches commits since the last git tag (or all commits),
# auto-categorizes them into Added/Fixed/Changed/Removed,
# and outputs a properly formatted CHANGELOG.md.
#
# Dependencies: git, bash 4+

set -euo pipefail

# ─── Config ────────────────────────────────────────────────────────
OUTPUT="CHANGELOG.md"
SINCE_TAG=""
REPO_ROOT=""

# ─── Parse args ────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --since-tag) SINCE_TAG="$2"; shift 2 ;;
        --output|-o) OUTPUT="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: bash changelog.sh [--since-tag TAG] [--output FILE]"
            echo "  --since-tag TAG   Only include commits after this tag (default: last tag)"
            echo "  --output FILE     Output file (default: CHANGELOG.md)"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ─── Find repo root ────────────────────────────────────────────────
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
cd "$REPO_ROOT"

# ─── Determine range ───────────────────────────────────────────────
if [[ -z "$SINCE_TAG" ]]; then
    # Auto-detect last tag
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -n "$SINCE_TAG" ]]; then
    RANGE="${SINCE_TAG}..HEAD"
    echo "📋 Generating changelog since tag: $SINCE_TAG"
else
    RANGE="HEAD"
    # Get all commits
    RANGE=$(git rev-list --max-parents=0 HEAD)..HEAD
    echo "📋 Generating changelog for entire history"
fi

# ─── Collect commits ───────────────────────────────────────────────
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    
    hash=$(echo "$line" | cut -d' ' -f1)
    msg=$(echo "$line" | cut -d' ' -f2-)
    
    # Categorize by conventional commit prefix or keywords
    lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$lower_msg" =~ ^(feat|add|new|create|implement|support) ]]; then
        ADDED+=("$msg")
    elif [[ "$lower_msg" =~ ^(fix|bugfix|patch|resolve|correct|hotfix) ]]; then
        FIXED+=("$msg")
    elif [[ "$lower_msg" =~ ^(remove|delete|drop|deprecate|eliminate) ]]; then
        REMOVED+=("$msg")
    elif [[ "$lower_msg" =~ ^(refactor|update|improve|change|modify|rename|move|restructure|optimize|perf|chore|build|ci|style) ]]; then
        CHANGED+=("$msg")
    elif [[ "$lower_msg" =~ ^(docs|doc|readme|changelog) ]]; then
        CHANGED+=("$msg")
    else
        OTHER+=("$msg")
    fi
done < <(git log --format="%h %s" --no-merges $RANGE 2>/dev/null)

# ─── Generate CHANGELOG ───────────────────────────────────────────
DATE=$(date +%Y-%m-%d)
VERSION="${SINCE_TAG:-v0.0.0}"
# Try to get current version from tag
if [[ -n "$SINCE_TAG" ]]; then
    # Next version - just use "Unreleased"
    VERSION="Unreleased"
fi

{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [$VERSION] — $DATE"
    echo ""
    
    if [[ ${#ADDED[@]} -gt 0 ]]; then
        echo "### Added"
        for item in "${ADDED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi
    
    if [[ ${#FIXED[@]} -gt 0 ]]; then
        echo "### Fixed"
        for item in "${FIXED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi
    
    if [[ ${#CHANGED[@]} -gt 0 ]]; then
        echo "### Changed"
        for item in "${CHANGED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi
    
    if [[ ${#REMOVED[@]} -gt 0 ]]; then
        echo "### Removed"
        for item in "${REMOVED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi
    
    if [[ ${#OTHER[@]} -gt 0 ]]; then
        echo "### Other"
        for item in "${OTHER[@]}"; do
            echo "- $item"
        done
        echo ""
    fi
    
    # Append existing CHANGELOG content if present
    if [[ -f "$OUTPUT" ]]; then
        # Skip the header of existing file
        tail -n +3 "$OUTPUT" 2>/dev/null || true
    fi
    
} > "${OUTPUT}.tmp"

mv "${OUTPUT}.tmp" "$OUTPUT"

TOTAL=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#OTHER[@]}))
echo "✅ Generated $OUTPUT with $TOTAL commits"
echo "   Added: ${#ADDED[@]} | Fixed: ${#FIXED[@]} | Changed: ${#CHANGED[@]} | Removed: ${#REMOVED[@]} | Other: ${#OTHER[@]}"
