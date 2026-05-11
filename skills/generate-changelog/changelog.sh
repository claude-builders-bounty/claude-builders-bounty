#!/usr/bin/env bash
set -euo pipefail

output_file="CHANGELOG.md"
range_override=""

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--output CHANGELOG.md] [--range GIT_RANGE]

Generates a structured CHANGELOG.md from commits since the latest git tag.

Options:
  -o, --output FILE   Write changelog to FILE. Defaults to CHANGELOG.md.
      --range RANGE   Use an explicit git revision range instead of latest-tag..HEAD.
  -h, --help          Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      output_file="${2:-}"
      if [[ -z "$output_file" ]]; then
        echo "Missing value for $1" >&2
        exit 1
      fi
      shift 2
      ;;
    --range)
      range_override="${2:-}"
      if [[ -z "$range_override" ]]; then
        echo "Missing value for --range" >&2
        exit 1
      fi
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Run this script inside a git repository." >&2
  exit 1
fi

last_tag=""
range_label=""
if [[ -n "$range_override" ]]; then
  git_range="$range_override"
  range_label="$range_override"
else
  last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "$last_tag" ]]; then
    git_range="${last_tag}..HEAD"
    range_label="${last_tag}..HEAD"
  else
    git_range="HEAD"
    range_label="full history"
  fi
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added_file="$tmp_dir/added"
fixed_file="$tmp_dir/fixed"
changed_file="$tmp_dir/changed"
removed_file="$tmp_dir/removed"
touch "$added_file" "$fixed_file" "$changed_file" "$removed_file"

category_for() {
  local subject="$1"
  local lower
  local prefix=""
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower" == *:* ]]; then
    prefix="${lower%%:*}"
    prefix="${prefix%%(*}"
    prefix="${prefix%!}"
  fi

  case "$prefix" in
    feat|feature|add)
      printf 'Added\n'
      return
      ;;
    fix|fixed|bugfix|hotfix|patch)
      printf 'Fixed\n'
      return
      ;;
    remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)
      printf 'Removed\n'
      return
      ;;
  esac

  if [[ "$lower" == "add "* ]] || [[ "$lower" == "adds "* ]] || [[ "$lower" == "added "* ]]; then
    printf 'Added\n'
  elif [[ "$lower" == "fix "* ]] || [[ "$lower" == "fixes "* ]] || [[ "$lower" == "fixed "* ]]; then
    printf 'Fixed\n'
  elif [[ "$lower" == "remove "* ]] || [[ "$lower" == "removed "* ]] || [[ "$lower" == "delete "* ]] || [[ "$lower" == "deleted "* ]] || [[ "$lower" == "drop "* ]] || [[ "$lower" == "dropped "* ]] || [[ "$lower" == "deprecate "* ]] || [[ "$lower" == "deprecated "* ]]; then
    printf 'Removed\n'
  else
    printf 'Changed\n'
  fi
}

clean_subject() {
  local subject="$1"
  local prefix=""
  local prefix_type=""
  local rest=""

  if [[ "$subject" == *:* ]]; then
    prefix="${subject%%:*}"
    rest="${subject#*:}"
    prefix_type="${prefix%%(*}"
    prefix_type="${prefix_type%!}"

    if [[ -n "$prefix_type" ]] && [[ "$prefix_type" != *" "* ]]; then
      while [[ "$rest" == " "* ]]; do
        rest="${rest# }"
      done
      printf '%s\n' "$rest"
    else
      printf '%s\n' "$subject"
    fi
  else
    printf '%s\n' "$subject"
  fi
}

append_entry() {
  local category="$1"
  local entry="$2"

  case "$category" in
    Added) printf '%s\n' "$entry" >> "$added_file" ;;
    Fixed) printf '%s\n' "$entry" >> "$fixed_file" ;;
    Removed) printf '%s\n' "$entry" >> "$removed_file" ;;
    *) printf '%s\n' "$entry" >> "$changed_file" ;;
  esac
}

commit_count=0
while IFS=$'\037' read -r hash commit_date subject; do
  if [[ -z "${hash}${subject}" ]]; then
    continue
  fi

  short_hash="${hash:0:7}"
  category="$(category_for "$subject")"
  cleaned_subject="$(clean_subject "$subject")"
  append_entry "$category" "- ${cleaned_subject} (${short_hash}, ${commit_date})"
  commit_count=$((commit_count + 1))
done < <(git log --reverse --date=short --pretty=tformat:'%H%x1f%ad%x1f%s' "$git_range")

write_section() {
  local title="$1"
  local file="$2"

  printf '### %s\n' "$title"
  if [[ -s "$file" ]]; then
    cat "$file"
  else
    printf '%s\n' "- No entries."
  fi
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$(date +%F)"
  printf '_Generated from `%s`._\n\n' "$range_label"

  if [[ "$commit_count" -eq 0 ]]; then
    printf '_No commits found for this range._\n\n'
  fi

  write_section "Added" "$added_file"
  write_section "Fixed" "$fixed_file"
  write_section "Changed" "$changed_file"
  write_section "Removed" "$removed_file"
} > "$output_file"

printf 'Wrote %s from %s (%s commits).\n' "$output_file" "$range_label" "$commit_count"
