#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-CHANGELOG.md}"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must run inside a Git repository" >&2
  exit 2
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  range="$last_tag..HEAD"
  since_label="since $last_tag"
else
  range="HEAD"
  since_label="from repository start"
fi

declare -A buckets
for section in Added Fixed Changed Removed; do buckets[$section]=""; done

categorize() {
  local subject="${1,,}"
  case "$subject" in
    feat:*|feat\(*|add:*|add\ *|create:*|create\ *|introduce:*|introduce\ *|new:*|new\ *) echo Added ;;
    fix:*|fix\(*|bugfix:*|bugfix\ *|repair:*|repair\ *) echo Fixed ;;
    remove:*|remove\(*|remove\ *|delete:*|delete\ *|drop:*|drop\ *) echo Removed ;;
    *) echo Changed ;;
  esac
}

while IFS=$'\x1f' read -r sha subject; do
  [[ -z "${sha:-}" ]] && continue
  section="$(categorize "$subject")"
  short="${sha:0:7}"
  buckets[$section]+="- ${subject} (\`${short}\`)"$'\n'
done < <(git log --no-merges --pretty=format:'%H%x1f%s%n' "$range")

{
  echo "# Changelog"
  echo
  echo "All notable changes for the current unreleased range (${since_label})."
  echo
  echo "## Unreleased"
  echo
  for section in Added Fixed Changed Removed; do
    echo "### $section"
    if [[ -n "${buckets[$section]}" ]]; then
      printf '%s' "${buckets[$section]}"
    else
      echo "- None."
    fi
    echo
  done
} > "$OUT"

echo "Wrote $OUT ($since_label)"
