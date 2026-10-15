#!/usr/bin/env bash
set -euo pipefail

output="CHANGELOG.md"
tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
range="${tag:+${tag}..HEAD}"

added="" fixed="" changed="" removed=""
while IFS='|' read -r hash subject; do
  [[ -z "$hash" ]] && continue
  entry="- ${subject} (\`${hash}\`)"
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  case "$normalized" in
    feat:*|feat\(*|add:*|add\ *) added+="$entry"$'\n' ;;
    fix:*|fix\(*|fixed:*|bugfix:*|bugfix\(* ) fixed+="$entry"$'\n' ;;
    remove:*|remove\ *|removed:*|delete:*|delete\ *) removed+="$entry"$'\n' ;;
    *) changed+="$entry"$'\n' ;;
  esac
done < <(git log ${range:+"$range"} --pretty=format:'%h|%s')

{
  printf '# Changelog\n\n## Unreleased\n'
  for category in Added Fixed Changed Removed; do
    case "$category" in
      Added) entries="$added" ;; Fixed) entries="$fixed" ;;
      Changed) entries="$changed" ;; Removed) entries="$removed" ;;
    esac
    printf '\n### %s\n' "$category"
    if [[ -n "$entries" ]]; then printf '%s' "$entries"; else printf -- '- None\n'; fi
  done
} > "$output"

printf 'Wrote %s using commits %s.\n' "$output" "${range:-from repository start}"
