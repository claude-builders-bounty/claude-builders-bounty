#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash changelog.sh [repo-dir] [output-file]

Generates a structured CHANGELOG.md from git commits since the latest tag.
If the repository has no tags, all commits are included.
EOF
}

repo_dir="${1:-.}"
output_file="${2:-CHANGELOG.md}"

if [[ "${repo_dir}" == "-h" || "${repo_dir}" == "--help" ]]; then
  usage
  exit 0
fi

if ! git -C "${repo_dir}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: ${repo_dir} is not a git repository" >&2
  exit 1
fi

latest_tag="$(git -C "${repo_dir}" describe --tags --abbrev=0 2>/dev/null || true)"
range_label="all history"
range_args=()

if [[ -n "${latest_tag}" ]]; then
  range_label="${latest_tag}..HEAD"
  range_args=("${latest_tag}..HEAD")
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

added_file="${tmp_dir}/added"
fixed_file="${tmp_dir}/fixed"
changed_file="${tmp_dir}/changed"
removed_file="${tmp_dir}/removed"
: >"${added_file}"
: >"${fixed_file}"
: >"${changed_file}"
: >"${removed_file}"

categorize_subject() {
  local subject_lower
  subject_lower="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  case "${subject_lower}" in
    feat:*|feat\(*|add:*|add\ *|added\ *|create:*|create\ *|introduce:*)
      printf '%s\n' "Added"
      ;;
    fix:*|fix\(*|fixed\ *|bugfix:*|repair:*|resolve:*|resolved\ *|correct:*)
      printf '%s\n' "Fixed"
      ;;
    remove:*|removed\ *|delete:*|deleted\ *|drop:*|dropped\ *|deprecate:*)
      printf '%s\n' "Removed"
      ;;
    *)
      printf '%s\n' "Changed"
      ;;
  esac
}

append_entry() {
  local category="$1"
  local entry="$2"

  case "${category}" in
    Added) printf '%s\n' "${entry}" >>"${added_file}" ;;
    Fixed) printf '%s\n' "${entry}" >>"${fixed_file}" ;;
    Removed) printf '%s\n' "${entry}" >>"${removed_file}" ;;
    *) printf '%s\n' "${entry}" >>"${changed_file}" ;;
  esac
}

commit_count=0
if [[ "${#range_args[@]}" -gt 0 ]]; then
  git_log_command=(git -C "${repo_dir}" log --reverse --no-merges --format='%h|%s' "${range_args[@]}")
else
  git_log_command=(git -C "${repo_dir}" log --reverse --no-merges --format='%h|%s')
fi

while IFS='|' read -r hash subject; do
  [[ -z "${hash}" ]] && continue
  commit_count=$((commit_count + 1))
  category="$(categorize_subject "${subject}")"
  append_entry "${category}" "- ${subject} (${hash})"
done < <("${git_log_command[@]}")

{
  printf '# Changelog\n\n'
  printf 'Generated from git history on %s.\n\n' "$(date -u '+%Y-%m-%d')"
  printf '## Unreleased\n\n'
  printf '_Range: %s_\n\n' "${range_label}"

  if [[ "${commit_count}" -eq 0 ]]; then
    printf 'No commits found for this range.\n'
    exit 0
  fi

  for section in Added Fixed Changed Removed; do
    case "${section}" in
      Added) section_file="${added_file}" ;;
      Fixed) section_file="${fixed_file}" ;;
      Changed) section_file="${changed_file}" ;;
      Removed) section_file="${removed_file}" ;;
    esac

    if [[ -s "${section_file}" ]]; then
      printf '### %s\n\n' "${section}"
      cat "${section_file}"
      printf '\n'
    fi
  done
} >"${output_file}"

printf 'Wrote %s\n' "${output_file}"
