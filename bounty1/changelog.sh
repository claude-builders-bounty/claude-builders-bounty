#!/usr/bin/env bash
set -euo pipefail

# AI-assisted deliverable for:
# https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
#
# Generate a structured CHANGELOG.md from commits after the most recent tag.
# This script intentionally uses only Git and Bash so it can run in a small
# repository without a runtime or package installation.

usage() {
  cat <<'USAGE'
Usage: changelog.sh [options]

Options:
  --output FILE       Write the changelog to FILE (default: CHANGELOG.md)
  --version VERSION   Heading to use (default: Unreleased)
  --since REF         Use REF as the lower bound instead of the latest tag
  --help              Show this help

Examples:
  bash changelog.sh
  bash changelog.sh --output docs/CHANGELOG.md --version 1.4.0
  bash changelog.sh --since v1.2.0
USAGE
}

output_file="CHANGELOG.md"
release_name="Unreleased"
since_ref=""

while (($# > 0)); do
  case "$1" in
    --output)
      (($# >= 2)) || { echo "--output requires a file path" >&2; exit 2; }
      output_file="$2"
      shift 2
      ;;
    --version)
      (($# >= 2)) || { echo "--version requires a value" >&2; exit 2; }
      release_name="$2"
      shift 2
      ;;
    --since)
      (($# >= 2)) || { echo "--since requires a Git ref" >&2; exit 2; }
      since_ref="$2"
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

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "Run this script from inside a Git working tree." >&2
  exit 1
}

if [[ -z "$since_ref" ]]; then
  since_ref="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$since_ref" ]]; then
  git rev-parse --verify "${since_ref}^{commit}" >/dev/null 2>&1 || {
    echo "Git ref not found: $since_ref" >&2
    exit 1
  }
  log_args=("${since_ref}..HEAD")
  range_label="${since_ref}..HEAD"
else
  log_args=(HEAD)
  range_label="repository history (no reachable tag)"
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

remote_url="$(git config --get remote.origin.url 2>/dev/null || true)"
commit_base=""
if [[ "$remote_url" =~ ^git@github\.com:([^/]+/[^/]+)\.git$ ]]; then
  commit_base="https://github.com/${BASH_REMATCH[1]}"
elif [[ "$remote_url" =~ ^https?://github\.com/([^/]+/[^/]+)(\.git)?$ ]]; then
  commit_base="https://github.com/${BASH_REMATCH[1]%.git}"
fi

format_entry() {
  local hash="$1"
  local subject="$2"
  local short_hash="${hash:0:7}"
  if [[ -n "$commit_base" ]]; then
    printf '%s ([%s](%s/commit/%s))' "$subject" "$short_hash" "$commit_base" "$hash"
  else
    printf '%s (`%s`)' "$subject" "$short_hash"
  fi
}

categorize() {
  local subject_lc
  subject_lc="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$subject_lc" in
    feat:*|feat\(*\):*|feat\ *|add:*|add\ *|adds\ *|added:*|added\ *|introduce:*|introduces\ *|new:*|support:*|support\ *|implement:*|implement\ *)
      printf 'added'
      ;;
    fix:*|fix\(*\):*|fix\ *|fixes\ *|fixed:*|fixed\ *|bug:*|bug\ *|bugfix:*|bugfix\ *|repair:*|repair\ *|correct:*|correct\ *|resolve:*|resolve\ *|patch:*|patch\ *|hotfix:*)
      printf 'fixed'
      ;;
    remove:*|remove\ *|removes\ *|removed:*|removed\ *|delete:*|delete\ *|deletes\ *|deleted:*|deleted\ *|drop:*|drop\ *|deprecate:*|deprecates:*|deprecate\ *)
      printf 'removed'
      ;;
    *)
      printf 'changed'
      ;;
  esac
}

while IFS=$'	' read -r hash subject; do
  [[ -n "$hash" ]] || continue
  # Strip a conventional-commit scope and an optional breaking-change marker
  # only when it is at the beginning; keep the actual human-readable subject.
  clean_subject="$(printf '%s' "$subject" | sed -E 's/^[[:alnum:]_-]+(\([^)]*\))?!:[[:space:]]*//')"
  entry="$(format_entry "$hash" "$clean_subject")"
  case "$(categorize "$subject")" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    removed) removed+=("$entry") ;;
    changed) changed+=("$entry") ;;
  esac
done < <(git log --no-merges --format='%H%x09%s' "${log_args[@]}")

mkdir -p "$(dirname -- "$output_file")"
tmp_file="$(mktemp "${output_file}.tmp.XXXXXX")"
trap 'rm -f -- "$tmp_file"' EXIT

{
  printf '# Changelog\n\n'
  printf 'Generated from `%s` on %s.\n\n' "$range_label" "$(date -u +%Y-%m-%d)"
  printf '## %s\n\n' "$release_name"

  printf '### Added\n\n'
  if ((${#added[@]})); then
    printf -- '- %s\n' "${added[@]}"
  else
    printf -- '- None\n'
  fi
  printf '\n### Fixed\n\n'
  if ((${#fixed[@]})); then
    printf -- '- %s\n' "${fixed[@]}"
  else
    printf -- '- None\n'
  fi
  printf '\n### Changed\n\n'
  if ((${#changed[@]})); then
    printf -- '- %s\n' "${changed[@]}"
  else
    printf -- '- None\n'
  fi
  printf '\n### Removed\n\n'
  if ((${#removed[@]})); then
    printf -- '- %s\n' "${removed[@]}"
  else
    printf -- '- None\n'
  fi
} >"$tmp_file"

mv -- "$tmp_file" "$output_file"
trap - EXIT
printf 'Wrote %s\n' "$output_file"
