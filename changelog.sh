#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./changelog.sh [--repo PATH] [--output PATH] [--range REV_RANGE]

Generate a structured CHANGELOG.md from git history.

Options:
  --repo PATH       Git repository to inspect. Defaults to current directory.
  --output PATH     Output file. Defaults to CHANGELOG.md in the repo.
  --range RANGE     Git revision range, for example v1.0.0..HEAD.
                   Defaults to commits since the latest tag, or all history.
USAGE
}

repo="."
output=""
range=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --output)
      output="${2:-}"
      shift 2
      ;;
    --range)
      range="${2:-}"
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

if [[ ! -d "$repo/.git" ]]; then
  echo "Not a git repository: $repo" >&2
  exit 1
fi

if [[ -z "$output" ]]; then
  output="$repo/CHANGELOG.md"
fi

git_in_repo() {
  git -C "$repo" "$@"
}

latest_tag=""
range_label=""

if [[ -z "$range" ]]; then
  if latest_tag="$(git_in_repo describe --tags --abbrev=0 2>/dev/null)"; then
    range="${latest_tag}..HEAD"
    range_label="Changes since ${latest_tag}"
  else
    range="HEAD"
    range_label="All repository history"
  fi
else
  range_label="Changes in ${range}"
fi

categorize() {
  local subject
  subject="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  case "$subject" in
    feat:*|feat\(*|add*|added*|create*|implement*|introduce*|initial*)
      printf 'Added'
      ;;
    fix:*|fix\(*|fixed*|bug*|patch*|repair*|resolve*)
      printf 'Fixed'
      ;;
    remove*|delete*|drop*|deprecat*)
      printf 'Removed'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

added=""
fixed=""
changed=""
removed=""

while IFS=$'\x1f' read -r hash subject body || [[ -n "${hash:-}" ]]; do
  [[ -z "${hash:-}" || -z "${subject:-}" ]] && continue
  short_hash="${hash:0:7}"
  category="$(categorize "$subject")"
  entry="- ${subject} (${short_hash})"

  case "$category" in
    Added) added+="${entry}"$'\n' ;;
    Fixed) fixed+="${entry}"$'\n' ;;
    Removed) removed+="${entry}"$'\n' ;;
    *) changed+="${entry}"$'\n' ;;
  esac
done < <(git_in_repo log --no-merges --pretty=format:'%H%x1f%s%x1f%b' "$range")

write_section() {
  local title="$1"
  local entries="$2"
  printf '### %s\n\n' "$title"
  if [[ -n "$entries" ]]; then
    printf '%s\n' "$entries"
  else
    printf '%s\n' '- No changes.'
  fi
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased\n\n'
  printf '_%s_\n\n' "$range_label"
  write_section "Added" "$added"
  write_section "Fixed" "$fixed"
  write_section "Changed" "$changed"
  write_section "Removed" "$removed"
} > "$tmp"

cp "$tmp" "$output"
printf 'Wrote %s\n' "$output"
