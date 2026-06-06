#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Bounty: $50 — https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
#
# Usage:
#   bash changelog.sh                    # writes CHANGELOG.md
#   bash changelog.sh --output RELEASE.md
#   bash changelog.sh --since v1.0.0     # specify a ref instead of last tag

set -euo pipefail

VERSION=""
OUTPUT="CHANGELOG.md"
SINCE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output|-o) OUTPUT="$2"; shift 2 ;;
    --since|-s)  SINCE="$2";  shift 2 ;;
    --version|-v) VERSION="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Determine "since" ref ───────────────────────────────────────────
if [[ -z "$SINCE" ]]; then
  SINCE="$(git describe --tags --abbrev=0 2>/dev/null || echo "")"
fi
if [[ -z "$SINCE" ]]; then
  SINCE="$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")"
fi
if [[ -z "$SINCE" ]]; then
  echo "❌ No commits found in this repository."
  exit 1
fi

# ── Derive version ───────────────────────────────────────────────────
if [[ -z "$VERSION" ]]; then
  VERSION="$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")"
fi

# ── Gather commits ───────────────────────────────────────────────────
COMMITS_RAW="$(git log "$SINCE..HEAD" --format="@@@%s|||%an|||%ai" --no-merges 2>/dev/null || true)"

if [[ -z "$COMMITS_RAW" ]]; then
  echo "ℹ️  No new commits since ${SINCE}."
  exit 0
fi

# ── Categorization helpers ───────────────────────────────────────────

# classify: returns "added"|"fixed"|"changed"|"removed"|"other"
classify() {
  local msg="$1"
  local prefix="${msg%%:*}"       # "feat(api)" from "feat(api): message"
  prefix="${prefix%%\(*}"         # "feat" (strip scope parens)
  prefix="$(echo "$prefix" | tr '[:upper:]' '[:lower:]')"

  case "$prefix" in
    feat|feature|add|new|implement|create) echo "added" ;;
    fix|bugfix|hotfix|bug|patch|repair|correct) echo "fixed" ;;
    refactor|update|change|modify|improve|perf|optimize|upgrade|chore|ci|build|docs|doc|style|test|security) echo "changed" ;;
    remove|delete|deprecate|drop|clean|revert) echo "removed" ;;
    *) echo "other" ;;
  esac
}

# clean_msg: strip conventional-commit prefix, capitalize first letter
clean_msg() {
  local raw="$1"
  # Strip "type(scope): " or "type: " prefix
  local cleaned
  cleaned="$(echo "$raw" | sed -E 's/^[a-z]+(\([^)]*\))?:[[:space:]]*//i')"
  if [[ -z "$cleaned" ]]; then cleaned="$raw"; fi
  # Capitalize first letter (bash-native, works on macOS)
  local first rest
  first="$(echo "${cleaned:0:1}" | tr '[:lower:]' '[:upper:]')"
  rest="${cleaned:1}"
  echo "${first}${rest}"
}

# ── Categorize commits ───────────────────────────────────────────────
declare -a CAT_ADDED CAT_FIXED CAT_CHANGED CAT_REMOVED CAT_OTHER

while IFS= read -r entry; do
  [[ -z "$entry" ]] && continue
  msg="${entry%%|||*}"
  msg="${msg#@@@}"
  cat="$(classify "$msg")"
  formatted="$(clean_msg "$msg")"
  item="- ${formatted}"

  case "$cat" in
    added)   CAT_ADDED+=("$item") ;;
    fixed)   CAT_FIXED+=("$item") ;;
    changed) CAT_CHANGED+=("$item") ;;
    removed) CAT_REMOVED+=("$item") ;;
    *)       CAT_OTHER+=("$item") ;;
  esac
done <<< "$COMMITS_RAW"

# ── Build CHANGELOG ──────────────────────────────────────────────────
DATE="$(date +%Y-%m-%d)"
{
  echo "# Changelog"
  echo
  echo "## [${VERSION}] - ${DATE}"
  echo

  section() {
    local heading="$1" emoji="$2"
    shift 2
    if [[ $# -gt 0 ]]; then
      echo "### ${emoji} ${heading}"
      echo
      for item in "$@"; do echo "$item"; done
      echo
    fi
  }

  section "Added"   "✨" "${CAT_ADDED[@]+"${CAT_ADDED[@]}"}"
  section "Fixed"   "🐛" "${CAT_FIXED[@]+"${CAT_FIXED[@]}"}"
  section "Changed" "🔧" "${CAT_CHANGED[@]+"${CAT_CHANGED[@]}"}"
  section "Removed" "🗑️" "${CAT_REMOVED[@]+"${CAT_REMOVED[@]}"}"
  section "Other"   "🔹" "${CAT_OTHER[@]+"${CAT_OTHER[@]}"}"
} > "$OUTPUT"

TOTAL=$((${#CAT_ADDED[@]}+${#CAT_FIXED[@]}+${#CAT_CHANGED[@]}+${#CAT_REMOVED[@]}+${#CAT_OTHER[@]}))
echo "✅ CHANGELOG generated → ${OUTPUT}"
echo "   ${#CAT_ADDED[@]} added, ${#CAT_FIXED[@]} fixed, ${#CAT_CHANGED[@]} changed, ${#CAT_REMOVED[@]} removed, ${#CAT_OTHER[@]} other (${TOTAL} total)"
