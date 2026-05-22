#!/usr/bin/env bash
set -euo pipefail

repo="."
output="CHANGELOG.md"
from_ref=""
to_ref="HEAD"

usage() {
  cat <<'USAGE'
Usage: bash scripts/generate-changelog.sh [options]

Options:
  --repo PATH       Git repository to inspect. Defaults to current directory.
  --output PATH     Changelog file to write. Defaults to CHANGELOG.md.
  --from REF        Start ref, exclusive. Defaults to latest reachable tag.
  --to REF          End ref, inclusive. Defaults to HEAD.
  --stdout          Print changelog instead of writing a file.
  -h, --help        Show this help.
USAGE
}

write_to_stdout=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:?Missing value for --repo}"
      shift 2
      ;;
    --output)
      output="${2:?Missing value for --output}"
      shift 2
      ;;
    --from)
      from_ref="${2:?Missing value for --from}"
      shift 2
      ;;
    --to)
      to_ref="${2:?Missing value for --to}"
      shift 2
      ;;
    --stdout)
      write_to_stdout=true
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

if ! git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $repo" >&2
  exit 1
fi

if [[ -z "$from_ref" ]]; then
  if from_ref="$(git -C "$repo" describe --tags --abbrev=0 "$to_ref" 2>/dev/null)"; then
    range="$from_ref..$to_ref"
    range_label="$from_ref..$to_ref"
  else
    range="$to_ref"
    range_label="initial history..$to_ref"
  fi
else
  range="$from_ref..$to_ref"
  range_label="$from_ref..$to_ref"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added="$tmp_dir/added"
fixed="$tmp_dir/fixed"
changed="$tmp_dir/changed"
removed="$tmp_dir/removed"
: > "$added"
: > "$fixed"
: > "$changed"
: > "$removed"

commit_count=0

while IFS=$'\t' read -r hash subject || [[ -n "${hash:-}" ]]; do
  [[ -z "${hash:-}" ]] && continue
  commit_count=$((commit_count + 1))
  subject="${subject//$'\r'/}"
  line="- ${subject} (${hash})"
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    feat:*|feat\(*|feature:*|add:*|added:*|new:*)
      printf '%s\n' "$line" >> "$added"
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*|repair:*)
      printf '%s\n' "$line" >> "$fixed"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|deprecated:*|deprecate:*|breaking:*)
      printf '%s\n' "$line" >> "$removed"
      ;;
    *)
      printf '%s\n' "$line" >> "$changed"
      ;;
  esac
done < <(git -C "$repo" log "$range" --date-order --reverse --pretty=format:'%h%x09%s')

today="$(date +%Y-%m-%d)"

render_section() {
  local title="$1"
  local file="$2"

  printf '### %s\n\n' "$title"
  if [[ -s "$file" ]]; then
    cat "$file"
  else
    printf -- '- No changes.\n'
  fi
}

changelog="$tmp_dir/changelog"
{
  printf '# Changelog\n\n'
  printf '## %s\n\n' "$today"
  printf 'Generated from `%s` with %s commit(s).\n\n' "$range_label" "$commit_count"
  render_section "Added" "$added"
  printf '\n'
  render_section "Fixed" "$fixed"
  printf '\n'
  render_section "Changed" "$changed"
  printf '\n'
  render_section "Removed" "$removed"
} > "$changelog"

if [[ "$write_to_stdout" == true ]]; then
  cat "$changelog"
else
  cp "$changelog" "$output"
  echo "Wrote $output from $commit_count commit(s)."
fi
