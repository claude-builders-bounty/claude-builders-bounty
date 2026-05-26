#!/usr/bin/env bash
set -euo pipefail

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
range="HEAD"
if [[ -n "${last_tag}" ]]; then
  range="${last_tag}..HEAD"
fi

out_file="${1:-CHANGELOG.md}"
tmp_file="$(mktemp)"
added=()
fixed=()
changed=()
removed=()

mapfile -t commits < <(git log --no-merges --format='%s' "${range}")

for subject in "${commits[@]}"; do
  lower="$(printf '%s' "${subject}" | tr '[:upper:]' '[:lower:]')"
  item="- ${subject}"
  if [[ "${lower}" =~ ^(feat|add)(\\(.+\\))?: ]] || [[ "${lower}" == *" add "* ]] || [[ "${lower}" == add\ * ]]; then
    added+=("${item}")
  elif [[ "${lower}" =~ ^(fix|bugfix)(\\(.+\\))?: ]] || [[ "${lower}" == *" fix "* ]] || [[ "${lower}" == fix\ * ]]; then
    fixed+=("${item}")
  elif [[ "${lower}" =~ ^(remove|drop|delete|deprecate)(\\(.+\\))?: ]] || [[ "${lower}" == *" remov"* ]] || [[ "${lower}" == *" delet"* ]]; then
    removed+=("${item}")
  else
    changed+=("${item}")
  fi
done

{
  echo "# Changelog"
  echo
  if [[ -n "${last_tag}" ]]; then
    echo "Changes since \`${last_tag}\`."
  else
    echo "Changes from the start of repository history."
  fi
  echo
  print_section() {
    local title="$1"
    shift
    echo "## ${title}"
    if [[ "$#" -eq 0 ]]; then
      echo "- None"
    else
      printf '%s\n' "$@"
    fi
    echo
  }
  print_section "Added" "${added[@]}"
  print_section "Fixed" "${fixed[@]}"
  print_section "Changed" "${changed[@]}"
  print_section "Removed" "${removed[@]}"
} > "${tmp_file}"

mv "${tmp_file}" "${out_file}"
printf 'Wrote %s\n' "${out_file}"
