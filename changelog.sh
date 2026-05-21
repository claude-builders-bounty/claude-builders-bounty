#!/usr/bin/env bash
set -euo pipefail

out="${1:-CHANGELOG.md}"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: run inside a git repository" >&2
  exit 1
fi

last_tag=""
if last_tag=$(git describe --tags --abbrev=0 2>/dev/null); then
  range="${last_tag}..HEAD"
  since="since ${last_tag}"
else
  range="HEAD"
  since="from repository start"
fi

added=()
fixed=()
changed=()
removed=()
other=()
while IFS=$'\t' read -r hash subject; do
  [ -n "${hash:-}" ] || continue
  line="- ${subject} (${hash})"
  lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')
  case "$lower" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" adds "*) added+=("$line") ;;
    fix:*|bugfix:*|hotfix:*|*" fix "*|*" fixes "*|*" bug "*) fixed+=("$line") ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|*" remove "*|*" delete "*) removed+=("$line") ;;
    refactor:*|change:*|changed:*|update:*|docs:*|chore:*|ci:*|test:*) changed+=("$line") ;;
    *) other+=("$line") ;;
  esac
done < <(git log --no-merges --pretty=format:'%h%x09%s' "$range")

emit_section() {
  local title="$1"
  local array_name="$2"
  local -n items="$array_name"
  printf '### %s\n' "$title"
  if ((${#items[@]})); then printf '%s\n' "${items[@]}"; else printf -- '- None\n'; fi
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'Generated %s from git history %s.\n\n' "$(date -u +%Y-%m-%d)" "$since"
  emit_section Added added
  emit_section Fixed fixed
  emit_section Changed changed
  emit_section Removed removed
  if ((${#other[@]})); then emit_section Other other; fi
} > "$out"

echo "wrote $out"
