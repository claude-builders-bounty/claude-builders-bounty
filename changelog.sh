#!/usr/bin/env bash
set -euo pipefail

range=""
last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  range="$last_tag..HEAD"
fi

commits="$(git log ${range:+$range} --pretty=format:'%s' --no-merges)"
{
  echo '# Changelog'
  echo
  if [[ -n "$last_tag" ]]; then
    echo "Changes since \`$last_tag\`."
  else
    echo 'Changes from the full git history (no tags found).'
  fi
  echo
  for section in Added Fixed Changed Removed; do
    echo "## $section"
    echo
    case "$section" in
      Added) pattern='^(feat|add)(\(.+\))?:|^added? ' ;;
      Fixed) pattern='^(fix|bugfix)(\(.+\))?:|^fixed? ' ;;
      Removed) pattern='^(remove|delete)(\(.+\))?:|^removed? ' ;;
      Changed) pattern='.*' ;;
    esac

    found=0
    while IFS= read -r subject; do
      [[ -z "$subject" ]] && continue
      if [[ "$section" != Changed && ! "$subject" =~ $pattern ]]; then
        continue
      fi
      if [[ "$section" == Changed && "$subject" =~ ^(feat|add|fix|bugfix|remove|delete)(\(.+\))?: ]]; then
        continue
      fi
      text="$(sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//' <<< "$subject")"
      echo "- $text"
      found=1
    done <<< "$commits"
    [[ "$found" -eq 0 ]] && echo '- No changes.'
    echo
  done
} > CHANGELOG.md

echo 'Generated CHANGELOG.md'
