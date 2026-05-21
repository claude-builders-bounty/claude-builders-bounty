#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./changelog.sh [options]

Generate a structured CHANGELOG.md from git commits since the latest tag.

Options:
  -o, --output FILE       Output file path (default: CHANGELOG.md)
  --since REF             Start ref/commit/tag (default: latest tag, or first commit)
  --to REF                End ref (default: HEAD)
  --append                Append generated section to existing output file
  -h, --help              Show this help

Examples:
  ./changelog.sh
  ./changelog.sh --since v1.2.0 --to HEAD
  ./changelog.sh --output docs/CHANGELOG.md --append
EOF
}

OUTPUT="CHANGELOG.md"
SINCE=""
TO="HEAD"
APPEND=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 2; }
      OUTPUT="$2"
      shift 2
      ;;
    --since)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 2; }
      SINCE="$2"
      shift 2
      ;;
    --to)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 2; }
      TO="$2"
      shift 2
      ;;
    --append)
      APPEND=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

if [[ -z "$SINCE" ]]; then
  if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    SINCE="$(git describe --tags --abbrev=0)"
  else
    SINCE="$(git rev-list --max-parents=0 HEAD | tail -n 1)"
  fi
fi

if ! git rev-parse --verify "$SINCE^{commit}" >/dev/null 2>&1; then
  echo "Error: --since ref '$SINCE' does not exist." >&2
  exit 1
fi

if ! git rev-parse --verify "$TO^{commit}" >/dev/null 2>&1; then
  echo "Error: --to ref '$TO' does not exist." >&2
  exit 1
fi

ROOT_COMMIT="$(git rev-list --max-parents=0 "$TO" | tail -n 1)"
RANGE="$SINCE..$TO"
INCLUDE_SINCE=0
if [[ "$(git rev-parse "$SINCE")" == "$(git rev-parse "$ROOT_COMMIT")" ]]; then
  RANGE="$SINCE..$TO"
  INCLUDE_SINCE=1
fi

if [[ "$INCLUDE_SINCE" -eq 1 ]]; then
  COMMITS="$(git log --no-merges --pretty=format:'%s%x09%h' "$TO" 2>/dev/null || true)"
else
  COMMITS="$(git log --no-merges --pretty=format:'%s%x09%h' "$RANGE" 2>/dev/null || true)"
fi
DATE="$(date +%Y-%m-%d)"
TITLE="## Unreleased - $DATE"

section_for_subject() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower" =~ ^(add|added|feat|feature)(\(.+\))?: ]]; then
    echo "Added"
  elif [[ "$lower" =~ ^(fix|fixed|bug|bugfix|hotfix)(\(.+\))?: ]]; then
    echo "Fixed"
  elif [[ "$lower" =~ ^(remove|removed|delete|deleted)(\(.+\))?: ]]; then
    echo "Removed"
  elif [[ "$lower" =~ ^(change|changed|chore|refactor|perf|docs|test|ci|build|style)(\(.+\))?: ]]; then
    echo "Changed"
  else
    case "$lower" in
      *" add "*|*" adds "*|*" added "*|*" implement"*|*" introduce"*) echo "Added" ;;
      *" fix "*|*" fixes "*|*" fixed "*|*" bug"*) echo "Fixed" ;;
      *" remove "*|*" removes "*|*" removed "*|*" delete "*|*" deletes "*) echo "Removed" ;;
      *" update "*|*" updates "*|*" updated "*|*" improve"*) echo "Changed" ;;
      *) echo "Changed" ;;
    esac
  fi
}

render_section() {
  local name="$1"
  local content="$2"
  printf '\n### %s\n' "$name"
  if [[ -n "$content" ]]; then
    printf '%s\n' "$content"
  else
    printf -- '- No changes.\n'
  fi
}

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

if [[ -n "$COMMITS" ]]; then
  while IFS=$'\t' read -r subject hash; do
    [[ -n "${subject:-}" ]] || continue
    item="- ${subject} (${hash})"
    case "$(section_for_subject "$subject")" in
      Added) ADDED+="${item}"$'\n' ;;
      Fixed) FIXED+="${item}"$'\n' ;;
      Changed) CHANGED+="${item}"$'\n' ;;
      Removed) REMOVED+="${item}"$'\n' ;;
    esac
  done <<< "$COMMITS"
fi

TMP="$(mktemp)"
{
  printf '# Changelog\n\n'
  printf 'Generated from commits in `%s` on %s.\n\n' "$RANGE" "$DATE"
  printf '%s\n' "$TITLE"
  render_section "Added" "${ADDED%$'\n'}"
  render_section "Fixed" "${FIXED%$'\n'}"
  render_section "Changed" "${CHANGED%$'\n'}"
  render_section "Removed" "${REMOVED%$'\n'}"
} > "$TMP"

if [[ "$APPEND" -eq 1 && -f "$OUTPUT" ]]; then
  {
    cat "$TMP"
    printf '\n---\n\n'
    cat "$OUTPUT"
  } > "${OUTPUT}.tmp"
  mv "${OUTPUT}.tmp" "$OUTPUT"
else
  mv "$TMP" "$OUTPUT"
fi

printf 'Wrote %s from range %s\n' "$OUTPUT" "$RANGE"
