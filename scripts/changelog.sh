#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

git_root="$(git rev-parse --show-toplevel)"
cd "$git_root"

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$last_tag" ]; then
  commit_range="${last_tag}..HEAD"
  range_note="Changes since \`${last_tag}\`."
else
  commit_range="HEAD"
  range_note="Changes from the full git history because no tag was found."
fi

commit_count="$(git rev-list --count "$commit_range" 2>/dev/null || echo 0)"
generated_date="$(date +%Y-%m-%d)"

added=()
fixed=()
changed=()
removed=()

while IFS=$'\t' read -r hash subject; do
  [ -n "${hash:-}" ] || continue

  lower_subject="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  line="- ${subject} (${hash})"

  case "$lower_subject" in
    feat:*|feat\(*|add*|create*|implement*|introduce*|support*)
      added+=("$line")
      ;;
    fix:*|fix\(*|bug*|repair*|resolve*|correct*|patch*)
      fixed+=("$line")
      ;;
    remove*|delete*|drop*|deprecate*)
      removed+=("$line")
      ;;
    *)
      changed+=("$line")
      ;;
  esac
done < <(git log --reverse --format='%h%x09%s' "$commit_range")

repo_url="$(git config --get remote.origin.url 2>/dev/null || true)"
repo_url="${repo_url%.git}"
if [[ "$repo_url" == git@github.com:* ]]; then
  repo_url="https://github.com/${repo_url#git@github.com:}"
fi

compare_url=""
if [ -n "$last_tag" ] && [[ "$repo_url" == https://github.com/* ]]; then
  compare_url="${repo_url}/compare/${last_tag}...HEAD"
fi

output_dir="$(dirname "$output_file")"
mkdir -p "$output_dir"
tmp_file="$(mktemp)"

{
  echo "# Changelog"
  echo
  echo "## Unreleased - ${generated_date}"
  echo
  echo "${range_note}"
  if [ -n "$compare_url" ]; then
    echo
    echo "Compare: ${compare_url}"
  fi
  echo
  echo "Commit count: ${commit_count}"
  echo
  echo "### Added"
  if [ "${#added[@]}" -eq 0 ]; then
    echo "- None"
  else
    printf '%s\n' "${added[@]}"
  fi
  echo
  echo "### Fixed"
  if [ "${#fixed[@]}" -eq 0 ]; then
    echo "- None"
  else
    printf '%s\n' "${fixed[@]}"
  fi
  echo
  echo "### Changed"
  if [ "${#changed[@]}" -eq 0 ]; then
    echo "- None"
  else
    printf '%s\n' "${changed[@]}"
  fi
  echo
  echo "### Removed"
  if [ "${#removed[@]}" -eq 0 ]; then
    echo "- None"
  else
    printf '%s\n' "${removed[@]}"
  fi
} > "$tmp_file"

mv "$tmp_file" "$output_file"
echo "Generated ${output_file}"
