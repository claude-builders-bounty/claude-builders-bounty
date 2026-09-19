#!/usr/bin/env bash
set -euo pipefail

# Changelog generator
# Usage: bash changelog.sh or /generate-changelog
if [[ "${1-}" == "/generate-changelog" || "${1-}" == "generate-changelog" ]]; then
  shift
fi

# Ensure we're inside a git repository
if ! git rev-parse --show-toplevel > /dev/null 2>&1; then
  echo "Error: run this script inside a git repository" >&2
  exit 1
fi

last_tag=""
if git describe --tags --abbrev=0 > /dev/null 2>&1; then
  last_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
fi

if [[ -n "$last_tag" ]]; then
  range="$last_tag..HEAD"
  tag_label="$last_tag"
else
  range="HEAD"
  tag_label="start"
fi

commits=$(git log ${range} --no-merges --pretty=format:"%h:::%s" 2>/dev/null || true)

added=""
fixed=""
changed=""
removed=""

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  commit_hash=${line%%:::*}
  subject=${line#*:::}
  lower_subject="${subject,,}"

  if [[ "$lower_subject" =~ ^add || "$lower_subject" =~ ^feat || "$lower_subject" =~ ^feature ]]; then
    added+="- ${commit_hash} ${subject}\n"
  elif [[ "$lower_subject" =~ ^fix || "$lower_subject" =~ bug || "$lower_subject" =~ hotfix ]]; then
    fixed+="- ${commit_hash} ${subject}\n"
  elif [[ "$lower_subject" =~ ^remove || "$lower_subject" =~ delete || "$lower_subject" =~ drop ]]; then
    removed+="- ${commit_hash} ${subject}\n"
  else
    changed+="- ${commit_hash} ${subject}\n"
  fi
done <<< "$commits"

output_section() {
  local content="$1"
  if [[ -n "$content" ]]; then
    printf "%b" "$content"
  else
    echo "- None"
  fi
}

{
  echo "# CHANGELOG"
  echo
  echo "## Unreleased (since ${tag_label}) - $(date +%Y-%m-%d)"
  echo
  echo "### Added"
  output_section "$added"
  echo
  echo "### Fixed"
  output_section "$fixed"
  echo
  echo "### Changed"
  output_section "$changed"
  echo
  echo "### Removed"
  output_section "$removed"
} > CHANGELOG.md

commit_count=$(printf "%s" "$commits" | grep -c "." || true)
echo "CHANGELOG.md updated with ${commit_count} commit(s) since ${tag_label}."
