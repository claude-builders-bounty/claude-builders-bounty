#!/usr/bin/env bash
set -euo pipefail

range="${1:-}"
outfile="${OUTPUT_FILE:-CHANGELOG.md}"

if [[ -z "$range" ]]; then
  if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    base_tag="$(git describe --tags --abbrev=0)"
    range="${base_tag}..HEAD"
  else
    root="$(git rev-list --max-parents=0 HEAD | tail -n 1)"
    range="${root}..HEAD"
  fi
fi

printf '# Changelog\n\nGenerated from `git log %s`\n\n' "$range" >"$outfile"

emit_section() {
  local heading="$1"
  local key="$2"
  local items="$3"
  if [[ -n "$items" ]]; then
    printf '## %s\n\n%s\n' "$heading" "$items" >>"$outfile"
  fi
}

added=""
fixed=""
changed=""
removed=""

while IFS=$'\t' read -r sha subject; do
  [[ -z "$sha" ]] && continue
  short="${sha:0:7}"
  line="- ${subject} (${short})"
  s="${subject,,}"
  prefix="${s%%[!a-z]*}"
  case "$prefix" in
    feat|feature|add|added|implement|implemented|introduce|introduced)
      added+="$line"$'\n'
      ;;
    fix|bug|bugfix|hotfix|patch|resolve|resolved)
      fixed+="$line"$'\n'
      ;;
    remove|removed|delete|deleted|deprecate|deprecated)
      removed+="$line"$'\n'
      ;;
    *)
      changed+="$line"$'\n'
      ;;
  esac
done < <(git log --no-merges --format='%H%x09%s' "$range")

emit_section "Added" added "$added"
emit_section "Fixed" fixed "$fixed"
emit_section "Changed" changed "$changed"
emit_section "Removed" removed "$removed"

echo "Wrote $outfile"
