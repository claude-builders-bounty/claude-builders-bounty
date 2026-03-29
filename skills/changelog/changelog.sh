#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Part of the Claude Code SKILL: /generate-changelog
#
# Usage:
#   bash changelog.sh                    # uses last git tag
#   bash changelog.sh . CHANGELOG.md     # specify path and output
#   bash changelog.sh --all              # all commits, no tag
#   bash changelog.sh v1.0..v2.0        # commit range
#
# Requirements: git, bash, awk, sed, grep (standard Unix tools)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── CLI argument parsing ──────────────────────────────────────────
REPO_PATH="."
OUTPUT_FILE="CHANGELOG.md"
COMMIT_RANGE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      COMMIT_RANGE="--all"
      shift
      ;;
    --version)
      shift
      COMMIT_RANGE="${1:-}"
      shift
      ;;
    -h|--help)
      echo "Usage: bash changelog.sh [path] [output] [--all] [--version TAG]"
      echo "  path    — repo path (default: .)"
      echo "  output  — output file (default: CHANGELOG.md)"
      echo "  --all   — process all commits, ignore tags"
      echo "  --version — process commits from this tag to HEAD"
      exit 0
      ;;
    -*)
      echo "Unknown option: $1"
      exit 1
      ;;
    *)
      if [[ -z "$REPO_PATH" || "$REPO_PATH" == "." ]]; then
        REPO_PATH="$1"
      elif [[ "$OUTPUT_FILE" == "CHANGELOG.md" ]]; then
        OUTPUT_FILE="$1"
      fi
      shift
      ;;
  esac
done

cd "$REPO_PATH"

# ── Validate git repo ─────────────────────────────────────────────
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not a git repository: $REPO_PATH"
  exit 1
fi

# ── Detect commit range ───────────────────────────────────────────
if [[ -z "$COMMIT_RANGE" ]]; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -n "$LAST_TAG" ]]; then
    COMMIT_RANGE="${LAST_TAG}..HEAD"
    echo "📋 Generating changelog since tag: $LAST_TAG"
  else
    COMMIT_RANGE="-50"   # fallback to last 50 commits
    echo "📋 No tags found — using last 50 commits"
  fi
elif [[ "$COMMIT_RANGE" != "--all" ]]; then
  # User passed a tag — convert to range
  COMMIT_RANGE="${COMMIT_RANGE}..HEAD"
  echo "📋 Generating changelog since: ${COMMIT_RANGE%%..*}"
fi

# ── Fetch commits ─────────────────────────────────────────────────
if [[ "$COMMIT_RANGE" == "--all" ]]; then
  RAW_COMMITS=$(git log --format="%s" 2>/dev/null || echo "")
else
  RAW_COMMITS=$(git log "$COMMIT_RANGE" --format="%s" 2>/dev/null || echo "")
fi

if [[ -z "$RAW_COMMITS" ]]; then
  echo "⚠️  No commits found in range."
  exit 0
fi

# ── Categorize commits ───────────────────────────────────────────
declare -A CATEGORIES=(
  [Added]=""
  [Fixed]=""
  [Changed]=""
  [Removed]=""
)

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  [[ "$line" =~ ^Merge[[:space:]] ]] && continue

  CATEGORY="Changed"

  if   [[ "$line" =~ ^(feat|add)(\(.+\))?: ]];   then CATEGORY="Added"
  elif [[ "$line" =~ ^fix(\(.+\))?: ]];           then CATEGORY="Fixed"
  elif [[ "$line" =~ ^refactor!: ]];              then CATEGORY="Removed"
  elif [[ "$line" =~ ^BREAKING[[:space:]]CHANGE ]]; then CATEGORY="Removed"
  elif [[ "$line" =~ ^(chore|ci|build|deps|test|docs|style)(\(.+\))?: ]]; then CATEGORY="Changed"
  fi

  CATEGORIES[$CATEGORY]="${CATEGORIES[$CATEGORY]}- ${line}\n"
done <<< "$RAW_COMMITS"

# ── Build CHANGELOG ───────────────────────────────────────────────
TODAY=$(date +"%Y-%m-%d")

# Preserve existing content if CHANGELOG.md already has entries
if [[ -f "$OUTPUT_FILE" ]] && grep -q "^## \[" "$OUTPUT_FILE" 2>/dev/null; then
  EXISTING=$(cat "$OUTPUT_FILE")
  HEADER_PART=""
  EXISTING_PART=""
else
  EXISTING=""
  HEADER_PART=$(cat << 'HEADER'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

HEADER
)
  EXISTING_PART=""
fi

# Determine version header
if [[ -n "$LAST_TAG" ]]; then
  VERSION_HEADER="## [${LAST_TAG}] - ${TODAY}"
else
  VERSION_HEADER="## [Unreleased] - ${TODAY}"
fi

# Write new section
{
  printf '%s\n\n' "$HEADER_PART"
  printf '%s\n\n' "$VERSION_HEADER"

  for cat in Added Fixed Changed Removed; do
    if [[ -n "${CATEGORIES[$cat]}" ]]; then
      printf '### %s\n' "$cat"
      echo -e "${CATEGORIES[$cat]}"
    fi
  done

  if [[ -n "$EXISTING" ]]; then
    printf '\n%s\n' "$EXISTING_PART"
    echo "$EXISTING"
  fi
} > "${OUTPUT_FILE}.tmp"

mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

echo ""
echo "✅ CHANGELOG generated → $OUTPUT_FILE"
echo ""
echo "Categories:"
for cat in Added Fixed Changed Removed; do
  COUNT=$(echo -e "${CATEGORIES[$cat]}" | grep -c "^-" || echo "0")
  if [[ "$COUNT" -gt 0 ]]; then
    echo "  • $cat: $COUNT entries"
  fi
done
