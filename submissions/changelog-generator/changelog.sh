#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output-file]
#   If output-file is omitted, writes to CHANGELOG.md
#
# Auto-categorizes commits since the last git tag into:
#   Added, Fixed, Changed, Removed, Security, Deprecated
# Falls back to listing all commits if no tags exist.

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_URL="${2:-}"

# ──  Detect repository info ──────────────────────────────────────
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not inside a git repository" >&2
  exit 1
fi

# Try to get remote origin URL for linking commits
if [[ -z "$REPO_URL" ]]; then
  REMOTE=$(git remote get-url origin 2>/dev/null || true)
  if echo "$REMOTE" | grep -qE '^https://github\.com|^git@github\.com'; then
    REPO_URL=$(echo "$REMOTE" | sed -E 's|git@github\.com:|https://github.com/|' | sed 's|\.git$||')
  fi
fi

# Determine the last tag and range
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

# If no tags, gather all commits up to HEAD
if [[ -z "$LAST_TAG" ]]; then
  RANGE="HEAD"
  TAG_LINE="(initial release — no tags yet)"
else
  RANGE="${LAST_TAG}..HEAD"
  TAG_LINE="since ${LAST_TAG}"
fi

# ──  Gather commits and categorize ───────────────────────────────
# Format: HASH|SUBJECT|BODY
COMMITS=$(git log "${RANGE}" --format="%H|%s|%b" --no-merges 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
  echo "No new commits ${TAG_LINE}." >&2
  echo "Nothing to do." >&2
  exit 0
fi

# ──  Categorization rules ────────────────────────────────────────
# We map keywords (case-insensitive) found in the subject line or body
# to conventional-changelog categories.

categorize() {
  local subject="$1"
  local body="$2"
  local lower_subject
  lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  # Type prefix detection (Conventional Commits)
  if echo "$lower_subject" | grep -qE '^feat(\([^)]*\))?!?:\s+'; then
    echo "Added"
    return
  fi
  if echo "$lower_subject" | grep -qE '^fix(\([^)]*\))?!?:\s+'; then
    echo "Fixed"
    return
  fi
  if echo "$lower_subject" | grep -qE '^chore(\([^)]*\))?!?:\s+|^refactor(\([^)]*\))?!?:\s+|^perf(\([^)]*\))?!?:\s+'; then
    echo "Changed"
    return
  fi
  if echo "$lower_subject" | grep -qE '^docs(\([^)]*\))?!?:\s+'; then
    echo "Documentation"  # merged into Changed
    return
  fi
  if echo "$lower_subject" | grep -qE '^style(\([^)]*\))?!?:\s+'; then
    echo "Changed"
    return
  fi
  if echo "$lower_subject" | grep -qE '^test(\([^)]*\))?!?:\s+'; then
    echo "Changed"
    return
  fi
  if echo "$lower_subject" | grep -qE '^ci(\([^)]*\))?!?:\s+|^build(\([^)]*\))?!?:\s+'; then
    echo "Changed"
    return
  fi
  if echo "$lower_subject" | grep -qE '^revert(\([^)]*\))?!?:\s+'; then
    echo "Removed"
    return
  fi

  # Keyword fallback for non-conventional commits
  local combined
  combined="$lower_subject $body"
  combined=$(echo "$combined" | tr '[:upper:]' '[:lower:]')

  if echo "$combined" | grep -qE '\bsecurity\b'; then
    echo "Security"
    return
  fi
  if echo "$combined" | grep -qE '\bdeprecat'; then
    echo "Deprecated"
    return
  fi
  if echo "$combined" | grep -qE '\bfix(ed|es|ing)?\b'; then
    echo "Fixed"
    return
  fi
  if echo "$combined" | grep -qE '\badd(ed|s)?\b|^new|initial|introduce|implement|feat'; then
    echo "Added"
    return
  fi
  if echo "$combined" | grep -qE '\bremov(e|ed|ing|al)\b|delete|drop(\s+table)?'; then
    echo "Removed"
    return
  fi
  if echo "$combined" | grep -qE '\bchang(e|ed|es)\b|refactor|upgrade|migrate|rework'; then
    echo "Changed"
    return
  fi

  # Default
  echo "Changed"
}

# ──  Generate changelog entries ──────────────────────────────────
declare -A SECTIONS
SECTIONS[Added]=""
SECTIONS[Fixed]=""
SECTIONS[Changed]=""
SECTIONS[Removed]=""
SECTIONS[Security]=""
SECTIONS[Deprecated]=""
SECTIONS[Uncategorized]=""

LINE_NUM=0

while IFS='|' read -r hash subject body; do
  # Skip malformed lines
  [[ -z "$hash" || -z "$subject" ]] && continue
  LINE_NUM=$((LINE_NUM + 1))

  short_hash=$(echo "$hash" | cut -c1-7)

  # Build a link if we have a repo URL
  if [[ -n "$REPO_URL" ]]; then
    link_str="[${short_hash}](${REPO_URL}/commit/${hash})"
  else
    link_str="${short_hash}"
  fi

  # Clean subject: remove conventional commit prefix for readability
  clean_subject=$(echo "$subject" | sed -E 's/^(feat|fix|chore|docs|refactor|perf|test|ci|build|style|revert)(\([^)]*\))?!?:\s*//')

  category=$(categorize "$subject" "$body")

  # Extra detail from body (first line of body if non-empty and short)
  detail=""
  if [[ -n "$body" ]]; then
    first_body_line=$(echo "$body" | head -1)
    if [[ ${#first_body_line} -gt 3 ]]; then
      detail=" — ${first_body_line}"
    fi
  fi

  entry="  - ${link_str} ${clean_subject}${detail}"
  SECTIONS[$category]="${SECTIONS[$category]}"$'\n'"${entry}"
done <<< "$COMMITS"

# ──  Determine version ───────────────────────────────────────────
NEXT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
# If we already have a tag, bump patch
if echo "$NEXT_VERSION" | grep -qE '^v?[0-9]+\.[0-9]+\.[0-9]+'; then
  # Just use the last tag as reference — the changelog says "since X"
  VERSION_HEADER="## [unreleased]"
else
  VERSION_HEADER="## [0.1.0]"
fi

# ──  Write the changelog ─────────────────────────────────────────
DATE=$(date +%Y-%m-%d)

{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "${VERSION_HEADER} — ${DATE} ${TAG_LINE}"
  echo ""

  non_empty=false
  for section in "Added" "Fixed" "Changed" "Removed" "Security" "Deprecated" "Uncategorized"; do
    entries="${SECTIONS[$section]}"
    if [[ -n "$entries" ]]; then
      non_empty=true
      echo "### ${section}"
      echo "$entries"
      echo ""
    fi
  done

  if ! $non_empty; then
    echo "_No significant changes._"
    echo ""
  fi

  if [[ -n "$REPO_URL" ]]; then
    echo "---"
    echo ""
    echo "**Full Changelog**: ${REPO_URL}/compare/${LAST_TAG:-$(git rev-list --max-parents=0 HEAD)}...HEAD"
  fi
} > "$OUTPUT"

echo "✓ Changelog written to ${OUTPUT}" >&2
echo "  ${LINE_NUM} commits categorized" >&2
