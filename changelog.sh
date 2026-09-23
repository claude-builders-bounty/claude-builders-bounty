#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: run this inside a Git repository." >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
  since_label="since ${last_tag}"
else
  range="HEAD"
  since_label="from repository start"
fi

mapfile -t commits < <(git log "$range" --pretty=format:'%s%x09%h' --no-merges)

added=()
fixed=()
changed=()
removed=()

categorize() {
  local subject="$1" sha="$2" lower
  lower="${subject,,}"
  local item="- ${subject} (${sha})"

  if [[ "$lower" =~ ^(feat|add)(\(.+\))?: ]] || [[ "$lower" == add* ]] || [[ "$lower" == feat* ]]; then
    added+=("$item")
  elif [[ "$lower" =~ ^(fix|bugfix|hotfix)(\(.+\))?: ]] || [[ "$lower" == fix* ]]; then
    fixed+=("$item")
  elif [[ "$lower" =~ ^(remove|delete)(\(.+\))?: ]] || [[ "$lower" == remove* ]] || [[ "$lower" == delete* ]]; then
    removed+=("$item")
  else
    changed+=("$item")
  fi
}

for entry in "${commits[@]:-}"; do
  [[ -z "$entry" ]] && continue
  IFS=$'\t' read -r subject sha <<< "$entry"
  categorize "$subject" "$sha"
done

emit_section() {
  local title="$1"; shift
  local -a items=("$@")
  printf '### %s\n\n' "$title"
  if ((${#items[@]} == 0)); then
    printf -- '- None\n\n'
  else
    printf '%s\n' "${items[@]}"
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf 'Generated from git history %s on %s.\n\n' "$since_label" "$(date -u +%Y-%m-%d)"
  printf '## Unreleased\n\n'
  emit_section "Added" "${added[@]}"
  emit_section "Fixed" "${fixed[@]}"
  emit_section "Changed" "${changed[@]}"
  emit_section "Removed" "${removed[@]}"
} > "$OUT_FILE"

echo "Wrote ${OUT_FILE} (${#commits[@]} commits processed)."
