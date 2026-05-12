#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$latest_tag" ]]; then
  commit_range="${latest_tag}..HEAD"
  range_label="Changes since ${latest_tag}"
else
  commit_range="HEAD"
  range_label="Changes from git history"
fi

if ! git rev-list --quiet --count "$commit_range" >/dev/null 2>&1; then
  echo "Error: unable to read git history for ${commit_range}." >&2
  exit 1
fi

commit_count="$(git rev-list --count "$commit_range")"

if [[ "$commit_count" == "0" ]]; then
  cat > CHANGELOG.md <<EOF
# Changelog

## Unreleased

No changes since the last git tag.
EOF
  echo "Generated CHANGELOG.md with no unreleased changes."
  exit 0
fi

work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT

added_file="${work_dir}/added"
fixed_file="${work_dir}/fixed"
changed_file="${work_dir}/changed"
removed_file="${work_dir}/removed"

touch "$added_file" "$fixed_file" "$changed_file" "$removed_file"

normalize_subject() {
  local subject="$1"

  subject="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  subject="$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"

  printf '%s' "$subject"
}

git log --reverse --format=%s "$commit_range" | while IFS= read -r subject; do
  normalized_subject="$(normalize_subject "$subject")"
  lowercase_subject="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lowercase_subject" in
    feat:*|feature:*|add:*|added:*|add\ *|added\ *)
      printf -- "- %s\n" "$normalized_subject" >> "$added_file"
      ;;
    fix:*|bugfix:*|hotfix:*|fixed:*|fix\ *|fixed\ *)
      printf -- "- %s\n" "$normalized_subject" >> "$fixed_file"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|remove\ *|removed\ *|delete\ *|deleted\ *|drop\ *|dropped\ *)
      printf -- "- %s\n" "$normalized_subject" >> "$removed_file"
      ;;
    *)
      printf -- "- %s\n" "$normalized_subject" >> "$changed_file"
      ;;
  esac
done

{
  echo "# Changelog"
  echo
  echo "## Unreleased"
  echo
  echo "_${range_label}_"
  echo

  if [[ -s "$added_file" ]]; then
    echo "### Added"
    cat "$added_file"
    echo
  fi

  if [[ -s "$fixed_file" ]]; then
    echo "### Fixed"
    cat "$fixed_file"
    echo
  fi

  if [[ -s "$changed_file" ]]; then
    echo "### Changed"
    cat "$changed_file"
    echo
  fi

  if [[ -s "$removed_file" ]]; then
    echo "### Removed"
    cat "$removed_file"
    echo
  fi
} > CHANGELOG.md

echo "Generated CHANGELOG.md from ${commit_count} commit(s)."
