#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--output CHANGELOG.md] [--since TAG_OR_REF]

Generate a structured CHANGELOG.md from git history.

Options:
  --output PATH     Output file path. Defaults to CHANGELOG.md.
  --since REF       Start after this git tag/ref. Defaults to the latest tag.
  -h, --help        Show this help.
USAGE
}

output_file="CHANGELOG.md"
since_ref=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      [[ $# -ge 2 ]] || { echo "Missing value for --output" >&2; exit 2; }
      output_file="$2"
      shift 2
      ;;
    --since)
      [[ $# -ge 2 ]] || { echo "Missing value for --since" >&2; exit 2; }
      since_ref="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository." >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if [[ -z "$since_ref" ]]; then
  since_ref="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$since_ref" ]]; then
  if ! git rev-parse --verify --quiet "$since_ref^{commit}" >/dev/null; then
    echo "Could not resolve --since ref: $since_ref" >&2
    exit 1
  fi
  log_range="${since_ref}..HEAD"
  range_note="Changes since \`$since_ref\`."
else
  log_range="HEAD"
  range_note="No git tags found; generated from the full commit history."
fi

today="$(date +%Y-%m-%d)"
remote_url="$(git config --get remote.origin.url || true)"

commit_url_prefix=""
if [[ "$remote_url" =~ github.com[:/]([^[:space:]]+/[^[:space:]/]+)(\.git)?$ ]]; then
  repo_slug="${BASH_REMATCH[1]}"
  repo_slug="${repo_slug%.git}"
  commit_url_prefix="https://github.com/${repo_slug}/commit/"
fi

added=()
fixed=()
changed=()
removed=()

clean_subject() {
  local subject="$1"
  local conventional_re
  subject="$(printf '%s' "$subject" | sed -E 's/^\[[^]]+\][[:space:]]+//; s/^[[:space:]]+|[[:space:]]+$//g')"
  conventional_re='^(feat|feature|add|create|implement|introduce|support|fix|bugfix|repair|resolve|correct|patch|remove|delete|drop|deprecate|chore|ci|build|docs|style|test|refactor|perf|change|update|improve)(\([^)]+\))?!?:[[:space:]]*(.+)$'

  shopt -s nocasematch
  if [[ "$subject" =~ $conventional_re ]]; then
    subject="${BASH_REMATCH[3]}"
  fi
  shopt -u nocasematch

  printf '%s' "$subject"
}

category_for_subject() {
  local lowered
  lowered="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lowered" =~ ^(feat|feature|add|create|implement|introduce|support)(\(.+\))?!?: ]]; then
    printf 'added'
  elif [[ "$lowered" =~ ^(fix|bugfix|repair|resolve|correct|patch)(\(.+\))?!?: ]]; then
    printf 'fixed'
  elif [[ "$lowered" =~ ^(remove|delete|drop|deprecate)(\(.+\))?!?: ]]; then
    printf 'removed'
  elif [[ "$lowered" =~ ^(chore|ci|build|docs|style|test|refactor|perf|change|update|improve)(\(.+\))?!?: ]]; then
    printf 'changed'
  elif [[ "$lowered" =~ (^|[[:space:]])(remove|removed|delete|deleted|drop|dropped)([[:space:]]|$) ]]; then
    printf 'removed'
  elif [[ "$lowered" =~ (^|[[:space:]])(fix|fixed|resolve|resolved|bug)([[:space:]]|$) ]]; then
    printf 'fixed'
  elif [[ "$lowered" =~ (^|[[:space:]])(add|added|create|created|implement|implemented|support)([[:space:]]|$) ]]; then
    printf 'added'
  else
    printf 'changed'
  fi
}

format_commit() {
  local hash="$1"
  local subject="$2"
  local short_hash
  short_hash="$(git rev-parse --short "$hash")"
  subject="$(clean_subject "$subject")"

  if [[ -n "$commit_url_prefix" ]]; then
    printf -- '- %s ([`%s`](%s%s))' "$subject" "$short_hash" "$commit_url_prefix" "$hash"
  else
    printf -- '- %s (`%s`)' "$subject" "$short_hash"
  fi
}

while IFS=$'\x1f' read -r hash subject || [[ -n "${hash:-}" ]]; do
  [[ -n "${hash:-}" && -n "${subject:-}" ]] || continue
  entry="$(format_commit "$hash" "$subject")"
  case "$(category_for_subject "$subject")" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    removed) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
done < <(git log "$log_range" --reverse --pretty=format:'%H%x1f%s')

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '### %s\n\n' "$title"
  if [[ ${#entries[@]} -eq 0 ]]; then
    printf '_No %s changes._\n\n' "$(printf '%s' "$title" | tr '[:upper:]' '[:lower:]')"
    return
  fi

  printf '%s\n' "${entries[@]}"
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes to this project are documented in this file.\n\n'
  printf '## [Unreleased] - %s\n\n' "$today"
  printf '_%s_\n\n' "$range_note"
  write_section "Added" ${added[@]+"${added[@]}"}
  write_section "Fixed" ${fixed[@]+"${fixed[@]}"}
  write_section "Changed" ${changed[@]+"${changed[@]}"}
  write_section "Removed" ${removed[@]+"${removed[@]}"}
} > "$output_file"

printf 'Wrote %s from %s\n' "$output_file" "$log_range"
