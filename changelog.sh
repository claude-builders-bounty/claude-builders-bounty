#!/usr/bin/env bash
set -euo pipefail

out=${1:-CHANGELOG.md}
repo=${2:-.}
cd "$repo"

range='HEAD'
if tag=$(git describe --tags --abbrev=0 2>/dev/null); then
  range="$tag..HEAD"
fi

declare -a added=() fixed=() changed=() removed=()
while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue
  lower=${subject,,}
  case "$lower" in
    add:*|added:*|feat:*|feature:*) added+=("$subject") ;;
    fix:*|fixed:*|bugfix:*|security:*) fixed+=("$subject") ;;
    remove:*|removed:*|delete:*|breaking:*) removed+=("$subject") ;;
    *) changed+=("$subject") ;;
  esac
done < <(git log "$range" --format='%s' --no-merges)

{
  printf '# Changelog\n\n'
  printf 'Generated from git history (%s).\n\n' "$(git rev-parse --short HEAD)"
  print_section() {
    local title=$1; shift
    (($#)) || return 0
    printf '## %s\n\n' "$title"
    for item in "$@"; do printf -- '- %s\n' "$item"; done
    printf '\n'
  }
  print_section Added "${added[@]}"
  print_section Fixed "${fixed[@]}"
  print_section Changed "${changed[@]}"
  print_section Removed "${removed[@]}"
} > "$out"
