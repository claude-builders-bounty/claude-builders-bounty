#!/usr/bin/env bash
# generate-changelog — build a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh [REPO_DIR] [OUTPUT_FILE]
#     REPO_DIR     path to a git repository (default: current directory)
#     OUTPUT_FILE  changelog path to write   (default: <REPO_DIR>/CHANGELOG.md)
#
# Behavior:
#   - Collects commits since the most recent git tag (or from the first commit
#     if the repository has no tags).
#   - Auto-categorizes each commit into Added / Fixed / Changed / Removed using
#     Conventional-Commit prefixes with a keyword fallback.
#   - Writes a Keep-a-Changelog style CHANGELOG.md and prints it to stdout.
set -euo pipefail

repo_dir="${1:-.}"
out_file="${2:-}"

if ! command -v git >/dev/null 2>&1; then
  echo "error: git is required" >&2
  exit 2
fi
if [ ! -d "$repo_dir/.git" ] && ! git -C "$repo_dir" rev-parse --git-dir >/dev/null 2>&1; then
  echo "error: '$repo_dir' is not a git repository" >&2
  exit 2
fi

git() { command git -C "$repo_dir" "$@"; }

[ -z "$out_file" ] && out_file="$repo_dir/CHANGELOG.md"

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$last_tag" ]; then
  range="${last_tag}..HEAD"
  since_label="$last_tag"
else
  range=""
  since_label="the beginning of the project"
fi

added=(); fixed=(); changed=(); removed=()

# Read "<subject>" per non-merge commit, newest first.
# `|| [ -n "$subject" ]` keeps the final line when git emits no trailing newline.
while IFS= read -r subject || [ -n "$subject" ]; do
  [ -z "$subject" ] && continue
  low="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  # strip a conventional-commit scope, e.g. "feat(core): x" -> keep prefix word
  head_word="${low%%[:(]*}"
  case "$head_word" in
    feat|feature|add) added+=("$subject") ;;
    fix|bugfix|hotfix) fixed+=("$subject") ;;
    remove|removed|delete|deprecate|drop|revert) removed+=("$subject") ;;
    *)
      # keyword fallback when no conventional prefix is used
      case "$low" in
        add\ *|added\ *|"new "*|introduce*) added+=("$subject") ;;
        fix*|resolve*|bug*) fixed+=("$subject") ;;
        remov*|delet*|revert*|deprecat*|drop\ *) removed+=("$subject") ;;
        *) changed+=("$subject") ;;
      esac
      ;;
  esac
done < <(git log --no-merges --pretty=format:'%s' ${range:+$range})

emit_section() {
  local title="$1"; shift
  local -a items=("$@")
  [ "${#items[@]}" -eq 0 ] && return 0
  printf '### %s\n' "$title"
  local it
  for it in "${items[@]}"; do
    printf -- '- %s\n' "$it"
  done
  printf '\n'
}

version="$(git describe --tags --always 2>/dev/null || echo HEAD)"
date_str="$(date -u +%Y-%m-%d)"
total=$(( ${#added[@]} + ${#fixed[@]} + ${#changed[@]} + ${#removed[@]} ))

{
  printf '# Changelog\n\n'
  printf 'All notable changes to this project. Generated from git history by '
  printf '`generate-changelog`.\n\n'
  printf '## [%s] - %s\n' "$version" "$date_str"
  printf '_%d change(s) since %s._\n\n' "$total" "$since_label"
  emit_section "Added"   "${added[@]+"${added[@]}"}"
  emit_section "Changed" "${changed[@]+"${changed[@]}"}"
  emit_section "Fixed"   "${fixed[@]+"${fixed[@]}"}"
  emit_section "Removed" "${removed[@]+"${removed[@]}"}"
  if [ "$total" -eq 0 ]; then
    printf '_No commits found in range._\n\n'
  fi
} | tee "$out_file"

echo "changelog written to: $out_file" >&2
