#!/usr/bin/env bash
set -euo pipefail

OUTPUT="CHANGELOG.md"
REPO="."
VERSION="Unreleased"
SINCE=""
INCLUDE_ALL=false

usage() {
  cat <<'EOF'
Usage: changelog.sh [options]

Generate a structured CHANGELOG.md from git history since the latest tag.

Options:
  -r, --repo PATH       Git repository path (default: .)
  -o, --output FILE     Output changelog path (default: CHANGELOG.md)
  -v, --version NAME    Version heading (default: Unreleased)
      --since REF       Start ref instead of latest tag
      --all             Include all commits if no tag exists
  -h, --help            Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--repo) REPO="$2"; shift 2 ;;
    -o|--output) OUTPUT="$2"; shift 2 ;;
    -v|--version) VERSION="$2"; shift 2 ;;
    --since) SINCE="$2"; shift 2 ;;
    --all) INCLUDE_ALL=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if ! git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $REPO" >&2
  exit 1
fi

if [[ -z "$SINCE" ]]; then
  if SINCE=$(git -C "$REPO" describe --tags --abbrev=0 2>/dev/null); then
    RANGE="$SINCE..HEAD"
  elif [[ "$INCLUDE_ALL" == true ]]; then
    RANGE="HEAD"
  else
    RANGE="HEAD"
  fi
else
  RANGE="$SINCE..HEAD"
fi

TMP=$(mktemp)
ADDED_FILE=$(mktemp)
FIXED_FILE=$(mktemp)
CHANGED_FILE=$(mktemp)
REMOVED_FILE=$(mktemp)
trap 'rm -f "$TMP" "$ADDED_FILE" "$FIXED_FILE" "$CHANGED_FILE" "$REMOVED_FILE"' EXIT

git -C "$REPO" log "$RANGE" --no-merges --date=short --pretty=format:'%h%x09%ad%x09%s' > "$TMP" || true

TODAY=$(date +%F)
LAST_TAG="${SINCE:-none}"

humanize_subject() {
  local subject="$1"
  subject=$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')
  subject=$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')
  printf '%s' "$subject"
}

category_for() {
  local s lc
  s="$1"
  lc=$(printf '%s' "$s" | tr '[:upper:]' '[:lower:]')
  case "$lc" in
    feat:*|feat\(*|add:*|added:*) echo "Added" ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|deprecate:*|deprecated:*) echo "Removed" ;;
    change:*|changed:*|refactor:*|refactor\(*|perf:*|perf\(*|chore:*|chore\(*|docs:*|docs\(*|style:*|test:*|ci:*|build:*) echo "Changed" ;;
    *)
      if [[ "$lc" =~ (^|[[:space:]])(remove|delete|drop|deprecate)[sd]?($|[[:space:]]) ]]; then echo "Removed"
      elif [[ "$lc" =~ (^|[[:space:]])(fix|repair|resolve|patch)[ed]?($|[[:space:]]) ]]; then echo "Fixed"
      elif [[ "$lc" =~ (^|[[:space:]])(add|create|implement|introduce)[sd]?($|[[:space:]]) ]]; then echo "Added"
      else echo "Changed"
      fi ;;
  esac
}

while IFS=$'\t' read -r hash date subject || [[ -n "${hash:-}" ]]; do
  [[ -z "${hash:-}" ]] && continue
  clean=$(humanize_subject "$subject")
  line="- ${clean} (${hash}, ${date})"
  case "$(category_for "$subject")" in
    Added) printf '%s\n' "$line" >> "$ADDED_FILE" ;;
    Fixed) printf '%s\n' "$line" >> "$FIXED_FILE" ;;
    Removed) printf '%s\n' "$line" >> "$REMOVED_FILE" ;;
    *) printf '%s\n' "$line" >> "$CHANGED_FILE" ;;
  esac
done < "$TMP"

write_section() {
  local title="$1"
  local file="$2"
  [[ ! -s "$file" ]] && return
  printf '\n### %s\n\n' "$title"
  cat "$file"
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes are generated from git history.\n\n'
  printf '## [%s] - %s\n' "$VERSION" "$TODAY"
  printf '\n_Source range: `%s`_\n' "$RANGE"
  if [[ ! -s "$TMP" ]]; then
    printf '\nNo commits found for this range.\n'
  else
    write_section "Added" "$ADDED_FILE"
    write_section "Fixed" "$FIXED_FILE"
    write_section "Changed" "$CHANGED_FILE"
    write_section "Removed" "$REMOVED_FILE"
  fi
} > "$OUTPUT"

printf 'Generated %s from %s\n' "$OUTPUT" "$RANGE"
