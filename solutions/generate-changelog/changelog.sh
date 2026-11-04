#!/usr/bin/env bash
set -euo pipefail

# Generate a changelog from commits after the most recent reachable Git tag.
# Usage: bash changelog.sh [path/to/repository]
repo="${1:-.}"
if ! git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: '$repo' is not a git repository" >&2
  exit 1
fi
repo="$(cd "$repo" && pwd)"
if git -C "$repo" describe --tags --abbrev=0 >/dev/null 2>&1; then
  tag="$(git -C "$repo" describe --tags --abbrev=0)"
  range="${tag}..HEAD"
  header="Changes since ${tag}"
else
  range="HEAD"
  header="Changes (no previous tag)"
fi

out="${repo}/CHANGELOG.md"
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
{
  printf '# Changelog\n\n## %s\n\n' "$header"
  for category in Added Fixed Changed Removed; do
    printf '### %s\n\n' "$category"
    count=0
    # Unit separator between commit hash and message avoids shell parsing ambiguity.
    while IFS=$'\x1f' read -r hash subject; do
      [[ -n "$hash" ]] || continue
      lower="${subject,,}"
      case "$category:$lower" in
        Added:feat:*|Added:add\ *|Added:added\ *|Added:new\ *|Added:implement\ *) ;;
        Fixed:fix:*|Fixed:fixed\ *|Fixed:bugfix:*|Fixed:repair\ *) ;;
        Removed:remove:*|Removed:removed\ *|Removed:delete:*|Removed:drop\ *) ;;
        Changed:*)
          case "$lower" in
            feat:*|add\ *|added\ *|new\ *|implement\ *|fix:*|fixed\ *|bugfix:*|repair\ *|remove:*|removed\ *|delete:*|drop\ *) continue ;;
          esac ;;
        *) continue ;;
      esac
      # Ensure git-originated text cannot inject extra Markdown lines.
      subject="${subject//$'\r'/ }"
      printf -- '- %s (`%s`)\n' "$subject" "${hash:0:7}"
      ((count+=1))
    done < <(git -C "$repo" log "$range" --no-merges --format='%h%x1f%s')
    if (( count == 0 )); then printf '_No changes._\n'; fi
    printf '\n'
  done
} > "$tmp"
mv "$tmp" "$out"
trap - EXIT
printf 'Wrote %s\n' "$out"
