#!/usr/bin/env bash
# generate-changelog.sh — Structured CHANGELOG.md from git history
# Usage: bash scripts/generate-changelog.sh [--stdout] [--no-emoji] [--output FILE]
set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
NO_EMOJI=false
while [[ $# -gt 0 ]]; do case $1 in
  --stdout) OUTPUT_FILE="" ; shift ;;
  --no-emoji) NO_EMOJI=true ; shift ;;
  --output) OUTPUT_FILE="$2"; shift 2 ;;
  *) echo "Usage: $0 [--stdout] [--no-emoji] [--output FILE]" >&2; exit 1 ;;
esac; done

E() { if [ "$NO_EMOJI" = false ]; then echo "$1"; fi; }

get_latest_tag() { git tag --sort=-version:refname 2>/dev/null | head -1; }

categorize() {
  local msg="$1" type="" scope="" rest=""
  if [[ "$msg" =~ ^([a-zA-Z_-]+)(\([^)]*\))?!?:(.*) ]]; then
    type="${BASH_REMATCH[1]}"; scope="${BASH_REMATCH[2]}"; rest="${BASH_REMATCH[3]}"
  elif [[ "$msg" =~ ^([a-zA-Z_-]+):(.*) ]]; then
    type="${BASH_REMATCH[1]}"; rest="${BASH_REMATCH[2]}"
  else echo "Miscellaneous||$(E '🔮') $msg"; return; fi
  rest="${rest#"${rest%%[![:space:]]*}"}"
  prefix=""; [ -n "$scope" ] && prefix="**$(echo "$scope" | tr -d '()')**: "
  case "$type" in
    feat|feature) echo "Added||$(E '🚀') $prefix$rest" ;;
    fix|bugfix|hotfix) echo "Fixed||$(E '🐛') $prefix$rest" ;;
    refactor|style|chore) echo "Changed||$(E '🔧') $prefix$rest" ;;
    docs|documentation) echo "Documentation||$(E '📖') $prefix$rest" ;;
    perf|performance) echo "Performance||$(E '⚡') $prefix$rest" ;;
    test|testing) echo "Testing||$(E '🧪') $prefix$rest" ;;
    security) echo "Security||$(E '🔒') $prefix$rest" ;;
    deps|dependencies|build|ci) echo "Dependencies||$(E '📦') $prefix$rest" ;;
    revert|remove|deprecate|delete) echo "Removed||$(E '🔥') $prefix$rest" ;;
    *) echo "Miscellaneous||$(E '🔮') $prefix$rest" ;;
  esac
}

main() {
  local tag; tag=$(get_latest_tag)
  local range; [ -n "$tag" ] && range="$tag..HEAD" || range="HEAD"
  local now; now=$(date +%Y-%m-%d)

  local output="# Changelog"
  output="$output"$'\n\n'"## [Unreleased]"$'\n\n'
  [ -n "$tag" ] && output="$output"'## ['"$tag"'] - '"$now"$'\n\n'

  declare -A items
  local IFS=$'\n'
  for entry in $(git log "$range" --format="%s||%h" --no-merges 2>/dev/null); do
    local msg="${entry%||*}"; local hash="${entry#*||}"; hash="${hash:0:7}"
    local result; result=$(categorize "$msg")
    local cat="${result%||*}"; local desc="${result#*||}"
    items["$cat"]="${items["$cat"]}- ${desc} (\`$hash\`)"$'\n'
  done

  local count=0
  for pair in "Added||🚀" "Fixed||🐛" "Changed||🔧" "Removed||🔥" \
              "Documentation||📖" "Performance||⚡" "Testing||🧪" \
              "Security||🔒" "Dependencies||📦" "Miscellaneous||🔮"; do
    local cat="${pair%||*}"; local icon="${pair#*||}"
    local content="${items[$cat]}"
    if [ -n "$content" ]; then
      local eicon=""; [ "$NO_EMOJI" = false ] && eicon="$icon "
      output="$output"'### '"$eicon$cat"$'\n\n'"$content"$'\n'
      count=$((count + $(echo "$content" | grep -c '^-')))
    fi
  done

  [ "$count" -eq 0 ] && output="$output"$'\n_No changes_\n'

  if [ -z "$OUTPUT_FILE" ]; then echo "$output"
  else echo "$output" > "$OUTPUT_FILE"
    echo "[✓] CHANGELOG generated: $OUTPUT_FILE"
    echo "    $count change(s) since ${tag:-initial}"
  fi
}

main "$@"
