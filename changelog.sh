#!/usr/bin/env bash
set -euo pipefail

# Generate a structured CHANGELOG from commits since the latest tag.
# Usage: ./changelog.sh [output-file]
output=${1:-CHANGELOG.md}

latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [[ -n "$latest_tag" ]]; then
  range="$latest_tag..HEAD"
  version="Unreleased (since $latest_tag)"
else
  range="HEAD"
  version="Unreleased"
fi

# Keep the output deterministic and safe for subjects containing shell syntax.
declare -a added=() fixed=() changed=() removed=()
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  subject=${line%%|*}
  sha=${line##*|}
  lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')
  entry="- ${subject} (${sha})"
  case "$lower" in
    feat*|add*|new*|*" add "*|*" introduce "*) added+=("$entry") ;;
    fix*|bug*|hotfix*|patch*|*" fix "*|*"bug"*) fixed+=("$entry") ;;
    revert*|remove*|delete*|deprecate*|*" remove "*|*"delete"*) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
done < <(git log "$range" --no-merges --format='%s|%h')

{
  printf '# Changelog\n\n'
  printf '## %s\n\n' "$version"
  for section in added fixed changed removed; do
    case "$section" in
      added) title='Added'; values_ref=added ;;
      fixed) title='Fixed'; values_ref=fixed ;;
      changed) title='Changed'; values_ref=changed ;;
      removed) title='Removed'; values_ref=removed ;;
    esac
    eval 'count=${#'"$values_ref"'[@]}'
    ((count)) || continue
    printf '### %s\n\n' "$title"
    eval 'printf "%s\n" "${'"$values_ref"'[@]}"'
    printf '\n'
  done
} > "$output"

printf 'Generated %s from %s\n' "$output" "$range"
