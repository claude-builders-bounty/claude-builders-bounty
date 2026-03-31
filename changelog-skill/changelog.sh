#!/usr/bin/env bash
# =============================================================================
# changelog.sh — Auto-generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag>] [--output <file>]
# =============================================================================
set -euo pipefail

# ---------- defaults ---------------------------------------------------------
OUTPUT_FILE="${OUTPUT:-CHANGELOG.md}"
SINCE_TAG=""
REPO_URL=""

# ---------- parse args -------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)   SINCE_TAG="$2"; shift 2 ;;
    --output)  OUTPUT_FILE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash changelog.sh [--since <tag>] [--output <file>]"
      echo "  --since   Start from a specific git tag (default: last tag)"
      echo "  --output  Output file path (default: CHANGELOG.md)"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ---------- detect last tag if not provided -----------------------------------
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# ---------- build git range --------------------------------------------------
if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
  SINCE_DISPLAY="since \`${SINCE_TAG}\`"
else
  RANGE="HEAD"
  SINCE_DISPLAY="(full history — no previous tag found)"
fi

# ---------- collect commits --------------------------------------------------
# Format: <short_hash> <subject>
mapfile -t COMMITS < <(git log "$RANGE" --pretty=format:"%h %s" --no-merges 2>/dev/null || true)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
  echo "No commits found ${SINCE_DISPLAY}. Nothing to generate."
  exit 0
fi

# ---------- categorise commits -----------------------------------------------
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

for line in "${COMMITS[@]}"; do
  hash="${line%% *}"
  subject="${line#* }"

  # Strip conventional-commit type prefix for display (feat: → feat)
  display="$subject"

  lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  if echo "$lower" | grep -qE '^(feat|add|new|create|implement|init)[:(\ ]|added|adds'; then
    ADDED+=("- $display (\`$hash\`)")
  elif echo "$lower" | grep -qE '^(fix|bug|patch|hotfix|resolve|close)[:(\ ]|fixed|fixes'; then
    FIXED+=("- $display (\`$hash\`)")
  elif echo "$lower" | grep -qE '^(remove|delete|drop|clean)[:(\ ]|removed|removes|deleted'; then
    REMOVED+=("- $display (\`$hash\`)")
  elif echo "$lower" | grep -qE '^(refactor|perf|style|docs|test|ci|chore|update|improve|bump|change)[:(\ ]|changed|updates'; then
    CHANGED+=("- $display (\`$hash\`)")
  else
    OTHER+=("- $display (\`$hash\`)")
  fi
done

# ---------- get repo remote URL for header -----------------------------------
REPO_URL=$(git remote get-url origin 2>/dev/null | sed 's/\.git$//' || echo "")
if echo "$REPO_URL" | grep -q "git@github.com:"; then
  REPO_URL=$(echo "$REPO_URL" | sed 's|git@github.com:|https://github.com/|')
fi

# ---------- get version / date info ------------------------------------------
CURRENT_DATE=$(date +"%Y-%m-%d")
NEXT_VERSION="Unreleased"
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [[ -n "$LATEST_TAG" ]]; then
  # Attempt to auto-bump patch version (e.g. v1.2.3 → v1.2.4)
  if [[ "$LATEST_TAG" =~ ^v?([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    MAJOR="${BASH_REMATCH[1]}"
    MINOR="${BASH_REMATCH[2]}"
    PATCH="${BASH_REMATCH[3]}"
    NEXT_VERSION="v${MAJOR}.${MINOR}.$((PATCH + 1))"
  fi
fi

# ---------- write header of CHANGELOG.md -------------------------------------
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo "Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."
  echo ""
  echo "---"
  echo ""
  echo "## [$NEXT_VERSION] — $CURRENT_DATE"
  echo ""
  echo "> Changes ${SINCE_DISPLAY}"
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
    echo "### 🔄 Changed"
    printf '%s\n' "${CHANGED[@]}"
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### 🗑️ Removed"
    printf '%s\n' "${REMOVED[@]}"
    echo ""
  fi

  if [[ ${#OTHER[@]} -gt 0 ]]; then
    echo "### 📦 Other"
    printf '%s\n' "${OTHER[@]}"
    echo ""
  fi

  echo "---"
  echo ""
  if [[ -n "$REPO_URL" && -n "$LATEST_TAG" ]]; then
    echo "[$NEXT_VERSION]: ${REPO_URL}/compare/${LATEST_TAG}...HEAD"
  fi

} > "$OUTPUT_FILE"

echo "✅ CHANGELOG written to: $OUTPUT_FILE"
echo "   Commits processed: ${#COMMITS[@]}"
echo "   Added: ${#ADDED[@]} | Fixed: ${#FIXED[@]} | Changed: ${#CHANGED[@]} | Removed: ${#REMOVED[@]} | Other: ${#OTHER[@]}"
