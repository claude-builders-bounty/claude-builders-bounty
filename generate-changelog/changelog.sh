#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${CHANGELOG_OUTPUT:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
cd "$REPO_ROOT"

last_tag=""
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  last_tag="$(git describe --tags --abbrev=0)"
  range="${last_tag}..HEAD"
else
  range="HEAD"
fi

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "No git commits found." >&2
  exit 1
fi

commit_lines="$(git log --no-merges --format='%s%x1f%h' "$range")"

if [[ -z "$commit_lines" ]]; then
  {
    echo "# Changelog"
    echo
    if [[ -n "$last_tag" ]]; then
      echo "No changes since ${last_tag}."
    else
      echo "No commits found."
    fi
  } > "$OUTPUT_FILE"
  echo "Wrote $OUTPUT_FILE"
  exit 0
fi

added=()
fixed=()
changed=()
removed=()

append_entry() {
  local category="$1"
  local subject="$2"
  local hash="$3"
  local entry="- ${subject} (${hash})"
  case "$category" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
    Changed) changed+=("$entry") ;;
  esac
}

categorize() {
  local subject_lc="$1"
  case "$subject_lc" in
    feat:*|feat\(*|add:*|added:*|implement:*|implemented:*) echo "Added" ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*|repair:*|patched:*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|deprecate:*|deprecated:*) echo "Removed" ;;
    *)
      if [[ "$subject_lc" =~ (^|[[:space:]])(fix|fixed|bug|bugfix|resolve|resolved)([[:space:]]|$) ]]; then
        echo "Fixed"
      elif [[ "$subject_lc" =~ (^|[[:space:]])(remove|removed|delete|deleted|deprecate|deprecated)([[:space:]]|$) ]]; then
        echo "Removed"
      elif [[ "$subject_lc" =~ (^|[[:space:]])(add|added|new|introduce|introduced|implement|implemented)([[:space:]]|$) ]]; then
        echo "Added"
      else
        echo "Changed"
      fi
      ;;
  esac
}

while IFS=$'\x1f' read -r subject hash; do
  [[ -z "${subject:-}" ]] && continue
  category="$(categorize "$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')")"
  append_entry "$category" "$subject" "$hash"
done <<< "$commit_lines"

write_section() {
  local title="$1"
  shift
  local entries=("$@")
  [[ ${#entries[@]} -eq 0 ]] && return
  echo "## $title"
  echo
  printf '%s\n' "${entries[@]}"
  echo
}

{
  echo "# Changelog"
  echo
  echo "Generated from git history on $(date -u +%Y-%m-%d)."
  if [[ -n "$last_tag" ]]; then
    echo
    echo "Changes since tag \`$last_tag\`."
  fi
  echo
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$OUTPUT_FILE"

echo "Wrote $OUTPUT_FILE"
