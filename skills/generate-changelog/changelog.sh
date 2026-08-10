#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh [--output PATH] [--since TAG] [--all] [--include-merges] [--help]
#
# Fetches commits since the last git tag (or all commits if no tags exist),
# categorizes them into Added / Fixed / Changed / Removed, and writes a
# properly formatted CHANGELOG.md.
#
# Requirements: bash 4+, git
#
set -euo pipefail

# --- Defaults ---------------------------------------------------------------
OUTPUT="CHANGELOG.md"
SINCE=""
INCLUDE_MERGES=0
USE_ALL=0

usage() {
  cat <<'EOF'
Usage: bash changelog.sh [options]

Generate a structured CHANGELOG.md from git history.

Options:
  -o, --output PATH     Output file path (default: CHANGELOG.md)
  -s, --since TAG       Start from TAG instead of auto-detecting the last tag
      --all             Include the full history (ignore tags)
      --include-merges  Include merge commits (excluded by default)
  -h, --help            Show this help message

Examples:
  bash changelog.sh
  bash changelog.sh --output docs/CHANGELOG.md
  bash changelog.sh --since v1.2.0
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output) OUTPUT="${2:?Missing value for $1}"; shift 2 ;;
    -s|--since) SINCE="$2"; shift 2 ;;
    --all) USE_ALL=1; shift ;;
    --include-merges) INCLUDE_MERGES=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Error: Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

# --- Validate git repo ------------------------------------------------------
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Not inside a git repository." >&2
  exit 1
fi

# --- Determine commit range -------------------------------------------------
LAST_TAG=""
if [[ "$USE_ALL" -eq 0 ]]; then
  if [[ -n "$SINCE" ]]; then
    LAST_TAG="$SINCE"
  else
    LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  fi
fi

MERGE_FLAG="--no-merges"
if [[ "$INCLUDE_MERGES" -eq 1 ]]; then
  MERGE_FLAG="--merges"
fi

if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  SECTION_TITLE="## [Unreleased] (since ${LAST_TAG})"
else
  RANGE="HEAD"
  SECTION_TITLE="## [Unreleased]"
fi

# --- Collect & categorize commits -------------------------------------------
# Use a unit separator (0x1f) between hash and subject so parsing is robust
# against any characters in the message.
added=()
fixed=()
changed=()
removed=()

# Regexes are stored in variables: bash's [[ =~ ]] mis-parses `!` and `(`
# when they appear inline, but treats variable-expanded regexes verbatim.
# Conventional commit: prefix(scope)!: rest  (scope and ! are optional)
RE_ADD='^(feat|feature|add|new|introduce|implement|support|create)(\([^)]*\))?!?:[[:space:]]*(.*)$'
RE_FIX='^(fix|bug|bugfix|hotfix|patch|correct|resolve|repair)(\([^)]*\))?!?:[[:space:]]*(.*)$'
RE_REMOVE='^(remove|delete|drop|deprecate)(\([^)]*\))?!?:[[:space:]]*(.*)$'
RE_CHANGE='^(refactor|chore|ci|build|style|perf|docs|test|update|change|improve|bump|migrate|rename|revert|config|security)(\([^)]*\))?!?:[[:space:]]*(.*)$'

while IFS=$'\x1f' read -r hash subject; do
  [[ -z "$hash" ]] && continue
  short="${hash:0:7}"
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower" =~ $RE_ADD ]]; then
    rest="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//')"
    added+=("- ${rest} (\`${short}\`)")
  elif [[ "$lower" =~ $RE_FIX ]]; then
    rest="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//')"
    fixed+=("- ${rest} (\`${short}\`)")
  elif [[ "$lower" =~ $RE_REMOVE ]]; then
    rest="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//')"
    removed+=("- ${rest} (\`${short}\`)")
  elif [[ "$lower" =~ $RE_CHANGE ]]; then
    rest="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//')"
    changed+=("- ${rest} (\`${short}\`)")
  else
    # No recognized prefix → Changed (default)
    changed+=("- ${subject} (\`${short}\`)")
  fi
done < <(git log --format='%h%x1f%s' "$MERGE_FLAG" "$RANGE" 2>/dev/null || git log --format='%h%x1f%s' "$MERGE_FLAG")

# --- Write output -----------------------------------------------------------
{
  echo "# Changelog"
  echo ""
  echo "$SECTION_TITLE"
  echo ""

  if [[ ${#added[@]} -gt 0 ]]; then
    echo "### Added"
    echo ""
    printf '%s\n' "${added[@]}"
    echo ""
  fi

  if [[ ${#fixed[@]} -gt 0 ]]; then
    echo "### Fixed"
    echo ""
    printf '%s\n' "${fixed[@]}"
    echo ""
  fi

  if [[ ${#changed[@]} -gt 0 ]]; then
    echo "### Changed"
    echo ""
    printf '%s\n' "${changed[@]}"
    echo ""
  fi

  if [[ ${#removed[@]} -gt 0 ]]; then
    echo "### Removed"
    echo ""
    printf '%s\n' "${removed[@]}"
    echo ""
  fi

  total=$(( ${#added[@]} + ${#fixed[@]} + ${#changed[@]} + ${#removed[@]} ))
  if [[ "$total" -eq 0 ]]; then
    echo "_No changes since ${LAST_TAG:-the beginning of history}._"
    echo ""
  fi
} > "$OUTPUT"

echo "Generated $OUTPUT ($total commits since ${LAST_TAG:-initial commit})"