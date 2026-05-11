#!/usr/bin/env bash
set -euo pipefail

if ! git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

cd "$git_root"

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  cat > CHANGELOG.md <<'EOF'
# Changelog

## Unreleased

_No commits found._
EOF
  echo "Generated CHANGELOG.md"
  exit 0
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  log_range="${latest_tag}..HEAD"
  range_description="after ${latest_tag}"
else
  log_range="HEAD"
  range_description="from the full git history"
fi

added=()
fixed=()
changed=()
removed=()

strip_commit_prefix() {
  printf '%s' "$1" | sed -E 's/^([A-Za-z]+)(\([^)]+\))?(!)?:[[:space:]]*//'
}

category_for_subject() {
  local subject="$1"
  local lower
  local added_type='^(feat|feature|add|added|new)(\([^)]+\))?(!)?:'
  local fixed_type='^(fix|fixed|bug|bugfix|hotfix)(\([^)]+\))?(!)?:'
  local removed_type='^(remove|removed|delete|deleted|deprecate|deprecated)(\([^)]+\))?(!)?:'
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower" =~ $added_type ]] ||
     [[ "$lower" =~ ^(add|added|new)[[:space:]] ]]; then
    echo "added"
  elif [[ "$lower" =~ $fixed_type ]] ||
       [[ "$lower" =~ ^(fix|fixed|bugfix)[[:space:]] ]]; then
    echo "fixed"
  elif [[ "$lower" =~ $removed_type ]] ||
       [[ "$lower" =~ ^(remove|removed|delete|deleted|deprecate|deprecated)[[:space:]] ]]; then
    echo "removed"
  else
    echo "changed"
  fi
}

while IFS=$'\x1f' read -r subject hash || [[ -n "${subject:-}" ]]; do
  [[ -z "${subject:-}" ]] && continue

  clean_subject="$(strip_commit_prefix "$subject")"
  entry="- ${clean_subject} (${hash})"

  case "$(category_for_subject "$subject")" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    removed) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
done < <(git log --no-merges --reverse --pretty=format:'%s%x1f%h' "$log_range")

write_section() {
  local title="$1"
  shift

  echo "### ${title}"
  if [[ "$#" -eq 0 ]]; then
    echo "- No changes."
  else
    printf '%s\n' "$@"
  fi
  echo
}

{
  echo "# Changelog"
  echo
  echo "## Unreleased - $(date +%Y-%m-%d)"
  echo
  echo "_Generated from git commits ${range_description}._"
  echo
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > CHANGELOG.md

echo "Generated CHANGELOG.md"
