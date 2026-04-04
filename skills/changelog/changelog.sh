#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [version] [since-tag]
# Example: bash changelog.sh v2.0.0
#          bash changelog.sh v2.0.0 v1.9.0

set -euo pipefail

VERSION="${1:-Unreleased}"
SINCE="${2:-}"
OUTPUT="CHANGELOG.md"
DATE=$(date +%Y-%m-%d)

# ── Find range ──────────────────────────────────────────────────────────────
if [[ -z "$SINCE" ]]; then
  # Auto-detect the most recent tag
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -n "$SINCE" ]]; then
  RANGE="${SINCE}..HEAD"
  SINCE_LABEL="since $SINCE"
else
  RANGE="HEAD"
  SINCE_LABEL="full history"
fi

echo "Generating CHANGELOG for $VERSION ($SINCE_LABEL)..."

# ── Collect commits ──────────────────────────────────────────────────────────
# Format: <hash> <subject>
mapfile -t COMMITS < <(git log "$RANGE" --pretty=format:"%h %s" --no-merges 2>/dev/null || true)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
  echo "No commits found in range. Nothing to generate."
  exit 0
fi

# ── Categorize by conventional commit prefix ────────────────────────────────
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

for commit in "${COMMITS[@]}"; do
  hash="${commit:0:7}"
  subject="${commit:8}"
  # Strip conventional commit scope: "feat(ui): ..." → "feat: ..."
  subject_clean=$(echo "$subject" | sed 's/^[a-z]*([^)]*): //')

  case "$subject" in
    feat*|add*|new*|implement*)
      ADDED+=("- $subject_clean ($hash)")
      ;;
    fix*|bug*|patch*|hotfix*|resolve*)
      FIXED+=("- $subject_clean ($hash)")
      ;;
    refactor*|perf*|update*|change*|improve*|bump*|upgrade*|style*|chore*)
      CHANGED+=("- $subject_clean ($hash)")
      ;;
    remove*|delete*|drop*|deprecate*)
      REMOVED+=("- $subject_clean ($hash)")
      ;;
    *)
      OTHER+=("- $subject ($hash)")
      ;;
  esac
done

# ── Write output ─────────────────────────────────────────────────────────────
{
  # Prepend new section if CHANGELOG already exists
  if [[ -f "$OUTPUT" ]]; then
    EXISTING=$(cat "$OUTPUT")
  else
    EXISTING=""
  fi

  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "---"
  echo ""
  echo "## [$VERSION] — $DATE"
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    printf '%s\n' "${ADDED[@]}"
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    printf '%s\n' "${FIXED[@]}"
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    printf '%s\n' "${CHANGED[@]}"
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    printf '%s\n' "${REMOVED[@]}"
    echo ""
  fi

  if [[ ${#OTHER[@]} -gt 0 ]]; then
    echo "### Other"
    printf '%s\n' "${OTHER[@]}"
    echo ""
  fi

  # Append existing changelog content (minus its own header)
  if [[ -n "$EXISTING" ]]; then
    echo "---"
    echo ""
    echo "$EXISTING" | tail -n +3  # skip "# Changelog\n"
  fi

} > "$OUTPUT"

echo "✅ Written to $OUTPUT (${#COMMITS[@]} commits categorized)"
echo ""
echo "Preview:"
head -40 "$OUTPUT"
