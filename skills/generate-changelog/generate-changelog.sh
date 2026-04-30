#!/usr/bin/env bash
# generate-changelog.sh
# Generates a structured CHANGELOG.md from git history since the last tag.
# Usage: bash generate-changelog.sh [output-file]
# Accepted via /generate-changelog in Claude Code (see SKILL.md)
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# ── Determine range ────────────────────────────────────────────────────────
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -z "$LAST_TAG" ]]; then
  echo "ℹ️  No tags found — generating CHANGELOG for entire history."
  RANGE="HEAD"
else
  echo "📌 Last tag: $LAST_TAG"
  RANGE="${LAST_TAG}..HEAD"
fi

COMMIT_COUNT="$(git log "$RANGE" --oneline 2>/dev/null | wc -l | tr -d ' ')"
if [[ "$COMMIT_COUNT" -eq 0 ]]; then
  echo "✅ No commits since $LAST_TAG — CHANGELOG is up to date."
  exit 0
fi

echo "🔍 Analysing $COMMIT_COUNT commits…"

# ── Categorise commits ─────────────────────────────────────────────────────
declare -a ADDED=() FIXED=() CHANGED=() REMOVED=() UNCATEGORISED=()

while IFS= read -r line; do
  hash="${line:0:7}"
  msg="${line:8}"

  lower="$(echo "$msg" | tr '[:upper:]' '[:lower:]')"

  if echo "$lower" | grep -qE "^(feat|add|new|feature)[:(!\s]"; then
    ADDED+=("- $msg ($hash)")
  elif echo "$lower" | grep -qE "^(fix|bug|hotfix|patch|resolve)[:(!\s]"; then
    FIXED+=("- $msg ($hash)")
  elif echo "$lower" | grep -qE "^(remove|delete|drop|deprecate)[:(!\s]"; then
    REMOVED+=("- $msg ($hash)")
  elif echo "$lower" | grep -qE "^(refactor|chore|perf|docs|style|ci|build|test|bump|update|change|improve|upgrade|tweak|enhance)[:(!\s]"; then
    CHANGED+=("- $msg ($hash)")
  else
    UNCATEGORISED+=("- $msg ($hash)")
  fi
done < <(git log "$RANGE" --pretty=format:"%h %s" --reverse)

# ── Write CHANGELOG ────────────────────────────────────────────────────────
TODAY="$(date +%Y-%m-%d)"
VERSION="${LAST_TAG:-Unreleased}"

{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo "Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)."
  echo ""
  echo "---"
  echo ""
  echo "## [$VERSION] — $TODAY"
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### ✨ Added"
    printf '%s\n' "${ADDED[@]}"
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### 🐛 Fixed"
    printf '%s\n' "${FIXED[@]}"
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### 🔧 Changed"
    printf '%s\n' "${CHANGED[@]}"
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### 🗑️ Removed"
    printf '%s\n' "${REMOVED[@]}"
    echo ""
  fi

  if [[ ${#UNCATEGORISED[@]} -gt 0 ]]; then
    echo "### 📝 Other"
    printf '%s\n' "${UNCATEGORISED[@]}"
    echo ""
  fi

  if [[ -n "$LAST_TAG" ]]; then
    PREV_TAG="$(git describe --tags --abbrev=0 "${LAST_TAG}^" 2>/dev/null || true)"
    if [[ -n "$PREV_TAG" ]]; then
      REMOTE="$(git remote get-url origin 2>/dev/null | sed 's/\.git$//' || true)"
      if [[ -n "$REMOTE" ]]; then
        echo "---"
        echo ""
        echo "[Full diff]($REMOTE/compare/$PREV_TAG...$LAST_TAG)"
      fi
    fi
  fi
} > "$OUTPUT"

echo "✅ CHANGELOG written to $OUTPUT"
echo "   Added: ${#ADDED[@]}  Fixed: ${#FIXED[@]}  Changed: ${#CHANGED[@]}  Removed: ${#REMOVED[@]}  Other: ${#UNCATEGORISED[@]}"
