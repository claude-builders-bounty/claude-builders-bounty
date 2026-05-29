#!/usr/bin/env bash
set -euo pipefail

output_path="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must run inside a git repository" >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  range="HEAD"
  range_label="full history"
fi

repo_url="$(git config --get remote.origin.url || true)"
repo_url="${repo_url%.git}"
if [[ "$repo_url" == git@github.com:* ]]; then
  repo_url="https://github.com/${repo_url#git@github.com:}"
fi

today="$(date +%Y-%m-%d)"
output_dir="$(dirname "$output_path")"
if [[ "$output_dir" != "." ]]; then
  mkdir -p "$output_dir"
fi
added=()
fixed=()
changed=()
removed=()
commit_count=0

commit_url() {
  local hash="$1"
  if [[ "$repo_url" == https://github.com/* ]]; then
    printf "[%s](%s/commit/%s)" "${hash:0:7}" "$repo_url" "$hash"
  else
    printf "%s" "${hash:0:7}"
  fi
}

categorize_subject() {
  local subject_lower="$1"
  case "$subject_lower" in
    feat:*|feature:*|add:*|added:*|*add\ *|*introduce\ *)
      printf "Added"
      ;;
    fix:*|bug:*|hotfix:*|*fix\ *|*bug\ *)
      printf "Fixed"
      ;;
    remove:*|removed:*|delete:*|deleted:*|*remove\ *|*delete\ *)
      printf "Removed"
      ;;
    *)
      printf "Changed"
      ;;
  esac
}

while IFS=$'\x1f' read -r hash subject; do
  [[ -z "${hash:-}" ]] && continue
  commit_count=$((commit_count + 1))
  subject_lower="$(printf "%s" "$subject" | tr '[:upper:]' '[:lower:]')"
  category="$(categorize_subject "$subject_lower")"
  entry="- ${subject} ($(commit_url "$hash"))"

  case "$category" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
done < <(git log --reverse --pretty=format:'%H%x1f%s' "$range")

write_section() {
  local title="$1"
  shift
  local items=("$@")

  printf "\n### %s\n\n" "$title"
  if [[ "${#items[@]}" -eq 0 ]]; then
    printf "%s\n" "- No changes."
    return
  fi

  local item
  for item in "${items[@]}"; do
    printf "%s\n" "$item"
  done
}

{
  printf "# Changelog\n\n"
  printf "## [Unreleased] - %s\n\n" "$today"
  printf "Generated from %s. Commit count: %s.\n" "$range_label" "$commit_count"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$output_path"

echo "Wrote ${output_path} from ${commit_count} commits ${range_label}."
