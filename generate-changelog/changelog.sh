#!/usr/bin/env bash
set -euo pipefail

repo_path="."
output_file="CHANGELOG.md"
title="Changelog"
include_hashes="1"

usage() {
  cat <<'USAGE'
Generate a structured CHANGELOG.md from git history.

Usage:
  bash generate-changelog/changelog.sh [options]

Options:
  --repo PATH       Git repository to read. Default: current directory.
  --output PATH     Output file path. Default: CHANGELOG.md.
  --title TEXT      Markdown title. Default: Changelog.
  --no-hashes       Omit short commit hashes from entries.
  -h, --help        Show this help text.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo_path="${2:?Missing value for --repo}"
      shift 2
      ;;
    --output)
      output_file="${2:?Missing value for --output}"
      shift 2
      ;;
    --title)
      title="${2:?Missing value for --title}"
      shift 2
      ;;
    --no-hashes)
      include_hashes="0"
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

cd "$repo_path"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not inside a git repository: $repo_path" >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  git_range=("$last_tag..HEAD")
  range_label="since tag \`$last_tag\`"
else
  git_range=("HEAD")
  range_label="from all commits because no git tags were found"
fi

tmp_log="$(mktemp)"
trap 'rm -f "$tmp_log"' EXIT

git log --no-merges --reverse --format='%s%x09%h' "${git_range[@]}" > "$tmp_log"

categorize_commit() {
  local subject_lc
  subject_lc="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  if [[ "$subject_lc" =~ ^(revert|remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)(\(.+\))?!?:? ]]; then
    echo "Removed"
  elif [[ "$subject_lc" =~ ^(fix|fixed|bugfix|bug|repair|repaired|resolve|resolved)(\(.+\))?!?:? ]]; then
    echo "Fixed"
  elif [[ "$subject_lc" =~ ^(feat|feature|add|added|create|created|implement|implemented|introduce|introduced)(\(.+\))?!?:? ]]; then
    echo "Added"
  elif [[ "$subject_lc" =~ ^(docs|doc|chore|refactor|perf|build|ci|test|style|update|updated|change|changed|improve|improved)(\(.+\))?!?:? ]]; then
    echo "Changed"
  else
    echo "Changed"
  fi
}

added=()
fixed=()
changed=()
removed=()

while IFS=$'\t' read -r subject sha; do
  [[ -z "${subject// }" ]] && continue

  entry="- $subject"
  if [[ "$include_hashes" == "1" && -n "${sha:-}" ]]; then
    entry="$entry ($sha)"
  fi

  case "$(categorize_commit "$subject")" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
done < "$tmp_log"

write_section() {
  local heading="$1"
  shift

  printf '## %s\n\n' "$heading"
  if [[ $# -eq 0 ]]; then
    printf '_No entries._\n'
  else
    printf '%s\n' "$@"
  fi
}

{
  printf '# %s\n\n' "$title"
  printf 'Generated on %s %s.\n\n' "$(date +%Y-%m-%d)" "$range_label"
  write_section "Added" "${added[@]}"
  printf '\n'
  write_section "Fixed" "${fixed[@]}"
  printf '\n'
  write_section "Changed" "${changed[@]}"
  printf '\n'
  write_section "Removed" "${removed[@]}"
} > "$output_file"

echo "Wrote $output_file"
