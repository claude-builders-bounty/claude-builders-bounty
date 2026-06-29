#!/usr/bin/env bash
set -euo pipefail

output_file="CHANGELOG.md"
range_override=""
include_authors="false"

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--output CHANGELOG.md] [--range <git-range>] [--include-authors]

Generates a structured CHANGELOG.md from commits since the latest git tag.
If no tag exists, it uses the complete repository history.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output|-o)
      output_file="${2:-}"
      [[ -n "$output_file" ]] || { echo "Missing value for --output" >&2; exit 2; }
      shift 2
      ;;
    --range)
      range_override="${2:-}"
      [[ -n "$range_override" ]] || { echo "Missing value for --range" >&2; exit 2; }
      shift 2
      ;;
    --include-authors)
      include_authors="true"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This command must be run inside a git repository." >&2
  exit 1
fi

latest_tag=""
if [[ -z "$range_override" ]]; then
  latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "$latest_tag" ]]; then
    commit_range="${latest_tag}..HEAD"
    since_label="since ${latest_tag}"
  else
    commit_range="HEAD"
    since_label="from the full git history"
  fi
else
  commit_range="$range_override"
  since_label="for ${range_override}"
fi

if ! git rev-list --max-count=1 "$commit_range" >/dev/null 2>&1; then
  echo "No commits found for range: ${commit_range}" >&2
  exit 1
fi

version="Unreleased"
repo_name="$(basename "$(git rev-parse --show-toplevel)")"
generated_date="$(date -u +%Y-%m-%d)"

declare -a added fixed changed removed

append_entry() {
  local category="$1"
  local sha="$2"
  local subject="$3"
  local author="$4"
  local clean="$subject"

  clean="$(printf '%s' "$clean" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
  clean="$(printf '%s' "$clean" | sed -E 's/^(feat|feature|fix|bugfix|change|changed|refactor|perf|docs|doc|remove|removed|delete|deleted|deprecate|deprecated|chore|style|test|build|ci)(\([^)]*\))?!?:[[:space:]]*//I')"
  clean="$(printf '%s' "$clean" | sed -E 's/^[-*][[:space:]]*//')"
  if [[ -z "$clean" ]]; then
    clean="$subject"
  fi

  local entry="- ${clean} (${sha})"
  if [[ "$include_authors" == "true" ]]; then
    entry="${entry} - ${author}"
  fi

  case "$category" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Changed) changed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
  esac
}

categorize_subject() {
  local subject_lc
  subject_lc="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  case "$subject_lc" in
    feat:*|feat\(*|feature:*|add:*|added:*|create:*|implement:*|introduce:*) echo "Added" ;;
    fix:*|fix\(*|bugfix:*|hotfix:*|repair:*|resolve:*|correct:*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|deprecate:*|deprecated:*) echo "Removed" ;;
    change:*|changed:*|refactor:*|refactor\(*|perf:*|perf\(*|docs:*|doc:*|style:*|test:*|build:*|ci:*|chore:*|update:*|improve:*|rename:*) echo "Changed" ;;
    *)
      if [[ "$subject_lc" =~ (^|[[:space:]])(fix|fixed|bug|bugfix|error|crash|regression)([[:space:]]|$) ]]; then
        echo "Fixed"
      elif [[ "$subject_lc" =~ (^|[[:space:]])(remove|removed|delete|deleted|drop|deprecated)([[:space:]]|$) ]]; then
        echo "Removed"
      elif [[ "$subject_lc" =~ (^|[[:space:]])(add|added|new|create|implement|introduce)([[:space:]]|$) ]]; then
        echo "Added"
      else
        echo "Changed"
      fi
      ;;
  esac
}

while IFS=$'\t' read -r sha subject author; do
  [[ -n "${sha:-}" ]] || continue
  category="$(categorize_subject "$subject")"
  append_entry "$category" "$sha" "$subject" "$author"
done < <(git log --no-merges --reverse --pretty=format:'%h%x09%s%x09%an' "$commit_range")

write_section() {
  local title="$1"
  shift
  local items=("$@")
  if [[ ${#items[@]} -eq 0 ]]; then
    return
  fi
  printf '### %s\n\n' "$title" >> "$output_file"
  printf '%s\n' "${items[@]}" >> "$output_file"
  printf '\n' >> "$output_file"
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes to `%s` are documented in this file.\n\n' "$repo_name"
  printf 'Generated on %s from commits %s.\n\n' "$generated_date" "$since_label"
  printf '## [%s] - %s\n\n' "$version" "$generated_date"
} > "$output_file"

write_section "Added" "${added[@]}"
write_section "Fixed" "${fixed[@]}"
write_section "Changed" "${changed[@]}"
write_section "Removed" "${removed[@]}"

if [[ ${#added[@]} -eq 0 && ${#fixed[@]} -eq 0 && ${#changed[@]} -eq 0 && ${#removed[@]} -eq 0 ]]; then
  printf 'No commit changes found for this range.\n' >> "$output_file"
fi

printf 'Generated %s\n' "$output_file"
