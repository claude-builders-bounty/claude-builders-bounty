#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag=""
if latest_tag=$(git describe --tags --abbrev=0 2>/dev/null); then
  range="${latest_tag}..HEAD"
  since_label="since ${latest_tag}"
else
  range="HEAD"
  since_label="for entire repository history"
fi

repo_name=$(basename "$(git rev-parse --show-toplevel)")
generated_at=$(date -u +%Y-%m-%d)
version_label="Unreleased"

commit_lines=$(git log --no-merges --reverse --format='%H%x1f%s' ${range})

declare -a added fixed changed removed other
added=()
fixed=()
changed=()
removed=()
other=()

clean_subject() {
  local subject="$1"
  subject="${subject#feat: }"
  subject="${subject#feat!: }"
  subject="${subject#feature: }"
  subject="${subject#fix: }"
  subject="${subject#bugfix: }"
  subject="${subject#perf: }"
  subject="${subject#refactor: }"
  subject="${subject#change: }"
  subject="${subject#chore: }"
  subject="${subject#docs: }"
  subject="${subject#doc: }"
  subject="${subject#test: }"
  subject="${subject#style: }"
  subject="${subject#remove: }"
  subject="${subject#removed: }"
  subject="${subject#delete: }"
  subject="${subject#deleted: }"
  printf '%s' "$subject"
}

add_entry() {
  local hash="$1"
  local subject="$2"
  local short_hash
  short_hash=$(git rev-parse --short "$hash")
  printf -- '- %s (%s)' "$(clean_subject "$subject")" "$short_hash"
}

while IFS=$'\x1f' read -r hash subject; do
  [[ -z "${hash:-}" || -z "${subject:-}" ]] && continue
  subject_lc=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')
  entry=$(add_entry "$hash" "$subject")

  case "$subject_lc" in
    feat:*|feature:*|add:*|added:*|"feat("*|"feature("*) added+=("$entry") ;;
    fix:*|bugfix:*|hotfix:*|"fix("*|"bugfix("*) fixed+=("$entry") ;;
    remove:*|removed:*|delete:*|deleted:*|"remove("*|"delete("*) removed+=("$entry") ;;
    change:*|changed:*|refactor:*|perf:*|docs:*|doc:*|test:*|style:*|chore:*|"refactor("*|"perf("*|"docs("*|"test("*|"chore("*) changed+=("$entry") ;;
    *) other+=("$entry") ;;
  esac
done <<< "$commit_lines"

write_section() {
  local title="$1"
  local entries_text="${2:-}"
  printf '\n### %s\n' "$title"
  if [[ -z "$entries_text" ]]; then
    printf -- '- No changes.\n'
  else
    printf '%s\n' "$entries_text"
  fi
}

join_entries() {
  if (($# == 0)); then
    return 0
  fi
  printf '%s\n' "$@"
}

added_text=$(join_entries "${added[@]+${added[@]}}")
fixed_text=$(join_entries "${fixed[@]+${fixed[@]}}")
changed_text=$(join_entries "${changed[@]+${changed[@]}}" "${other[@]+${other[@]}}")
removed_text=$(join_entries "${removed[@]+${removed[@]}}")

{
  printf '# Changelog\n\n'
  printf 'All notable changes to `%s` are documented in this file.\n\n' "$repo_name"
  printf 'Generated on %s from git commits %s.\n\n' "$generated_at" "$since_label"
  printf '## [%s] - %s\n' "$version_label" "$generated_at"
  write_section "Added" "$added_text"
  write_section "Fixed" "$fixed_text"
  write_section "Changed" "$changed_text"
  write_section "Removed" "$removed_text"
} > "$OUTPUT_FILE"

printf 'Wrote %s using commits %s\n' "$OUTPUT_FILE" "$since_label"
