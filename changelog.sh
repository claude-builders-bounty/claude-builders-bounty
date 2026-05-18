#!/usr/bin/env bash
set -euo pipefail

out="CHANGELOG.md"
since=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 2; }
      out="$2"
      shift 2
      ;;
    --since)
      [[ $# -ge 2 ]] || { echo "Missing value for --since" >&2; exit 2; }
      since="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [OUTPUT] [--output FILE] [--since REF]"
      exit 0
      ;;
    *)
      out="$1"
      shift
      ;;
  esac
done

if [[ -n "$since" ]]; then
  range="$since..HEAD"
  summary="Changes since \`$since\`."
else
  last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "$last_tag" ]]; then
    range="$last_tag..HEAD"
    summary="Changes since \`$last_tag\`."
  else
    range="HEAD"
    summary="Changes in this repository."
  fi
fi

commits="$(git log --pretty=format:'%s' "$range")"
write_section() {
  local section="$1"
  local matched=0
  echo "## $section"
  echo
  while IFS= read -r msg; do
    [[ -z "$msg" ]] && continue
    local lower="${msg,,}"
    case "$section:$lower" in
      Added:*add*|Added:*feat*|Added:*create*) echo "- $msg"; matched=1 ;;
      Changed:*change*|Changed:*update*|Changed:*refactor*|Changed:*improve*) echo "- $msg"; matched=1 ;;
      Fixed:*fix*|Fixed:*bug*|Fixed:*patch*|Fixed:*repair*) echo "- $msg"; matched=1 ;;
      Removed:*remove*|Removed:*delete*|Removed:*drop*) echo "- $msg"; matched=1 ;;
    esac
  done <<< "$commits"
  [[ "$matched" -eq 0 ]] && echo "- No entries."
  echo
}

{
  echo "# Changelog"
  echo
  echo "$summary"
  echo
  write_section Added
  write_section Changed
  write_section Fixed
  write_section Removed
} > "$out"

echo "Wrote $out"
