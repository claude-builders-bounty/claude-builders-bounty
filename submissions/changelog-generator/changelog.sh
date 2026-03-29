#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Bounty #1: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
#
# Usage:
#   bash changelog.sh                    # Full changelog from all tags
#   bash changelog.sh --since v1.2.0     # Since a specific tag
#   bash changelog.sh --output CHANGES.md
#
# Requirements: git, bash 4+

set -euo pipefail

# ---------------------------------------------------------------------------
# Config / defaults
# ---------------------------------------------------------------------------
OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
REPO_URL=""
DRY_RUN=false

# ---------------------------------------------------------------------------
# Parse args
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output|-o) OUTPUT_FILE="$2"; shift 2 ;;
    --since|-s)  SINCE_TAG="$2"; shift 2 ;;
    --dry-run)   DRY_RUN=true; shift ;;
    --help|-h)
      echo "Usage: bash changelog.sh [--output FILE] [--since TAG] [--dry-run]"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
git_ok() {
  git rev-parse --is-inside-work-tree &>/dev/null
}

get_latest_tag() {
  git describe --tags --abbrev=0 2>/dev/null || echo ""
}

get_previous_tag() {
  local current="$1"
  git describe --tags --abbrev=0 "${current}^" 2>/dev/null || echo ""
}

get_repo_url() {
  local remote
  remote=$(git remote get-url origin 2>/dev/null || echo "")
  # Convert SSH to HTTPS
  remote="${remote/git@github.com:/https://github.com/}"
  remote="${remote%.git}"
  echo "$remote"
}

categorize_commit() {
  local msg="$1"
  local lower
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  # Conventional commits + common patterns
  if echo "$lower" | grep -qE '^(feat|add|new|implement|create)[:(]'; then
    echo "Added"
  elif echo "$lower" | grep -qE '^(fix|bug|hotfix|patch|resolve|revert)[:(]'; then
    echo "Fixed"
  elif echo "$lower" | grep -qE '^(refactor|chore|perf|improve|update|change|bump|upgrade|rename|move)[:(]'; then
    echo "Changed"
  elif echo "$lower" | grep -qE '^(remove|delete|drop|deprecate|clean)[:(]'; then
    echo "Removed"
  # Fallback: scan message content
  elif echo "$lower" | grep -qE '\b(add|implement|introduce|support|enable|create)\b'; then
    echo "Added"
  elif echo "$lower" | grep -qE '\b(fix|repair|resolve|solve|correct|patch)\b'; then
    echo "Fixed"
  elif echo "$lower" | grep -qE '\b(remove|delete|drop|clean|deprecate)\b'; then
    echo "Removed"
  else
    echo "Changed"
  fi
}

format_commit_line() {
  local hash="$1"
  local msg="$2"
  local repo="$3"

  # Strip conventional commit prefix (feat: / fix(scope): etc.)
  local clean_msg
  clean_msg=$(echo "$msg" | sed -E 's/^[a-z]+(\([^)]+\))?!?: //')

  if [[ -n "$repo" ]]; then
    local short_hash="${hash:0:7}"
    echo "- ${clean_msg} ([${short_hash}](${repo}/commit/${hash}))"
  else
    echo "- ${clean_msg} (${hash:0:7})"
  fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  if ! git_ok; then
    echo "Error: not inside a git repository." >&2
    exit 1
  fi

  REPO_URL=$(get_repo_url)

  # Determine the range to scan
  local latest_tag
  latest_tag=$(get_latest_tag)

  if [[ -n "$SINCE_TAG" ]]; then
    local range="${SINCE_TAG}..HEAD"
    local version_header="${latest_tag:-Unreleased}"
    local date_str
    date_str=$(date +"%Y-%m-%d")
  elif [[ -n "$latest_tag" ]]; then
    local range="${latest_tag}..HEAD"
    local version_header="Unreleased"
    local date_str
    date_str=$(date +"%Y-%m-%d")
  else
    # No tags — generate full history
    local range="HEAD"
    local version_header="Unreleased"
    local date_str
    date_str=$(date +"%Y-%m-%d")
  fi

  # Collect commits
  local commits
  if [[ "$range" == "HEAD" ]]; then
    commits=$(git log --pretty=format:"%H %s" --no-merges 2>/dev/null || echo "")
  else
    commits=$(git log "${range}" --pretty=format:"%H %s" --no-merges 2>/dev/null || echo "")
  fi

  if [[ -z "$commits" ]]; then
    echo "No commits found in range. Nothing to generate."
    exit 0
  fi

  # Categorize commits
  declare -A categories
  categories["Added"]=""
  categories["Fixed"]=""
  categories["Changed"]=""
  categories["Removed"]=""

  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local hash="${line%% *}"
    local msg="${line#* }"
    local category
    category=$(categorize_commit "$msg")
    local entry
    entry=$(format_commit_line "$hash" "$msg" "$REPO_URL")
    categories["$category"]+="${entry}"$'\n'
  done <<< "$commits"

  # Build changelog block
  local block=""
  block+="## [${version_header}] — ${date_str}"$'\n\n'

  for cat in Added Fixed Changed Removed; do
    if [[ -n "${categories[$cat]}" ]]; then
      block+="### ${cat}"$'\n'
      block+="${categories[$cat]}"$'\n'
    fi
  done

  # Dry run: just print
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "$block"
    exit 0
  fi

  # Write / prepend to output file
  if [[ -f "$OUTPUT_FILE" ]]; then
    # Prepend to existing changelog
    local tmp
    tmp=$(mktemp)
    # Find insertion point: after header (# Changelog line) or at top
    if head -5 "$OUTPUT_FILE" | grep -q "^# Changelog\|^# CHANGELOG"; then
      awk -v block="$block" '
        /^## \[/ && !inserted {
          print block
          inserted=1
        }
        { print }
      ' "$OUTPUT_FILE" > "$tmp"
      # If no existing version block, append after header
      if ! grep -q "^## " "$tmp" 2>/dev/null || diff -q "$tmp" "$OUTPUT_FILE" &>/dev/null; then
        head -2 "$OUTPUT_FILE" > "$tmp"
        echo "" >> "$tmp"
        echo "$block" >> "$tmp"
        tail -n +3 "$OUTPUT_FILE" >> "$tmp"
      fi
    else
      # Prepend entirely
      { echo "$block"; cat "$OUTPUT_FILE"; } > "$tmp"
    fi
    mv "$tmp" "$OUTPUT_FILE"
  else
    # Create new CHANGELOG.md
    {
      echo "# Changelog"
      echo ""
      echo "All notable changes to this project are documented here."
      echo "Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)."
      echo ""
      echo "$block"
    } > "$OUTPUT_FILE"
  fi

  local count
  count=$(echo "$commits" | wc -l | tr -d ' ')
  echo "Generated ${OUTPUT_FILE} — ${count} commits categorized."

  # Also generate a tag list at bottom if tags exist
  local all_tags
  all_tags=$(git tag --sort=-version:refname 2>/dev/null | head -10 || echo "")
  if [[ -n "$all_tags" && -n "$latest_tag" ]]; then
    echo "" >> "$OUTPUT_FILE"
    echo "---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "<!-- Generated by changelog.sh on $(date -u +"%Y-%m-%dT%H:%M:%SZ") -->" >> "$OUTPUT_FILE"
  fi
}

main "$@"
