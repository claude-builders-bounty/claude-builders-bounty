#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [options]

Generate CHANGELOG.md from git commits since the last tag.

Options:
  --repo PATH       Git repository to inspect. Default: current directory.
  --output PATH     Output file. Default: CHANGELOG.md in the repo.
  --from REF        Start ref. Default: latest reachable git tag.
  --to REF          End ref. Default: HEAD.
  --version NAME    Changelog version heading. Default: Unreleased.
  --help            Show this help.

Environment alternatives:
  CHANGELOG_REPO, CHANGELOG_OUTPUT, CHANGELOG_FROM, CHANGELOG_TO, CHANGELOG_VERSION
USAGE
}

repo="${CHANGELOG_REPO:-.}"
output="${CHANGELOG_OUTPUT:-CHANGELOG.md}"
from_ref="${CHANGELOG_FROM:-}"
to_ref="${CHANGELOG_TO:-HEAD}"
version="${CHANGELOG_VERSION:-Unreleased}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:?missing value for --repo}"
      shift 2
      ;;
    --output)
      output="${2:?missing value for --output}"
      shift 2
      ;;
    --from)
      from_ref="${2:?missing value for --from}"
      shift 2
      ;;
    --to)
      to_ref="${2:?missing value for --to}"
      shift 2
      ;;
    --version)
      version="${2:?missing value for --version}"
      shift 2
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

cd "$repo"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repository: $repo" >&2
  exit 1
fi

if [[ -z "$from_ref" ]]; then
  from_ref="$(git describe --tags --abbrev=0 "$to_ref" 2>/dev/null || true)"
fi

if [[ -n "$from_ref" ]]; then
  commit_range="${from_ref}..${to_ref}"
  range_label="${from_ref}..${to_ref}"
else
  commit_range="$to_ref"
  range_label="repository start..${to_ref}"
fi

generated_at="$(date -u '+%Y-%m-%d')"
added_entries=""
fixed_entries=""
changed_entries=""
removed_entries=""

category_for_subject() {
  local subject_lc
  subject_lc="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  case "$subject_lc" in
    feat:*|feat\(*|feature:*|add:*|added:*)
      printf 'Added'
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*)
      printf 'Fixed'
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|deprecate:*|deprecated:*)
      printf 'Removed'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

clean_subject() {
  local subject="$1"
  subject="$(printf '%s' "$subject" | sed -E 's/^[A-Za-z]+(\([^)]+\))?!?:[[:space:]]*//')"
  subject="$(printf '%s' "$subject" | sed -E 's/[[:space:]]+/ /g; s/^ //; s/ $//')"
  if [[ -z "$subject" ]]; then
    subject="Unspecified change"
  fi
  printf '%s' "$subject"
}

append_entry() {
  local category="$1"
  local entry="$2"
  case "$category" in
    Added)
      added_entries+="${entry}"$'\n'
      ;;
    Fixed)
      fixed_entries+="${entry}"$'\n'
      ;;
    Removed)
      removed_entries+="${entry}"$'\n'
      ;;
    *)
      changed_entries+="${entry}"$'\n'
      ;;
  esac
}

while IFS=$'\t' read -r hash date subject || [[ -n "${hash:-}" ]]; do
  [[ -n "${hash:-}" ]] || continue
  category="$(category_for_subject "$subject")"
  clean="$(clean_subject "$subject")"
  append_entry "$category" "- ${clean} (${hash}, ${date})"
done < <(git log "$commit_range" --no-merges --pretty=format:'%h%x09%ad%x09%s' --date=short --reverse)

write_section() {
  local title="$1"
  local entries="$2"
  {
    printf '### %s\n\n' "$title"
    if [[ -n "$entries" ]]; then
      printf '%s\n' "$entries"
    else
      printf -- '- No changes.\n\n'
    fi
  } >> "$tmp_file"
}

tmp_file="$(mktemp)"
{
  printf '# Changelog\n\n'
  printf 'Generated from git history on %s.\n\n' "$generated_at"
  printf '## [%s] - %s\n\n' "$version" "$generated_at"
  printf 'Source range: `%s`\n\n' "$range_label"
} > "$tmp_file"

write_section "Added" "$added_entries"
write_section "Fixed" "$fixed_entries"
write_section "Changed" "$changed_entries"
write_section "Removed" "$removed_entries"

mkdir -p "$(dirname "$output")"
mv "$tmp_file" "$output"
printf 'Wrote %s\n' "$output"
