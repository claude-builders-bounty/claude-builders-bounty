#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [options]

Generate a structured CHANGELOG.md from commits after the latest reachable tag.

Options:
  --repo PATH       Git repository to inspect (default: current directory)
  --output PATH     Output file (default: CHANGELOG.md in the repository root)
  --since REF       Use REF instead of the latest reachable tag
  --no-date         Omit the generated-on date from the file header
  -h, --help        Show this help text
USAGE
}

repo_arg="."
output_arg=""
since_ref=""
include_date=1

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      [ "$#" -ge 2 ] || { echo "--repo requires a path" >&2; exit 2; }
      repo_arg="$2"
      shift 2
      ;;
    --output)
      [ "$#" -ge 2 ] || { echo "--output requires a path" >&2; exit 2; }
      output_arg="$2"
      shift 2
      ;;
    --since)
      [ "$#" -ge 2 ] || { echo "--since requires a git ref" >&2; exit 2; }
      since_ref="$2"
      shift 2
      ;;
    --no-date)
      include_date=0
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

if ! repo_root="$(git -C "$repo_arg" rev-parse --show-toplevel 2>/dev/null)"; then
  echo "Not a git repository: $repo_arg" >&2
  exit 1
fi

if ! git -C "$repo_root" rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "The repository has no commits: $repo_root" >&2
  exit 1
fi

if [ -n "$output_arg" ]; then
  output_path="$output_arg"
else
  output_path="$repo_root/CHANGELOG.md"
fi

base_label="repository root"
if [ -n "$since_ref" ]; then
  if ! git -C "$repo_root" rev-parse --verify "$since_ref^{commit}" >/dev/null 2>&1; then
    echo "Unknown git ref: $since_ref" >&2
    exit 1
  fi
  log_range="$since_ref..HEAD"
  base_label="$since_ref"
else
  latest_tag="$(git -C "$repo_root" describe --tags --abbrev=0 2>/dev/null || true)"
  if [ -n "$latest_tag" ]; then
    log_range="$latest_tag..HEAD"
    base_label="$latest_tag"
  else
    # With no tag, include the root commit as well as all later commits.
    log_range="HEAD"
  fi
fi

temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/changelog.XXXXXX")"
temp_output=""
cleanup() {
  rm -rf "$temp_dir"
  if [ -n "$temp_output" ]; then
    rm -f "$temp_output"
  fi
}
trap cleanup EXIT

for category in Added Fixed Changed Removed; do
  : > "$temp_dir/$category"
done

commit_lines="$(git -C "$repo_root" log --pretty=format:'%h%x09%s' "$log_range" 2>/dev/null || true)"
if [ -n "$commit_lines" ]; then
  while IFS="$(printf '\t')" read -r commit_hash subject; do
    [ -n "$commit_hash" ] || continue
    lower_subject="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

    case "$lower_subject" in
      feat:*|feature:*|add:*|added:*|new:*|introduce*|implement*)
        category="Added"
        ;;
      fix:*|fixed:*|bug:*|bugfix:*|repair:*|hotfix:*|resolve*)
        category="Fixed"
        ;;
      remove:*|removed:*|delete:*|deleted:*|drop:*|deprecate*)
        category="Removed"
        ;;
      *)
        category="Changed"
        ;;
    esac

    printf '%s\n' "- $subject ($commit_hash)" >> "$temp_dir/$category"
  done <<EOF
$commit_lines
EOF
fi

output_dir="$(dirname "$output_path")"
mkdir -p "$output_dir"
temp_output="$output_path.tmp.$$"

{
  printf '# Changelog\n\n'
  if [ "$include_date" -eq 1 ]; then
    printf 'Generated on %s from git history since `%s`.\n\n' "$(date -u +%Y-%m-%d)" "$base_label"
  else
    printf 'Generated from git history since `%s`.\n\n' "$base_label"
  fi
  printf '## Unreleased\n\n'

  has_changes=0
  for category in Added Fixed Changed Removed; do
    if [ -s "$temp_dir/$category" ]; then
      has_changes=1
      printf '### %s\n\n' "$category"
      cat "$temp_dir/$category"
      printf '\n'
    fi
  done

  if [ "$has_changes" -eq 0 ]; then
    printf '_No changes detected since the selected reference._\n'
  fi
} > "$temp_output"

mv "$temp_output" "$output_path"
printf 'Generated %s from %s\n' "$output_path" "$base_label"
