#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history since the last tag.
# Usage: bash changelog.sh [output-path] [repo-path]
# Defaults: CHANGELOG.md in the current (or repo) directory.
set -euo pipefail

OUT_FILE="${1:-CHANGELOG.md}"
REPO_PATH="${2:-.}"

if [[ ! -d "$REPO_PATH/.git" && ! -d "$REPO_PATH" ]]; then
  echo "error: not a directory: $REPO_PATH" >&2
  exit 1
fi

# Resolve to absolute for stable git -C usage
REPO_PATH="$(cd "$REPO_PATH" && pwd)"

if ! git -C "$REPO_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not a git repository: $REPO_PATH" >&2
  exit 1
fi

# --- categorization (conventional commits + keyword fallbacks) ---
# Prints one of: Added | Fixed | Changed | Removed
categorize_subject() {
  local subject="$1"
  local lower type re_cc
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  # Conventional commit type prefix: type(scope)!: subject
  # Store regex in a variable so parentheses are not parsed as [[ ]] syntax.
  re_cc='^([a-z]+)(\([^)]*\))?\!?:[[:space:]]'
  type=""
  if [[ "$lower" =~ $re_cc ]]; then
    type="${BASH_REMATCH[1]}"
  fi

  case "$type" in
    feat|feature)
      echo "Added"
      return
      ;;
    fix|bugfix)
      echo "Fixed"
      return
      ;;
    remove)
      echo "Removed"
      return
      ;;
    revert|chore|docs|doc|style|refactor|perf|test|ci|build|change|update)
      echo "Changed"
      return
      ;;
  esac

  # Keyword heuristics when type is missing or unknown (simple word matches)
  case "$lower" in
    *add\ *|*added*|*adds\ *|*adding*|*introduce*|*implement*|*create\ *|*created*|*new\ *)
      echo "Added"
      ;;
    *fix\ *|*fixed*|*fixes\ *|*fixing*|*bugfix*|*hotfix*|*patch*)
      echo "Fixed"
      ;;
    *remove*|*delete*|*drop\ *|*dropped*|*deprecate*)
      echo "Removed"
      ;;
    *)
      echo "Changed"
      ;;
  esac
}

# Last tag (annotated or lightweight); empty if none
LAST_TAG="$(git -C "$REPO_PATH" describe --tags --abbrev=0 2>/dev/null || true)"
RANGE_DESC=""
if [[ -n "$LAST_TAG" ]]; then
  RANGE_DESC="since tag \`$LAST_TAG\`"
  LOG_RANGE="${LAST_TAG}..HEAD"
else
  RANGE_DESC="full history (no tags found)"
  LOG_RANGE="HEAD"
fi

# subject\thash  (subject may contain spaces; hash is last field — use custom format)
# Use %H full hash short via %h; separate with SOH to avoid collisions
mapfile -t COMMITS < <(
  if [[ -n "$LAST_TAG" ]]; then
    git -C "$REPO_PATH" log "$LOG_RANGE" --pretty=format:'%h%x01%s' --no-merges
  else
    git -C "$REPO_PATH" log --pretty=format:'%h%x01%s' --no-merges
  fi
)

declare -a ADDED=() FIXED=() CHANGED=() REMOVED=()

for line in "${COMMITS[@]+"${COMMITS[@]}"}"; do
  [[ -z "${line:-}" ]] && continue
  hash="${line%%$'\x01'*}"
  subject="${line#*$'\x01'}"
  [[ -z "$subject" ]] && continue
  catg="$(categorize_subject "$subject")"
  entry="- ${subject} (\`${hash}\`)"
  case "$catg" in
    Added) ADDED+=("$entry") ;;
    Fixed) FIXED+=("$entry") ;;
    Removed) REMOVED+=("$entry") ;;
    *) CHANGED+=("$entry") ;;
  esac
done

TODAY="$(date -u +%Y-%m-%d)"
REPO_NAME="$(basename "$REPO_PATH")"
VERSION_HEADER="Unreleased"
if [[ -n "$LAST_TAG" ]]; then
  VERSION_HEADER="Unreleased (after ${LAST_TAG})"
fi

# Write CHANGELOG (Keep a Changelog–style sections)
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to **${REPO_NAME}** are documented in this file."
  echo ""
  echo "Generated ${TODAY} UTC from git history ${RANGE_DESC}."
  echo ""
  echo "## [${VERSION_HEADER}] - ${TODAY}"
  echo ""

  echo "### Added"
  if ((${#ADDED[@]})); then
    printf '%s\n' "${ADDED[@]}"
  else
    echo "_None_"
  fi
  echo ""

  echo "### Fixed"
  if ((${#FIXED[@]})); then
    printf '%s\n' "${FIXED[@]}"
  else
    echo "_None_"
  fi
  echo ""

  echo "### Changed"
  if ((${#CHANGED[@]})); then
    printf '%s\n' "${CHANGED[@]}"
  else
    echo "_None_"
  fi
  echo ""

  echo "### Removed"
  if ((${#REMOVED[@]})); then
    printf '%s\n' "${REMOVED[@]}"
  else
    echo "_None_"
  fi
  echo ""
} > "$OUT_FILE"

# If OUT_FILE is relative and REPO is not cwd, still write where caller asked;
# report absolute path for convenience
ABS_OUT="$(cd "$(dirname "$OUT_FILE")" && pwd)/$(basename "$OUT_FILE")"
echo "Wrote $ABS_OUT"
echo "Commits processed: ${#COMMITS[@]}"
echo "  Added: ${#ADDED[@]}  Fixed: ${#FIXED[@]}  Changed: ${#CHANGED[@]}  Removed: ${#REMOVED[@]}"
if [[ -n "$LAST_TAG" ]]; then
  echo "Range: ${LAST_TAG}..HEAD"
else
  echo "Range: full history (no tags)"
fi
