#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/generate_changelog.sh [--from <ref>] [--to <ref>] [--output <file>]

Generates a Markdown changelog from git commit history.

Options:
  --from <ref>     Start ref. Defaults to latest tag, or first commit if no tag exists.
  --to <ref>       End ref. Defaults to HEAD.
  --output <file>  Write changelog to a file instead of stdout.
  -h, --help       Show this help message.
USAGE
}

from_ref=""
to_ref="HEAD"
output_file=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)
      from_ref="${2:?--from requires a ref}"
      shift 2
      ;;
    --to)
      to_ref="${2:?--to requires a ref}"
      shift 2
      ;;
    --output)
      output_file="${2:?--output requires a file path}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null

if [[ -z "$from_ref" ]]; then
  if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    from_ref="$(git describe --tags --abbrev=0)"
  else
    from_ref="$(git rev-list --max-parents=0 "$to_ref" | tail -n 1)"
  fi
fi

if [[ "$from_ref" == "$to_ref" ]]; then
  range="$to_ref"
else
  range="${from_ref}..${to_ref}"
fi

today="$(date +%Y-%m-%d)"
repo_name="$(basename "$(git rev-parse --show-toplevel)")"

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

cat >"$tmp_file" <<HEADER
# Changelog

## ${today}

Generated from \`${repo_name}\` commits in \`${range}\`.

HEADER

append_section() {
  local title="$1"
  local pattern="$2"
  local commits

  commits="$(git log "$range" --pretty=format:'- %s (%h)' --grep="$pattern" --extended-regexp --regexp-ignore-case || true)"
  if [[ -n "$commits" ]]; then
    {
      printf '### %s\n\n' "$title"
      printf '%s\n\n' "$commits"
    } >>"$tmp_file"
  fi
}

append_section "Features" '^(feat|feature)(\(.+\))?:|add|create|implement|introduce'
append_section "Fixes" '^(fix|bugfix)(\(.+\))?:|fix|repair|resolve|prevent'
append_section "Documentation" '^(docs)(\(.+\))?:|readme|doc|documentation'
append_section "Maintenance" '^(chore|refactor|test|ci|build)(\(.+\))?:|test|refactor|cleanup|ci|build'

all_section="$(git log "$range" --pretty=format:'- %s (%h)' || true)"
if [[ -z "$all_section" ]]; then
  printf 'No commits found for this range.\n' >>"$tmp_file"
else
  {
    printf '### All Commits\n\n'
    printf '%s\n' "$all_section"
  } >>"$tmp_file"
fi

if [[ -n "$output_file" ]]; then
  cp "$tmp_file" "$output_file"
else
  cat "$tmp_file"
fi
