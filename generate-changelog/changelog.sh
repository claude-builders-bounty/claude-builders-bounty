#!/usr/bin/env bash
set -euo pipefail

output_file="CHANGELOG.md"
from_ref=""
version=""
dry_run=0

usage() {
  cat <<'USAGE'
Usage: bash generate-changelog/changelog.sh [options]

Options:
  --from REF       Start after this tag/ref instead of the latest tag
  --version NAME   Version heading to use instead of the current date
  --output FILE    Output file path (default: CHANGELOG.md)
  --dry-run        Print changelog to stdout without writing a file
  -h, --help       Show this help
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --from)
      from_ref="${2:-}"
      shift 2
      ;;
    --version)
      version="${2:-}"
      shift 2
      ;;
    --output)
      output_file="${2:-}"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: this command must run inside a git repository." >&2
  exit 1
fi

if [ -z "$version" ]; then
  version="$(date +%Y-%m-%d)"
fi

if [ -z "$from_ref" ]; then
  from_ref="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [ -n "$from_ref" ]; then
  range="${from_ref}..HEAD"
  source_label="since ${from_ref}"
else
  range="HEAD"
  source_label="from repository history"
fi

format_commit() {
  local subject="$1"
  local hash="$2"
  subject="${subject#*: }"
  subject="${subject#*:}"
  subject="$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+//')"
  printf -- "- %s (%s)\n" "$subject" "$hash"
}

category_for() {
  local subject="$1"
  case "$subject" in
    feat:*|feat\(*)
      printf '%s' "Added"
      ;;
    fix:*|fix\(*)
      printf '%s' "Fixed"
      ;;
    remove:*|removed:*|rm:*|delete:*|deleted:*|revert:*)
      printf '%s' "Removed"
      ;;
    chore:*|docs:*|doc:*|style:*|refactor:*|perf:*|test:*|ci:*|build:*|changed:*)
      printf '%s' "Changed"
      ;;
    *)
      printf '%s' "Changed"
      ;;
  esac
}

added=""
fixed=""
changed=""
removed=""

mapfile -t commits < <(git log "$range" --no-merges --pretty=format:'%h%x09%s')

for commit in "${commits[@]}"; do
  [ -n "${commit:-}" ] || continue
  hash="${commit%%$'\t'*}"
  subject="${commit#*$'\t'}"
  category="$(category_for "$subject")"
  line="$(format_commit "$subject" "$hash")"
  line="${line}"$'\n'
  case "$category" in
    Added) added="${added}${line}" ;;
    Fixed) fixed="${fixed}${line}" ;;
    Changed) changed="${changed}${line}" ;;
    Removed) removed="${removed}${line}" ;;
  esac
done

section() {
  local title="$1"
  local body="$2"
  if [ -n "$body" ]; then
    printf '### %s\n\n%s\n' "$title" "$body"
  fi
}

tmp_file="$(mktemp)"
{
  printf '# Changelog\n\n'
  printf 'All notable changes are documented in this file.\n\n'
  printf '## [%s] - %s\n\n' "$version" "$(date +%Y-%m-%d)"
  printf '_Generated from git commits %s._\n\n' "$source_label"
  section "Added" "$added"
  section "Fixed" "$fixed"
  section "Changed" "$changed"
  section "Removed" "$removed"
} > "$tmp_file"
trimmed_file="$(mktemp)"
awk '
  { lines[NR] = $0 }
  END {
    last = NR
    while (last > 0 && lines[last] == "") {
      last--
    }
    for (i = 1; i <= last; i++) {
      print lines[i]
    }
  }
' "$tmp_file" > "$trimmed_file"
mv "$trimmed_file" "$tmp_file"

if [ "$dry_run" -eq 1 ]; then
  cat "$tmp_file"
  rm -f "$tmp_file"
else
  mv "$tmp_file" "$output_file"
  echo "Wrote ${output_file}"
fi
