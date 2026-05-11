#!/usr/bin/env bash
set -eo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

die() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

command -v git >/dev/null 2>&1 || die "git is required"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "run this script inside a git repository"

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  range="HEAD"
  range_label="from all commits because no git tags were found"
fi

remote_url="$(git config --get remote.origin.url || true)"
commit_url_base=""
if [[ "$remote_url" =~ ^git@github\.com:(.+)\.git$ ]]; then
  commit_url_base="https://github.com/${BASH_REMATCH[1]}/commit"
elif [[ "$remote_url" =~ ^https://github\.com/(.+)\.git$ ]]; then
  commit_url_base="https://github.com/${BASH_REMATCH[1]}/commit"
elif [[ "$remote_url" =~ ^https://github\.com/(.+)$ ]]; then
  commit_url_base="https://github.com/${BASH_REMATCH[1]}/commit"
fi

categorize_commit() {
  local subject_lc="$1"

  case "$subject_lc" in
    fix:*|fix\(*|fixed*|bugfix*|hotfix*|repair*|resolve*|resolved*)
      printf 'Fixed'
      return
      ;;
    feat:*|feat\(*|feature:*|add*|added*|create*|created*|implement*|implemented*|introduce*|introduced*|new*)
      printf 'Added'
      return
      ;;
    remove*|removed*|delete*|deleted*|drop*|dropped*|deprecate*|deprecated*)
      printf 'Removed'
      return
      ;;
  esac

  if [[ "$subject_lc" =~ (fix|bug|crash|error|regression|broken) ]]; then
    printf 'Fixed'
  elif [[ "$subject_lc" =~ (add|create|feature|implement|introduce|support) ]]; then
    printf 'Added'
  elif [[ "$subject_lc" =~ (remove|delete|drop|deprecat) ]]; then
    printf 'Removed'
  else
    printf 'Changed'
  fi
}

format_commit_link() {
  local hash="$1"
  local short_hash
  short_hash="$(git rev-parse --short "$hash")"

  if [[ -n "$commit_url_base" ]]; then
    printf '([%s](%s/%s))' "$short_hash" "$commit_url_base" "$hash"
  else
    printf '(%s)' "$short_hash"
  fi
}

sanitize_subject() {
  local subject="$1"
  subject="${subject//$'\r'/ }"
  subject="${subject//$'\n'/ }"
  printf '%s' "$subject"
}

added=()
fixed=()
changed=()
removed=()

while IFS=$'\t' read -r hash subject; do
  [[ -n "${hash:-}" ]] || continue
  subject="$(sanitize_subject "$subject")"
  subject_lc="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  category="$(categorize_commit "$subject_lc")"
  entry="- ${subject} $(format_commit_link "$hash")"

  case "$category" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
done < <(git log --no-merges --reverse --format=$'%H\t%s' "$range")

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '### %s\n\n' "$title"
  if ((${#entries[@]} == 0)); then
    printf -- '- No changes.\n\n'
    return
  fi

  printf '%s\n' "${entries[@]}"
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$(date +%Y-%m-%d)"
  printf '_Generated from git history %s._\n\n' "$range_label"
  write_section 'Added' "${added[@]}"
  write_section 'Fixed' "${fixed[@]}"
  write_section 'Changed' "${changed[@]}"
  write_section 'Removed' "${removed[@]}"
} >"$OUTPUT_FILE"

printf 'Wrote %s using commits %s.\n' "$OUTPUT_FILE" "$range_label"
