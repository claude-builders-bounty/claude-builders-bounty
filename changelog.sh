#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./changelog.sh [OUTPUT] [REPOSITORY]

Generate OUTPUT (default: CHANGELOG.md) from commits after the latest git tag.
REPOSITORY defaults to the current directory.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

output="${1:-CHANGELOG.md}"
repo="${2:-.}"

if ! git -C "$repo" rev-parse --git-dir >/dev/null 2>&1; then
  echo "error: '$repo' is not a git repository" >&2
  exit 1
fi

if [[ "$output" != /* ]]; then
  output="$(pwd)/$output"
fi
mkdir -p "$(dirname "$output")"

latest_tag="$(git -C "$repo" describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="$latest_tag..HEAD"
  range_label="after $latest_tag"
else
  range="HEAD"
  range_label="the beginning of history (no tags found)"
fi

remote_url="$(git -C "$repo" remote get-url origin 2>/dev/null || true)"
if [[ "$remote_url" == git@github.com:* ]]; then
  remote_url="https://github.com/${remote_url#git@github.com:}"
fi
remote_url="${remote_url%.git}"

declare -A entries
for category in Added Fixed Changed Removed; do
  entries["$category"]=""
done

classify() {
  local subject="${1,,}"
  local head="${subject%%:*}"
  head="${head%% *}"
  head="${head%%(*}"
  head="${head//[^a-z0-9]/}"

  case "$head" in
    feat|add|new|implement|create|introduce) printf '%s' Added ;;
    fix|fixed|bug|repair|resolve|correct|patch) printf '%s' Fixed ;;
    remove|removed|delete|deleted|drop|deprecate) printf '%s' Removed ;;
    *) printf '%s' Changed ;;
  esac
}

while IFS=$'\t' read -r hash date subject; do
  [[ -z "${hash:-}" ]] && continue
  category="$(classify "$subject")"
  if [[ -n "$remote_url" ]]; then
    entry="- ${subject} ([${hash}](${remote_url}/commit/${hash})) — ${date}"
  else
    entry="- ${subject} (${hash}) — ${date}"
  fi
  if [[ -n "${entries[$category]}" ]]; then
    entries["$category"]+=$'\n'
  fi
  entries["$category"]+="$entry"
done < <(git -C "$repo" log --no-merges --date=short --format='%h%x09%ad%x09%s' "$range")

{
  printf '%s\n\n' '# Changelog'
  printf '%s\n\n' "Generated from git history (${range_label})."
  printf '%s\n\n' '## [Unreleased]'

  for category in Added Fixed Changed Removed; do
    printf '### %s\n' "$category"
    if [[ -n "${entries[$category]}" ]]; then
      printf '%s\n\n' "${entries[$category]}"
    else
      printf '%s\n\n' '- None.'
    fi
  done
} > "$output"

echo "Wrote $output"
