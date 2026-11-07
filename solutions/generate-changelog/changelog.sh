#!/usr/bin/env bash
set -euo pipefail

# Generate a changelog from commits after the most recent reachable Git tag.
# Usage: bash changelog.sh [path/to/repository]
repo="${1:-.}"
if ! repo_root="$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null)"; then
  echo "Error: '$repo' is not a git working tree" >&2
  exit 1
fi
repo="$repo_root"
if ! git -C "$repo" rev-parse --verify 'HEAD^{commit}' >/dev/null 2>&1; then
  echo "Error: '$repo' has no commits" >&2
  exit 1
fi
if tag="$(git -C "$repo" describe --tags --abbrev=0 2>/dev/null)"; then
  range="${tag}..HEAD"
  header="Changes since ${tag}"
else
  range="HEAD"
  header="Changes (no previous tag)"
fi

out="${repo}/CHANGELOG.md"
tmp=""
log=""
trap 'rm -f "$tmp" "$log"' EXIT
log="$(mktemp)"
# Process substitution hides git log's exit status from set -e. Read it once,
# check success, and only then generate a replacement for the existing file.
if ! git -C "$repo" log "$range" --no-merges --format='%h%x1f%s' > "$log"; then
  echo "Error: could not read git history; CHANGELOG.md was not changed" >&2
  exit 1
fi
tmp="$(mktemp "${repo}/.CHANGELOG.md.XXXXXX")"

classify() {
  local lower="${1,,}"
  local conventional='^(feat|fix|bugfix|remove|delete)(\([^()]+\))?!?:'
  if [[ "$lower" =~ $conventional ]]; then
    case "${BASH_REMATCH[1]}" in
      feat) printf Added ;;
      fix|bugfix) printf Fixed ;;
      remove|delete) printf Removed ;;
    esac
  else
    case "$lower" in
      add\ *|added\ *|new\ *|implement\ *) printf Added ;;
      fixed\ *|repair\ *) printf Fixed ;;
      removed\ *|drop\ *) printf Removed ;;
      *) printf Changed ;;
    esac
  fi
}

{
  printf '# Changelog\n\n## %s\n\n' "$header"
  for category in Added Fixed Changed Removed; do
    printf '### %s\n\n' "$category"
    count=0
    # Unit separator between commit hash and message avoids shell parsing ambiguity.
    while IFS=$'\x1f' read -r hash subject; do
      [[ -n "$hash" ]] || continue
      [[ "$(classify "$subject")" == "$category" ]] || continue
      # Ensure git-originated text cannot inject extra Markdown lines.
      subject="${subject//$'\r'/ }"
      printf -- '- %s (`%s`)\n' "$subject" "${hash:0:7}"
      ((count+=1))
    done < "$log"
    if (( count == 0 )); then printf '_No changes._\n'; fi
    printf '\n'
  done
} > "$tmp"
mv "$tmp" "$out"
printf 'Wrote %s\n' "$out"
