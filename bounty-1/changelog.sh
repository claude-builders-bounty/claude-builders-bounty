#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
# Usage: bash changelog.sh [repo_path]
#
set -euo pipefail

REPO_PATH="${1:-.}"
cd "$REPO_PATH"

# ── helpers ──────────────────────────────────────────────────────────────
bold() { printf "**%s**" "$1"; }
code() { printf "\`%s\`" "$1"; }

# ── determine range ──────────────────────────────────────────────────────
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [ -n "$LAST_TAG" ]; then
  RANGE="$LAST_TAG..HEAD"
else
  RANGE="HEAD"
fi

# ── collect commits ──────────────────────────────────────────────────────
COMMITS=$(git log "$RANGE" --pretty=format:"%H||%s" 2>/dev/null || true)
if [ -z "$COMMITS" ]; then
  echo "No commits found in range: $RANGE" >&2
  exit 0
fi

# ── version & date ───────────────────────────────────────────────────────
VERSION="${LAST_TAG:-Unreleased}"
TODAY=$(date +%Y-%m-%d)

# ── categorize ───────────────────────────────────────────────────────────
declare -a ADDED FIXED CHANGED REMOVED

categorize() {
  local msg="$1"
  local lower="${msg,,}"

  # prefix-based
  case "$lower" in
    feat:*|feature:*) ADDED+=("$msg"); return ;;
    fix:*|bugfix:*|hotfix:*) FIXED+=("$msg"); return ;;
    chore:*|refactor:*|perf:*|build:*|ci:*) CHANGED+=("$msg"); return ;;
    docs:*|doc:*) CHANGED+=("$msg"); return ;;
    remove:*|delete:*|revert:*) REMOVED+=("$msg"); return ;;
  esac

  # keyword-based fallback
  if [[ "$lower" =~ (add|create|introduce|implement|new ) ]]; then
    ADDED+=("$msg"); return
  fi
  if [[ "$lower" =~ (fix|repair|resolve|patch|correct) ]]; then
    FIXED+=("$msg"); return
  fi
  if [[ "$lower" =~ (change|update|improve|rename|move|upgrade|migrate|bump) ]]; then
    CHANGED+=("$msg"); return
  fi
  if [[ "$lower" =~ (remove|delete|drop|strip|eliminate) ]]; then
    REMOVED+=("$msg"); return
  fi

  # default → Changed
  CHANGED+=("$msg")
}

while IFS= read -r line; do
  [ -z "$line" ] && continue
  msg="${line#*||}"
  categorize "$msg"
done <<< "$COMMITS"

# ── render section helper ────────────────────────────────────────────────
render_section() {
  local title="$1"
  shift
  local items=("$@")
  if [ ${#items[@]} -eq 0 ]; then return; fi
  echo "### $title"
  echo ""
  for item in "${items[@]}"; do
    # strip common prefixes for cleaner display
    clean="${item#feat: }"
    clean="${clean#feature: }"
    clean="${clean#fix: }"
    clean="${clean#bugfix: }"
    clean="${clean#hotfix: }"
    clean="${clean#chore: }"
    clean="${clean#refactor: }"
    clean="${clean#perf: }"
    clean="${clean#build: }"
    clean="${clean#ci: }"
    clean="${clean#docs: }"
    clean="${clean#doc: }"
    clean="${clean#remove: }"
    clean="${clean#delete: }"
    clean="${clean#revert: }"
    echo "- $clean"
  done
  echo ""
}

# ── output ───────────────────────────────────────────────────────────────
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "## [$VERSION] - $TODAY"
  echo ""

  render_section "Added"    "${ADDED[@]:-}"
  render_section "Fixed"    "${FIXED[@]:-}"
  render_section "Changed"  "${CHANGED[@]:-}"
  render_section "Removed"  "${REMOVED[@]:-}"

  # footer with commit count
  TOTAL=$(echo "$COMMITS" | wc -l)
  echo "---"
  echo ""
  echo "_Generated from $TOTAL commits since ${LAST_TAG:-project inception}._"
} > CHANGELOG.md

echo "✅  CHANGELOG.md generated ($TOTAL commits, $VERSION, $TODAY)"
