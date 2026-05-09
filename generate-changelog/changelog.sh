#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  since_label="since ${latest_tag}"
else
  range=""
  since_label="for all history"
fi

remote_url="$(git config --get remote.origin.url || true)"
commit_base=""
if [[ "$remote_url" =~ ^git@github.com:(.+)\.git$ ]]; then
  commit_base="https://github.com/${BASH_REMATCH[1]}/commit"
elif [[ "$remote_url" =~ ^https://github.com/(.+)\.git$ ]]; then
  commit_base="https://github.com/${BASH_REMATCH[1]}/commit"
elif [[ "$remote_url" =~ ^https://github.com/(.+)$ ]]; then
  commit_base="https://github.com/${BASH_REMATCH[1]}/commit"
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

format_entry() {
  local hash="$1"
  local subject="$2"
  local short="${hash:0:7}"

  subject="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  subject="$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"

  if [[ -n "$commit_base" ]]; then
    printf -- "- %s ([%s](%s/%s))" "$subject" "$short" "$commit_base" "$hash"
  else
    printf -- "- %s (%s)" "$subject" "$short"
  fi
}

categorize() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  lower="$(printf '%s' "$lower" | sed -E 's/^([a-z]+)(\([^)]+\))?!:/\1:/')"

  case "$lower" in
    feat:*|feature:*|add:*|added:*|new:*) echo "added" ;;
    fix:*|bug:*|bugfix:*|repair:*|hotfix:*) echo "fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*) echo "removed" ;;
    change:*|changed:*|refactor:*|perf:*|docs:*|doc:*|style:*|test:*|build:*|ci:*|chore:*) echo "changed" ;;
    *) echo "changed" ;;
  esac
}

while IFS=$'\x1f' read -r hash subject; do
  [[ -z "${hash:-}" ]] && continue
  entry="$(format_entry "$hash" "$subject")"
  case "$(categorize "$subject")" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    removed) removed+=("$entry") ;;
    changed) changed+=("$entry") ;;
  esac
done < <(git log --reverse --format=$'%H%x1f%s' ${range:+"$range"})

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  if [[ "${#entries[@]}" -eq 0 ]]; then
    return
  fi

  {
    printf '\n### %s\n\n' "$title"
    printf '%s\n' "${entries[@]}"
  } >> "$output_file"
}

{
  printf '# Changelog\n\n'
  printf 'Generated from git history %s on %s.\n' "$since_label" "$(date +%Y-%m-%d)"
} > "$output_file"

if [[ "${#added[@]}" -eq 0 && "${#fixed[@]}" -eq 0 && "${#changed[@]}" -eq 0 && "${#removed[@]}" -eq 0 ]]; then
  printf '\nNo commits found for this range.\n' >> "$output_file"
else
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
fi

echo "Wrote ${output_file}"
