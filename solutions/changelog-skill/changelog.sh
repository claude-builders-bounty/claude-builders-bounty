#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag>] [--output <file>] [--version <label>]
# See README.md for details.

set -euo pipefail

# ── Defaults ────────────────────────────────────────────────────────────────
OUTPUT_FILE="CHANGELOG.md"
VERSION_LABEL="Unreleased"
SINCE_TAG=""

# ── Argument parsing ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)   SINCE_TAG="$2";    shift 2 ;;
    --output)  OUTPUT_FILE="$2";  shift 2 ;;
    --version) VERSION_LABEL="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash changelog.sh [--since <tag>] [--output <file>] [--version <label>]"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Sanity check ─────────────────────────────────────────────────────────────
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: not inside a git repository." >&2
  exit 1
fi

# ── Detect last tag ───────────────────────────────────────────────────────────
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
fi

if [[ -n "$SINCE_TAG" ]]; then
  # Validate the tag exists
  if ! git rev-parse "$SINCE_TAG" &>/dev/null; then
    echo "Error: tag '$SINCE_TAG' not found in this repository." >&2
    exit 1
  fi
  LOG_RANGE="${SINCE_TAG}..HEAD"
  echo "Generating changelog since tag: $SINCE_TAG"
else
  LOG_RANGE=""
  echo "No tags found — using full commit history."
fi

# ── Collect commits ───────────────────────────────────────────────────────────
# Format: <short-hash>|<subject>
mapfile -t COMMITS < <(git log $LOG_RANGE --pretty=format:"%h|%s" --no-merges 2>/dev/null)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
  echo "No new commits found since ${SINCE_TAG:-the beginning}. Nothing to do."
  exit 0
fi

# ── Categorise ────────────────────────────────────────────────────────────────
declare -a CAT_ADDED=()
declare -a CAT_FIXED=()
declare -a CAT_CHANGED=()
declare -a CAT_REMOVED=()

categorise_commit() {
  local hash="$1"
  local subject="$2"

  # Strip leading conventional-commit prefix and optional scope, e.g. "feat(ui): "
  local prefix
  prefix=$(echo "$subject" | grep -oiP '^[a-z]+(\([^)]+\))?!?:' || true)

  local clean_subject="$subject"
  if [[ -n "$prefix" ]]; then
    clean_subject="${subject#"$prefix"}"
    clean_subject="${clean_subject# }"   # trim leading space
  fi

  local type
  type=$(echo "$prefix" | grep -oiP '^[a-z]+' | tr '[:upper:]' '[:lower:]' || true)

  local entry="- ${clean_subject} (\`${hash}\`)"

  case "$type" in
    feat|add|feature)
      CAT_ADDED+=("$entry") ;;
    fix|bug|bugfix|hotfix)
      CAT_FIXED+=("$entry") ;;
    remove|delete|deprecate|revert)
      CAT_REMOVED+=("$entry") ;;
    change|refactor|chore|perf|style|docs|test|ci|build|wip|"")
      CAT_CHANGED+=("$entry") ;;
    *)
      CAT_CHANGED+=("$entry") ;;
  esac
}

for commit in "${COMMITS[@]}"; do
  IFS='|' read -r hash subject <<< "$commit"
  categorise_commit "$hash" "$subject"
done

# ── Build the new CHANGELOG block ─────────────────────────────────────────────
DATE=$(date +%Y-%m-%d)

build_block() {
  echo "## [${VERSION_LABEL}] - ${DATE}"
  echo ""

  if [[ ${#CAT_ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    for line in "${CAT_ADDED[@]}"; do echo "$line"; done
    echo ""
  fi

  if [[ ${#CAT_FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    for line in "${CAT_FIXED[@]}"; do echo "$line"; done
    echo ""
  fi

  if [[ ${#CAT_CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    for line in "${CAT_CHANGED[@]}"; do echo "$line"; done
    echo ""
  fi

  if [[ ${#CAT_REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    for line in "${CAT_REMOVED[@]}"; do echo "$line"; done
    echo ""
  fi
}

HEADER="# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
"

NEW_BLOCK=$(build_block)

# ── Write output ──────────────────────────────────────────────────────────────
if [[ -f "$OUTPUT_FILE" ]]; then
  # Prepend new block after the existing header (first line starting with '## ')
  TMP=$(mktemp)

  # Extract existing header lines (everything before the first '## [')
  existing_header=$(awk '/^## \[/{exit} {print}' "$OUTPUT_FILE")
  existing_body=$(awk '/^## \[/{found=1} found{print}' "$OUTPUT_FILE")

  {
    echo "$existing_header"
    echo ""
    echo "$NEW_BLOCK"
    echo "$existing_body"
  } > "$TMP"

  mv "$TMP" "$OUTPUT_FILE"
  echo "Prepended new block to existing $OUTPUT_FILE"
else
  {
    echo "$HEADER"
    echo "$NEW_BLOCK"
  } > "$OUTPUT_FILE"
  echo "Created $OUTPUT_FILE"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
TOTAL=$(( ${#CAT_ADDED[@]} + ${#CAT_FIXED[@]} + ${#CAT_CHANGED[@]} + ${#CAT_REMOVED[@]} ))
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Changelog written → $OUTPUT_FILE"
echo "  Total commits processed : $TOTAL"
echo "  Added    : ${#CAT_ADDED[@]}"
echo "  Fixed    : ${#CAT_FIXED[@]}"
echo "  Changed  : ${#CAT_CHANGED[@]}"
echo "  Removed  : ${#CAT_REMOVED[@]}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
