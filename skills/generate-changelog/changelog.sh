#!/usr/bin/env bash
set -eo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  revision_range="${latest_tag}..HEAD"
  source_label="since ${latest_tag}"
else
  revision_range="HEAD"
  source_label="from all commits because no git tags were found"
fi

generated_at="$(date -u +%Y-%m-%d)"
remote_url="$(git config --get remote.origin.url || true)"
if [[ -n "$remote_url" ]]; then
  repo_name="$(basename "${remote_url%.git}")"
else
  repo_name="$(basename "$(git rev-parse --show-toplevel)")"
fi

added=()
fixed=()
changed=()
removed=()

while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  entry="- ${subject}"

  if [[ "$normalized" =~ (^|[^a-z])(remove|removed|removes|delete|deleted|deletes|drop|dropped|drops|deprecate|deprecated)([^a-z]|$) ]]; then
    removed+=("$entry")
  elif [[ "$normalized" =~ ^(feat|feature)(\(.+\))?: ]] || [[ "$normalized" =~ (^|[^a-z])(add|added|adds|introduce|introduced|new)([^a-z]|$) ]]; then
    added+=("$entry")
  elif [[ "$normalized" =~ ^(fix|bugfix)(\(.+\))?: ]] || [[ "$normalized" =~ (^|[^a-z])(fix|fixed|fixes|bug|repair|patched|resolve|resolved)([^a-z]|$) ]]; then
    fixed+=("$entry")
  else
    changed+=("$entry")
  fi
done < <(git log --no-merges --format=%s "$revision_range")

write_section() {
  local title="$1"
  shift
  local -a entries=("$@")

  printf '### %s\n\n' "$title"
  if ((${#entries[@]} == 0)); then
    printf -- '- No changes detected.\n\n'
    return
  fi

  printf '%s\n' "${entries[@]}"
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes for `%s` are grouped by commit intent.\n\n' "$repo_name"
  printf '## Unreleased - %s\n\n' "$generated_at"
  printf '_Generated from git history %s._\n\n' "$source_label"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$output_file"

echo "Wrote ${output_file}"
