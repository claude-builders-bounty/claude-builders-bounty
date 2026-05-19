#!/usr/bin/env bash
set -euo pipefail

# Generate a categorized CHANGELOG from git history since the latest tag.
# Usage:
#   bash changelog.sh
#   bash changelog.sh --repo /path/to/repo --output CHANGELOG.md

REPO_PATH="."
OUT_FILE="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO_PATH="${2:-}"
      shift 2
      ;;
    --output)
      OUT_FILE="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ ! -d "$REPO_PATH/.git" ]]; then
  echo "Not a git repository: $REPO_PATH" >&2
  exit 1
fi

if ! git -C "$REPO_PATH" rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "Repository has no commits: $REPO_PATH" >&2
  exit 1
fi

LAST_TAG="$(git -C "$REPO_PATH" describe --tags --abbrev=0 2>/dev/null || true)"
DATE_NOW="$(date +%F)"

if [[ -n "$LAST_TAG" ]]; then
  VERSION="Unreleased (since ${LAST_TAG})"
  RANGE="${LAST_TAG}..HEAD"
  LOG_CMD=(git -C "$REPO_PATH" log "$RANGE" --pretty=format:'%h%x09%s')
else
  VERSION="Unreleased"
  LOG_CMD=(git -C "$REPO_PATH" log HEAD --pretty=format:'%h%x09%s')
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

map_commit() {
  local hash="$1"
  local subject="$2"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  local line="- ${subject} (${hash})"

  if [[ "$lower" =~ ^feat(\(.+\))?: ]] || [[ "$lower" =~ ^add(\(.+\))?: ]] || [[ "$lower" =~ ^new(\(.+\))?: ]]; then
    ADDED+=("$line")
  elif [[ "$lower" =~ ^fix(\(.+\))?: ]] || [[ "$lower" =~ bug|hotfix|patch ]]; then
    FIXED+=("$line")
  elif [[ "$lower" =~ ^remove(\(.+\))?: ]] || [[ "$lower" =~ ^delete(\(.+\))?: ]] || [[ "$lower" =~ removed|deprecated|drop ]]; then
    REMOVED+=("$line")
  elif [[ "$lower" =~ ^refactor(\(.+\))?: ]] || [[ "$lower" =~ ^perf(\(.+\))?: ]] || [[ "$lower" =~ ^style(\(.+\))?: ]] || [[ "$lower" =~ ^docs(\(.+\))?: ]] || [[ "$lower" =~ ^chore(\(.+\))?: ]] || [[ "$lower" =~ ^ci(\(.+\))?: ]] || [[ "$lower" =~ ^build(\(.+\))?: ]]; then
    CHANGED+=("$line")
  else
    CHANGED+=("$line")
  fi
}

while IFS=$'\t' read -r hash subject; do
  [[ -z "${hash:-}" || -z "${subject:-}" ]] && continue
  map_commit "$hash" "$subject"
done < <("${LOG_CMD[@]}")

{
  echo "# Changelog"
  echo
  echo "## [${VERSION}] - ${DATE_NOW}"
  echo

  echo "### Added"
  if [[ ${#ADDED[@]} -eq 0 ]]; then
    echo "- _No notable additions_"
  else
    printf '%s\n' "${ADDED[@]}"
  fi
  echo

  echo "### Fixed"
  if [[ ${#FIXED[@]} -eq 0 ]]; then
    echo "- _No notable fixes_"
  else
    printf '%s\n' "${FIXED[@]}"
  fi
  echo

  echo "### Changed"
  if [[ ${#CHANGED[@]} -eq 0 ]]; then
    echo "- _No notable changes_"
  else
    printf '%s\n' "${CHANGED[@]}"
  fi
  echo

  echo "### Removed"
  if [[ ${#REMOVED[@]} -eq 0 ]]; then
    echo "- _No notable removals_"
  else
    printf '%s\n' "${REMOVED[@]}"
  fi
} > "$OUT_FILE"

echo "Generated ${OUT_FILE} from ${REPO_PATH}"
