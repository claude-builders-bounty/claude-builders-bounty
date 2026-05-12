#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
SINCE_REF=""
DRY_RUN=0

usage() {
  cat <<'USAGE'
Generate a structured CHANGELOG.md from git history.

Usage:
  bash changelog.sh [--output CHANGELOG.md] [--since <git-ref>] [--dry-run]

Options:
  --output <file>  File to write. Defaults to CHANGELOG.md.
  --since <ref>    Generate entries after this tag/ref. Defaults to latest tag.
  --dry-run        Print the generated changelog section instead of writing.
  -h, --help       Show this help.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output)
      OUTPUT_FILE="${2:-}"
      [ -n "$OUTPUT_FILE" ] || { echo "Missing value for --output" >&2; exit 2; }
      shift 2
      ;;
    --since)
      SINCE_REF="${2:-}"
      [ -n "$SINCE_REF" ] || { echo "Missing value for --since" >&2; exit 2; }
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not inside a git repository." >&2
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [ -z "$SINCE_REF" ]; then
  SINCE_REF="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [ -n "$SINCE_REF" ]; then
  if ! git rev-parse --verify --quiet "$SINCE_REF^{commit}" >/dev/null; then
    echo "Ref not found: $SINCE_REF" >&2
    exit 1
  fi
  RANGE="$SINCE_REF..HEAD"
  RANGE_LABEL="since $SINCE_REF"
else
  RANGE="HEAD"
  RANGE_LABEL="from full history"
fi

TODAY="$(date +%Y-%m-%d)"
HEADER="## [Unreleased] - $TODAY"

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

trim_subject() {
  printf '%s' "$1" |
    sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//; s/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//'
}

append_entry() {
  category="$1"
  subject="$2"
  hash="$3"
  entry="- $(trim_subject "$subject") (${hash})"

  case "$category" in
    Added) ADDED="${ADDED}${entry}
" ;;
    Fixed) FIXED="${FIXED}${entry}
" ;;
    Removed) REMOVED="${REMOVED}${entry}
" ;;
    *) CHANGED="${CHANGED}${entry}
" ;;
  esac
}

category_for_subject() {
  subject="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  case "$subject" in
    feat:*|feat\(*|feature:*|add:*|added:*|create:*|introduce:*|implement:*)
      printf 'Added'
      return
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|patch:*|resolve:*|resolved:*)
      printf 'Fixed'
      return
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*)
      printf 'Removed'
      return
      ;;
  esac

  if printf '%s' "$subject" | grep -Eq '\b(add|added|create|introduce|implement|new)\b'; then
    printf 'Added'
  elif printf '%s' "$subject" | grep -Eq '\b(fix|fixed|bug|resolve|resolved|repair)\b'; then
    printf 'Fixed'
  elif printf '%s' "$subject" | grep -Eq '\b(remove|removed|delete|deleted|drop|deprecated)\b'; then
    printf 'Removed'
  else
    printf 'Changed'
  fi
}

COMMITS="$(git log --no-merges --reverse --pretty=format:'%h%x09%s' "$RANGE" 2>/dev/null || true)"

if [ -n "$COMMITS" ]; then
  while IFS="$(printf '\t')" read -r hash subject; do
    [ -n "$hash" ] || continue
    category="$(category_for_subject "$subject")"
    append_entry "$category" "$subject" "$hash"
  done <<EOF
$COMMITS
EOF
fi

section_for() {
  title="$1"
  entries="$2"
  if [ -n "$entries" ]; then
    printf '### %s\n%s\n' "$title" "$entries"
  fi
}

GENERATED="$(
  printf '# Changelog\n\n'
  printf '%s\n\n' "$HEADER"
  if [ -z "$ADDED$FIXED$CHANGED$REMOVED" ]; then
    printf '_No commits found %s._\n\n' "$RANGE_LABEL"
  else
    section_for "Added" "$ADDED"
    section_for "Fixed" "$FIXED"
    section_for "Changed" "$CHANGED"
    section_for "Removed" "$REMOVED"
  fi
)"

if [ "$DRY_RUN" -eq 1 ]; then
  printf '%s' "$GENERATED"
  exit 0
fi

if [ -f "$OUTPUT_FILE" ]; then
  EXISTING_WITHOUT_TITLE="$(sed '1{/^# Changelog$/d;}' "$OUTPUT_FILE")"
  {
    printf '%s' "$GENERATED"
    printf '%s\n' "$EXISTING_WITHOUT_TITLE"
  } > "${OUTPUT_FILE}.tmp"
  mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
else
  printf '%s' "$GENERATED" > "$OUTPUT_FILE"
fi

echo "Wrote $OUTPUT_FILE ($RANGE_LABEL)."
