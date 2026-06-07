#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh                    # outputs CHANGELOG.md in current dir
#   bash changelog.sh --output FILE.md   # write to FILE.md instead
#   bash changelog.sh --repo /path       # run in a different repo
#
set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────
OUTPUT="${PWD}/CHANGELOG.md"
TARGET_REPO="${PWD}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output|-o)  OUTPUT="$2";  shift 2 ;;
    --repo|-r)    TARGET_REPO="$2"; shift 2 ;;
    --help|-h)    echo "Usage: bash changelog.sh [--output FILE] [--repo /path]" >&2; exit 0 ;;
    *)            echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

cd "$TARGET_REPO"

# ── Guard: is this a git repo? ────────────────────────────────────────
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not a git repository: $TARGET_REPO" >&2
  exit 1
fi

# ── Determine commit range ────────────────────────────────────────────
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  SCOPE="since tag \`${LAST_TAG}\`"
else
  RANGE="--root"
  SCOPE="since the beginning of the repository"
fi

# ── Fetch commits and classify ────────────────────────────────────────
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS=$'\x1f' read -r hash refs subject; do
  # Determine the "clean" subject (strip conventional-commit prefix)
  clean_subject="$subject"
  raw_type=""

  # Try to match conventional-commit pattern:  type(scope)!: subject
  # Extract type manually using parameter expansion for robustness
  if [[ "$subject" == *:* ]]; then
    # Check if it starts with conventional commit format
    first_word="${subject%%:*}"
    # Remove leading whitespace
    first_word="${first_word#"${first_word%%[![:space:]]*}"}"
    # Check if first word looks like type(scope) or type or type!
    if [[ "$first_word" =~ ^[a-zA-Z_]+ ]]; then
      raw_type="${BASH_REMATCH[0]}"
      # Clean subject: everything after the colon+space
      clean_subject="${subject#*:[[:space:]]}"
      # If the first part had (scope) or !, the raw_type extracted above still works
      # But let's handle it more precisely
      if [[ "$first_word" =~ ^([a-zA-Z_]+) ]]; then
        raw_type="${BASH_REMATCH[1]}"
      fi
    fi
  fi

  # Build a full entry line
  entry="- ${clean_subject} (${hash:0:7})"

  # Convert to lowercase for comparison
  case "${raw_type,,}" in
    feat|feature)
      ADDED+=("$entry") ;;
    fix|bugfix|bug|bugfix)
      FIXED+=("$entry") ;;
    remove|removed|delete|deleted|deprecate|deprecated)
      REMOVED+=("$entry") ;;
    *)
      # Heuristic word matching inside the subject as fallback
      subject_lower="$(echo "$subject" | tr '[:upper:]' '[:lower:]')"
      case "$subject_lower" in
        *"add"*|*"new"*|*"introduce"*|*"implement"*|*"create"*|*"support"*)
          ADDED+=("$entry") ;;
        *"fix"*|*"patch"*|*"correct"*|*"resolve"*|*"repair"*)
          FIXED+=("$entry") ;;
        *"remov"*|*"delet"*|*"deprecat"*|*"drop"*|*"cleanup"*|*"unused"*)
          REMOVED+=("$entry") ;;
        *"updat"*|*"refactor"*|*"improv"*|*"change"*|*"migrat"*|*"bump"*|*"upgrade"*|*"optimize"*|*"simplify"*|*"rework"*|*"tweak"*|*"convert"*|*"rewrite"*)
          CHANGED+=("$entry") ;;
        *)
          CHANGED+=("$entry") ;;  # default to Changed
      esac
      ;;
  esac
done < <(git log "$RANGE" --format="%H%x1f%D%x1f%s" --reverse --date=short 2>/dev/null)

# ── Build CHANGELOG.md ────────────────────────────────────────────────
{
  echo "# Changelog"
  echo ""
  echo "> Generated from git history ${SCOPE}."
  echo "> Date: $(date '+%Y-%m-%d')"
  echo ""

  # Latest version (tag) as heading
  if [[ -n "$LAST_TAG" ]]; then
    echo "## [${LAST_TAG}]"
  else
    echo "## [Unreleased]"
  fi
  echo ""

  # Print each section with its icon
  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added ✨"
    echo ""
    for item in "${ADDED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed 🐛"
    echo ""
    for item in "${FIXED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed 🔧"
    echo ""
    for item in "${CHANGED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed 🗑️"
    echo ""
    for item in "${REMOVED[@]}"; do echo "$item"; done
    echo ""
  fi

  # Summary line
  total=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))
  echo "---"
  echo ""
  echo "_${total} commits ${SCOPE}._"

} > "$OUTPUT"

echo "CHANGELOG written to ${OUTPUT}"
echo "  ${#ADDED[@]} added | ${#FIXED[@]} fixed | ${#CHANGED[@]} changed | ${#REMOVED[@]} removed"
