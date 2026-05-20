#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--output CHANGELOG.md] [--range <git-range>] [--no-links]

Generate a structured CHANGELOG.md from git commits since the latest tag.

Options:
  --output, -o    File to write. Defaults to CHANGELOG.md.
  --range, -r     Explicit git revision range, for example v1.2.0..HEAD.
  --no-links      Do not add GitHub commit links.
  --help, -h      Show this help text.
USAGE
}

output_file="CHANGELOG.md"
custom_range=""
include_links=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output|-o)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 2; }
      output_file="$2"
      shift 2
      ;;
    --range|-r)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 2; }
      custom_range="$2"
      shift 2
      ;;
    --no-links)
      include_links=0
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

if ! command -v git >/dev/null 2>&1; then
  echo "git is required but was not found in PATH" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Run this script from inside a git repository" >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "This repository has no commits yet" >&2
  exit 1
fi

range_label=""
git_log_args=()

if [[ -n "$custom_range" ]]; then
  git_log_args=("$custom_range")
  range_label="\`$custom_range\`"
else
  latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "$latest_tag" ]]; then
    git_log_args=("${latest_tag}..HEAD")
    range_label="since \`$latest_tag\`"
  else
    git_log_args=("HEAD")
    range_label="from the beginning of history"
  fi
fi

remote_base_url() {
  local remote
  remote="$(git config --get remote.origin.url 2>/dev/null || true)"
  [[ -n "$remote" ]] || return 1

  case "$remote" in
    git@github.com:*.git)
      remote="${remote#git@github.com:}"
      remote="${remote%.git}"
      printf 'https://github.com/%s\n' "$remote"
      ;;
    git@github.com:*)
      remote="${remote#git@github.com:}"
      printf 'https://github.com/%s\n' "$remote"
      ;;
    https://github.com/*.git)
      printf '%s\n' "${remote%.git}"
      ;;
    https://github.com/*)
      printf '%s\n' "$remote"
      ;;
    *)
      return 1
      ;;
  esac
}

categorize_subject() {
  local subject lower
  subject="$1"
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower" == feat:* || "$lower" == feat\(* || "$lower" == feature:* ||
        "$lower" == add:* || "$lower" == added:* || "$lower" == implement:* ||
        "$lower" == introduce:* || "$lower" == *" add "* ||
        "$lower" == *" adds "* || "$lower" == *" added "* ||
        "$lower" == *" implement "* || "$lower" == *" introduces "* ]]; then
    printf 'Added'
  elif [[ "$lower" == fix:* || "$lower" == fix\(* || "$lower" == fixed:* ||
          "$lower" == bugfix:* || "$lower" == hotfix:* ||
          "$lower" == repair:* || "$lower" == patch:* ||
          "$lower" == *" fix "* || "$lower" == *" fixes "* ||
          "$lower" == *" fixed "* || "$lower" == *" bug "* ||
          "$lower" == *" regression "* ]]; then
    printf 'Fixed'
  elif [[ "$lower" == remove:* || "$lower" == removed:* ||
          "$lower" == delete:* || "$lower" == deleted:* ||
          "$lower" == drop:* || "$lower" == dropped:* ||
          "$lower" == deprecate:* || "$lower" == deprecated:* ||
          "$lower" == *" remove "* || "$lower" == *" removes "* ||
          "$lower" == *" removed "* || "$lower" == *" delete "* ||
          "$lower" == *" deleted "* ]]; then
    printf 'Removed'
  else
    printf 'Changed'
  fi
}

commit_reference() {
  local sha short ref
  sha="$1"
  short="$(git rev-parse --short "$sha")"

  if [[ "$include_links" -eq 1 ]] && ref="$(remote_base_url 2>/dev/null)"; then
    printf '([%s](%s/commit/%s))' "$short" "$ref" "$sha"
  else
    printf '(%s)' "$short"
  fi
}

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

for section in Added Fixed Changed Removed; do
  : > "$tmpdir/$section"
done

git log --reverse --format='%H%x1f%s' "${git_log_args[@]}" > "$tmpdir/commits"

while IFS=$'\x1f' read -r sha subject; do
  [[ -n "$sha" ]] || continue
  category="$(categorize_subject "$subject")"
  printf -- '- %s %s\n' "$subject" "$(commit_reference "$sha")" >> "$tmpdir/$category"
done < "$tmpdir/commits"

today="$(date +%Y-%m-%d)"

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$today"
  printf '_Generated from git history %s._\n\n' "$range_label"

  for section in Added Fixed Changed Removed; do
    printf '### %s\n' "$section"
    if [[ -s "$tmpdir/$section" ]]; then
      cat "$tmpdir/$section"
    else
      printf -- '- No changes.\n'
    fi
    printf '\n'
  done
} > "$output_file"

printf 'Wrote %s using commits %s.\n' "$output_file" "$range_label"
