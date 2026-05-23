#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: run inside a git repository" >&2
  exit 1
fi

last_tag=""
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  last_tag="$(git describe --tags --abbrev=0)"
fi

if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
  heading="## [Unreleased]"
else
  range="HEAD"
  heading="## [Initial Release]"
fi

mapfile -t commits < <(git log --no-merges --pretty=format:'%s' "$range")

added=()
fixed=()
changed=()
removed=()

categorize() {
  local msg="$1"
  local low
  low="$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')"

  if [[ "$low" =~ ^(feat|add|added|new)(\(|:|\s) ]] || [[ "$low" == *" add "* ]] || [[ "$low" == *" added "* ]]; then
    added+=("$msg")
  elif [[ "$low" =~ ^(fix|bugfix|hotfix)(\(|:|\s) ]] || [[ "$low" == *" fix "* ]] || [[ "$low" == *" fixed "* ]] || [[ "$low" == *" bug "* ]]; then
    fixed+=("$msg")
  elif [[ "$low" =~ ^(remove|removed|delete|deleted|drop)(\(|:|\s) ]] || [[ "$low" == *" remove "* ]] || [[ "$low" == *" removed "* ]]; then
    removed+=("$msg")
  else
    changed+=("$msg")
  fi
}

for c in "${commits[@]}"; do
  [[ -n "$c" ]] && categorize "$c"
done

emit_section() {
  local title="$1"
  shift
  local -a items=("$@")
  echo "### ${title}" >> "$OUT_FILE"
  if [[ ${#items[@]} -eq 0 ]]; then
    echo "- None" >> "$OUT_FILE"
  else
    for m in "${items[@]}"; do
      echo "- ${m}" >> "$OUT_FILE"
    done
  fi
  echo >> "$OUT_FILE"
}

{
  echo "# Changelog"
  echo
  echo "All notable changes to this project will be documented in this file."
  echo
  echo "$heading"
  echo
} > "$OUT_FILE"

emit_section "Added" "${added[@]}"
emit_section "Fixed" "${fixed[@]}"
emit_section "Changed" "${changed[@]}"
emit_section "Removed" "${removed[@]}"

echo "Generated ${OUT_FILE} from range: ${range}"