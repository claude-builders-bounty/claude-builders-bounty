#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: this command must be run inside a git repository." >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
if [ -z "$repo_root" ] || ! cd "$repo_root"; then
  echo "Error: failed to resolve repository root." >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$latest_tag" ]; then
  rev_range="$latest_tag..HEAD"
  source_label="since tag $latest_tag"
else
  rev_range="--all"
  source_label="entire commit history (no tags found)"
fi

echo "# Changelog" > CHANGELOG.md
echo >> CHANGELOG.md
echo "Generated on $(date -u +"%Y-%m-%d %H:%M:%SZ") from $source_label." >> CHANGELOG.md
echo >> CHANGELOG.md
echo "## [Unreleased]" >> CHANGELOG.md
echo >> CHANGELOG.md

declare -a added fixed changed removed

while IFS='|' read -r hash date subject
do
  lower_subject="$(printf "%s" "$subject" | tr '[:upper:]' '[:lower:]')"
  if [[ "$lower_subject" =~ ^(feat|feature|add|added|implement|create)(\(|\s|:|-) ]]; then
    added+=("$hash $date $subject")
  elif [[ "$lower_subject" =~ ^(fix|fixed|patch|bugfix|hotfix)(\(|\s|:|-) ]]; then
    fixed+=("$hash $date $subject")
  elif [[ "$lower_subject" =~ ^(remove|removed|delete|deprecate|deprecation)(\(|\s|:|-) ]]; then
    removed+=("$hash $date $subject")
  else
    changed+=("$hash $date $subject")
  fi
done < <(git log --no-merges --date=short --pretty=format:'%h|%ad|%s' "$rev_range" --reverse)

write_section() {
  local title="$1"
  local -n entries="$2"

  echo "### $title" >> CHANGELOG.md
  echo >> CHANGELOG.md
  if [ ${#entries[@]} -eq 0 ]; then
    echo "- _No entries_" >> CHANGELOG.md
  else
    for item in "${entries[@]}"; do
      local commit="${item%% *}"
      local rest="${item#* }"
      local commit_date="${rest%% *}"
      local commit_msg="${item#${commit} ${commit_date} }"
      echo "- [$commit_date] $commit_msg ($commit)" >> CHANGELOG.md
    done
  fi
  echo >> CHANGELOG.md
}

write_section "Added" "${added[@]}"
write_section "Fixed" "${fixed[@]}"
write_section "Changed" "${changed[@]}"
write_section "Removed" "${removed[@]}"

echo "CHANGELOG.md generated successfully."
