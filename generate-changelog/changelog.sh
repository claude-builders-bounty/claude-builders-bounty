#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
FROM_REF=""
TO_REF="HEAD"
DRY_RUN=0

usage() {
  cat <<'USAGE'
Generate a structured CHANGELOG.md from git history.

Usage:
  bash generate-changelog/changelog.sh [options]

Options:
  --output <file>   Write changelog to this path. Default: CHANGELOG.md
  --from <ref>      Start after this tag/commit. Default: latest git tag
  --to <ref>        End at this ref. Default: HEAD
  --dry-run         Print changelog instead of writing it
  -h, --help        Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      OUTPUT_FILE="${2:-}"
      [[ -n "$OUTPUT_FILE" ]] || { echo "Missing value for --output" >&2; exit 2; }
      shift 2
      ;;
    --from)
      FROM_REF="${2:-}"
      [[ -n "$FROM_REF" ]] || { echo "Missing value for --from" >&2; exit 2; }
      shift 2
      ;;
    --to)
      TO_REF="${2:-}"
      [[ -n "$TO_REF" ]] || { echo "Missing value for --to" >&2; exit 2; }
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
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: run this script inside a git repository." >&2
  exit 1
fi

if [[ -z "$FROM_REF" ]]; then
  FROM_REF="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$FROM_REF" ]]; then
  RANGE="${FROM_REF}..${TO_REF}"
  RANGE_LABEL="commits since ${FROM_REF}"
else
  RANGE="${TO_REF}"
  RANGE_LABEL="the full git history because no tag was found"
fi

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

clean_subject() {
  local subject="$1"
  subject="${subject#*: }"
  subject="${subject#*:}"
  printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g'
}

append_entry() {
  local category="$1"
  local message="$2"
  local hash="$3"
  local entry="- ${message} (${hash})"

  case "$category" in
    added) ADDED+=("$entry") ;;
    fixed) FIXED+=("$entry") ;;
    removed) REMOVED+=("$entry") ;;
    changed) CHANGED+=("$entry") ;;
  esac
}

while IFS=$'\t' read -r hash subject; do
  [[ -n "${hash:-}" && -n "${subject:-}" ]] || continue

  lower_subject="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  message="$(clean_subject "$subject")"

  if [[ "$lower_subject" =~ ^(feat|feature|add)(\(.+\))?!?: ]]; then
    append_entry added "$message" "$hash"
  elif [[ "$lower_subject" =~ ^(fix|bugfix|hotfix|patch)(\(.+\))?!?: ]]; then
    append_entry fixed "$message" "$hash"
  elif [[ "$lower_subject" =~ ^(remove|delete|drop|deprecate)(\(.+\))?!?: ]]; then
    append_entry removed "$message" "$hash"
  else
    append_entry changed "$message" "$hash"
  fi
done < <(git log "$RANGE" --no-merges --format='%h%x09%s')

print_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '### %s\n\n' "$title"
  if [[ "${#entries[@]}" -eq 0 ]]; then
    printf -- '- None\n\n'
    return
  fi

  printf '%s\n' "${entries[@]}"
  printf '\n'
}

CHANGELOG_CONTENT="$(
  {
    printf '# Changelog\n\n'
    printf 'Generated on %s from %s through `%s`.\n\n' "$(date +%Y-%m-%d)" "$RANGE_LABEL" "$TO_REF"
    printf '## Unreleased\n\n'
    print_section "Added" "${ADDED[@]}"
    print_section "Fixed" "${FIXED[@]}"
    print_section "Changed" "${CHANGED[@]}"
    print_section "Removed" "${REMOVED[@]}"
  }
)"

if [[ "$DRY_RUN" -eq 1 ]]; then
  printf '%s\n' "$CHANGELOG_CONTENT"
else
  mkdir -p "$(dirname "$OUTPUT_FILE")"
  printf '%s\n' "$CHANGELOG_CONTENT" > "$OUTPUT_FILE"
  echo "Wrote ${OUTPUT_FILE}"
fi

