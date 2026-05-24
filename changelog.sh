#!/usr/bin/env bash
# ============================================================
# 📋 CHANGELOG Generator — generates CHANGELOG.md
# Usage: bash changelog.sh [--output FILE]
# ============================================================
set -euo pipefail

CHANGELOG="CHANGELOG.md"; REPO=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output|-o) CHANGELOG="$2"; shift 2 ;;
    --repo|-r) REPO="$2"; shift 2 ;;
    --help|-h) echo "Usage: bash changelog.sh [--output FILE] [--repo PATH]"; exit 0 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

TARGET="${REPO:-.}"; cd "$TARGET" 2>/dev/null || exit 1
git rev-parse --git-dir >/dev/null 2>&1 || { echo "❌ Not a git repo"; exit 1; }

echo "🔍 Generating for $(basename $(git rev-parse --show-toplevel))..."
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
LOG_RANGE="${LAST_TAG:-HEAD}..HEAD"; [ -z "$LAST_TAG" ] && LOG_RANGE="HEAD"

A=(); F=(); C=(); R=(); O=()
while IFS='|' read -r h s; do
  [ -z "$h" ] && continue
  ls=$(echo "$s" | tr '[:upper:]' '[:lower:]')
  echo "$ls" | grep -qE '^(add|feat|new|create|implement)' && { A+=("$s"); continue; }
  echo "$ls" | grep -qE '^(fix|bug|hotfix|patch|correct|resolve)' && { F+=("$s"); continue; }
  echo "$ls" | grep -qE '^(change|update|refactor|improve|upgrade|bump)' && { C+=("$s"); continue; }
  echo "$ls" | grep -qE '^(remove|delete|drop|deprecate|clean)' && { R+=("$s"); continue; }
  O+=("$s")
done < <(git log --reverse "$LOG_RANGE" --format="%h|%s" 2>/dev/null)

{
  echo "# Changelog"; echo ""
  echo "All notable changes will be documented here."
  echo "---"; echo "### $(date +%Y-%m-%d)"; echo ""
  [ ${#A[@]} -gt 0 ] && { echo "### 🚀 Added"; for i in "${A[@]}"; do echo "- $i"; done; echo ""; }
  [ ${#F[@]} -gt 0 ] && { echo "### 🐛 Fixed"; for i in "${F[@]}"; do echo "- $i"; done; echo ""; }
  [ ${#C[@]} -gt 0 ] && { echo "### 🔄 Changed"; for i in "${C[@]}"; do echo "- $i"; done; echo ""; }
  [ ${#R[@]} -gt 0 ] && { echo "### ❌ Removed"; for i in "${R[@]}"; do echo "- $i"; done; echo ""; }
  [ ${#O[@]} -gt 0 ] && { echo "### 📋 Other"; for i in "${O[@]}"; do echo "- $i"; done; echo ""; }
  echo "---"
  echo "*$(( ${#A[@]}+${#F[@]}+${#C[@]}+${#R[@]}+${#O[@]} )) commits since ${LAST_TAG:-the beginning}*"
} > "$CHANGELOG"
echo "✅ $CHANGELOG written (${#A[@]} Added | ${#F[@]} Fixed | ${#C[@]} Changed | ${#R[@]} Removed)"
