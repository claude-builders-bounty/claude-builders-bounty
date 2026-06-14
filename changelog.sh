#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"
repo_name="$(basename "$(git rev-parse --show-toplevel)")"
latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
today="$(date +%Y-%m-%d)"

if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  range_label="Changes since ${latest_tag}"
else
  range=""
  range_label="All commits"
fi

added=()
fixed=()
changed=()
removed=()
breaking=()
breaking_subject_re='^[[:alpha:]]+(\([^)]+\))?!:'

normalize_subject() {
  local subject="$1"
  subject="$(printf '%s' "$subject" | sed -E 's/^(feat|fix|docs|chore|refactor|test|style|perf|build|ci)(\([^)]+\))?!?:[[:space:]]*//')"
  printf '%s' "$subject"
}

add_entry() {
  local category="$1"
  local line="$2"

  case "$category" in
    breaking) breaking+=("$line") ;;
    added) added+=("$line") ;;
    fixed) fixed+=("$line") ;;
    removed) removed+=("$line") ;;
    *) changed+=("$line") ;;
  esac
}

contains_word() {
  local haystack=" $1 "
  local needle="$2"
  [[ "$haystack" == *" $needle "* ]]
}

while IFS= read -r -d $'\x1e' record; do
  IFS=$'\x1f' read -r hash subject body <<< "$record"
  [[ -z "${subject:-}" ]] && continue

  lower_subject="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  prefix="${lower_subject%%:*}"
  prefix="${prefix%%(*}"
  clean_subject="$(normalize_subject "$subject")"
  entry="- ${clean_subject} (${hash})"

  if [[ "$subject" =~ $breaking_subject_re ]] \
    || printf '%s\n' "${body:-}" | grep -Eiq '^BREAKING[ -]CHANGE:'; then
    add_entry breaking "$entry"
  else
    case "$prefix" in
      feat|add|added|create|implement) add_entry added "$entry" ;;
      fix|fixed|bug|bugfix|resolve|patch) add_entry fixed "$entry" ;;
      remove|removed|delete|deleted|drop|dropped|deprecate) add_entry removed "$entry" ;;
      *)
      if contains_word "$lower_subject" add \
        || contains_word "$lower_subject" added \
        || contains_word "$lower_subject" create \
        || contains_word "$lower_subject" implement; then
        add_entry added "$entry"
      elif contains_word "$lower_subject" fix \
        || contains_word "$lower_subject" fixed \
        || contains_word "$lower_subject" bug \
        || contains_word "$lower_subject" resolve; then
        add_entry fixed "$entry"
      elif contains_word "$lower_subject" remove \
        || contains_word "$lower_subject" removed \
        || contains_word "$lower_subject" delete \
        || contains_word "$lower_subject" drop; then
        add_entry removed "$entry"
      else
        add_entry changed "$entry"
      fi
      ;;
    esac
  fi
done < <(git log --no-merges --date-order --format='%h%x1f%s%x1f%b%x1e' ${range})

has_entries=false
if (( ${#breaking[@]} > 0 || ${#added[@]} > 0 || ${#fixed[@]} > 0 || ${#changed[@]} > 0 || ${#removed[@]} > 0 )); then
  has_entries=true
fi

{
  printf '# Changelog\n\n'
  printf '## %s - %s\n\n' "$today" "$range_label"
  printf 'Repository: `%s`\n\n' "$repo_name"

  if [[ "$has_entries" == false ]]; then
    printf 'No commits found for this range.\n'
  else
    if (( ${#breaking[@]} > 0 )); then
      printf '### Breaking Changes\n'
      printf '%s\n' "${breaking[@]}"
      printf '\n'
    fi

    if (( ${#added[@]} > 0 )); then
      printf '### Added\n'
      printf '%s\n' "${added[@]}"
      printf '\n'
    fi

    if (( ${#fixed[@]} > 0 )); then
      printf '### Fixed\n'
      printf '%s\n' "${fixed[@]}"
      printf '\n'
    fi

    if (( ${#changed[@]} > 0 )); then
      printf '### Changed\n'
      printf '%s\n' "${changed[@]}"
      printf '\n'
    fi

    if (( ${#removed[@]} > 0 )); then
      printf '### Removed\n'
      printf '%s\n' "${removed[@]}"
      printf '\n'
    fi
  fi
} > "$output_file"

printf 'Generated %s from %s.\n' "$output_file" "$range_label"
