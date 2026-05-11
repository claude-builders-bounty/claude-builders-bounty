#!/usr/bin/env bash
set -euo pipefail

repo="."
output="CHANGELOG.md"
version="Unreleased"
since=""
fetch_tags=1

usage() {
  cat <<'USAGE'
Generate a structured CHANGELOG.md from git history.

Usage:
  bash changelog.sh [options]

Options:
  --repo <path>       Repository path. Defaults to current directory.
  --output <file>     Output file. Defaults to CHANGELOG.md.
  --version <name>    Changelog release heading. Defaults to Unreleased.
  --since <tag>       Start from a specific git tag.
  --no-fetch          Do not fetch tags from origin before generating.
  -h, --help          Show this help message.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:?--repo requires a path}"
      shift 2
      ;;
    --output)
      output="${2:?--output requires a file path}"
      shift 2
      ;;
    --version)
      version="${2:?--version requires a heading value}"
      shift 2
      ;;
    --since)
      since="${2:?--since requires a tag}"
      shift 2
      ;;
    --no-fetch)
      fetch_tags=0
      shift
      ;;
    -h|--help)
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

git_in_repo() {
  git -C "$repo" "$@"
}

if ! git_in_repo rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $repo" >&2
  exit 1
fi

if [[ "$fetch_tags" -eq 1 ]] && git_in_repo remote get-url origin >/dev/null 2>&1; then
  git_in_repo fetch --tags --quiet origin || true
fi

if [[ -z "$since" ]]; then
  since="$(git_in_repo describe --tags --abbrev=0 2>/dev/null || true)"
fi

range=HEAD
if [[ -n "$since" ]]; then
  if ! git_in_repo rev-parse --verify --quiet "$since^{commit}" >/dev/null; then
    echo "Tag or revision not found: $since" >&2
    exit 1
  fi
  range="${since}..HEAD"
fi

remote_url="$(git_in_repo remote get-url origin 2>/dev/null || true)"
github_base=""
if [[ "$remote_url" =~ github.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
  github_base="https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
fi

date="$(date +%Y-%m-%d)"
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

append_commit() {
  local bucket="$1"
  local hash="$2"
  local subject="$3"
  local entry="- ${subject} (${hash})"

  if [[ -n "$github_base" ]]; then
    entry="- ${subject} ([${hash}](${github_base}/commit/${hash}))"
  fi

  case "$bucket" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    removed) removed+=("$entry") ;;
    changed) changed+=("$entry") ;;
  esac
}

categorize() {
  local subject_lc="$1"

  case "$subject_lc" in
    feat:*|feat\(*|add:*|added:*|implement:*|implemented:*|create:*|created:*)
      echo "added"
      ;;
    fix:*|fix\(*|fixed:*|bug:*|bugfix:*|repair:*|resolve:*|resolved:*)
      echo "fixed"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*)
      echo "removed"
      ;;
    *)
      if [[ "$subject_lc" =~ (^|[[:space:]])(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)([[:space:]]|$) ]]; then
        echo "removed"
      elif [[ "$subject_lc" =~ (^|[[:space:]])(fix|fixed|bugfix|repair|resolve|resolved)([[:space:]]|$) ]]; then
        echo "fixed"
      elif [[ "$subject_lc" =~ (^|[[:space:]])(add|added|implement|implemented|create|created|introduce|introduced)([[:space:]]|$) ]]; then
        echo "added"
      else
        echo "changed"
      fi
      ;;
  esac
}

while IFS=$'\t' read -r hash subject || [[ -n "${hash:-}" ]]; do
  [[ -z "${hash:-}" || -z "${subject:-}" ]] && continue
  lower_subject="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  bucket="$(categorize "$lower_subject")"
  append_commit "$bucket" "$hash" "$subject"
done < <(git_in_repo log --no-merges --pretty=format:'%h%x09%s' "$range")

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '### %s\n\n' "$title" >> "$tmp"
  if [[ "${#entries[@]}" -eq 0 ]]; then
    printf -- '- No changes.\n\n' >> "$tmp"
    return
  fi

  printf '%s\n' "${entries[@]}" >> "$tmp"
  printf '\n' >> "$tmp"
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes to this project are documented in this file.\n\n'
  printf '## [%s] - %s\n\n' "$version" "$date"
} > "$tmp"

if [[ -n "$since" ]]; then
  printf '_Changes since `%s`._\n\n' "$since" >> "$tmp"
else
  printf '_No git tags were found, so this includes the full repository history._\n\n' >> "$tmp"
fi

write_section "Added" "${added[@]+"${added[@]}"}"
write_section "Fixed" "${fixed[@]+"${fixed[@]}"}"
write_section "Changed" "${changed[@]+"${changed[@]}"}"
write_section "Removed" "${removed[@]+"${removed[@]}"}"

if [[ -n "$github_base" && -n "$since" ]]; then
  printf '[%s]: %s/compare/%s...HEAD\n' "$version" "$github_base" "$since" >> "$tmp"
fi

mv "$tmp" "$output"
trap - EXIT

echo "Wrote $output"
if [[ -n "$since" ]]; then
  echo "Included commits since $since"
else
  echo "Included full git history"
fi
