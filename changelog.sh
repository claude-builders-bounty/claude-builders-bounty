#!/usr/bin/env bash
set -euo pipefail
OUT="CHANGELOG.md"
usage() { echo "Usage: bash changelog.sh [output-file]" >&2; }
if [[ $# -gt 1 ]]; then usage; exit 2; fi
[[ $# -eq 1 ]] && OUT="$1"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Error: not a git repository" >&2; exit 1; }
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then echo "Error: repository has no commits" >&2; exit 1; fi
if FROM=$(git describe --tags --abbrev=0 2>/dev/null); then
  RANGE="${FROM}..HEAD"; TITLE="Changes since ${FROM}"
else
  RANGE="HEAD"; TITLE="Changes"
fi
added=(); fixed=(); changed=(); removed=()
while IFS=$'\t' read -r sha subject; do
  [[ -z "${sha:-}" ]] && continue
  subject=${subject%$'\r'}
  lower=${subject,,}
  case "$lower" in
    add:*|added:*|add\ *|feat:*|feature:*|new:*|create:*|created:*|introduc*) bucket=added ;;
    fix:*|fixed:*|fix\ *|bugfix:*|bug:*|patch:*|hotfix:*) bucket=fixed ;;
    remove:*|removed:*|remove\ *|delete:*|deleted:*|deprecat*:*) bucket=removed ;;
    change:*|changed:*|change\ *|update:*|updated:*|update\ *|refactor:*|improv*:|docs:*|chore:*|perf:*|style:*|build:*|ci:*|test:*|release:*) bucket=changed ;;
    *) bucket=changed ;;
  esac
  line="- ${subject} (${sha:0:7})"
  case "$bucket" in
    added) added+=("$line") ;;
    fixed) fixed+=("$line") ;;
    changed) changed+=("$line") ;;
    removed) removed+=("$line") ;;
  esac
done < <(git log --no-merges --format='%H%x09%s' "$RANGE")
{
  echo "# Changelog"; echo; echo "## ${TITLE}"; echo
  for pair in "Added|added" "Fixed|fixed" "Changed|changed" "Removed|removed"; do
    IFS='|' read -r heading name <<< "$pair"; echo "### ${heading}"
    case "$name" in
      added) items=("${added[@]-}") ;; fixed) items=("${fixed[@]-}") ;;
      changed) items=("${changed[@]-}") ;; removed) items=("${removed[@]-}") ;;
    esac
    if ((${#items[@]})); then printf '%s\n' "${items[@]}"; else echo "- None"; fi
    echo
  done
} > "$OUT"
echo "Generated $OUT from ${RANGE}."
