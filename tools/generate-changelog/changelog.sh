#!/usr/bin/env bash
set -euo pipefail

output="CHANGELOG.md"
repo="."
from_ref=""
version=""

usage() {
  cat <<'EOF'
Usage:
  bash tools/generate-changelog/changelog.sh [options]

Options:
  --repo <path>       Git repository path. Defaults to current directory.
  --output <path>     Output changelog path. Defaults to CHANGELOG.md.
  --from <ref>        Start ref. Defaults to the last git tag, or all history if no tag exists.
  --version <name>    Version heading. Defaults to the current date.
  --help              Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:?Missing value for --repo}"
      shift 2
      ;;
    --output)
      output="${2:?Missing value for --output}"
      shift 2
      ;;
    --from)
      from_ref="${2:?Missing value for --from}"
      shift 2
      ;;
    --version)
      version="${2:?Missing value for --version}"
      shift 2
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $repo" >&2
  exit 1
fi

if [[ -z "$from_ref" ]]; then
  from_ref="$(git -C "$repo" describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -z "$version" ]]; then
  version="$(date -u +%Y-%m-%d)"
fi

range_label="all history"
range_arg=""
if [[ -n "$from_ref" ]]; then
  range_arg="${from_ref}..HEAD"
  range_label="since ${from_ref}"
fi

added=""
fixed=""
changed=""
removed=""
commit_count=0

while IFS= read -r entry || [[ -n "$entry" ]]; do
  [[ -z "$entry" ]] && continue
  commit_count=$((commit_count + 1))
  subject="${entry%$'\t'*}"
  hash="${entry##*$'\t'}"
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  line="- ${subject} (${hash})"$'\n'

  case "$normalized" in
    feat:*|feat\(*|add:*|add\(*|added:*|create:*|create\(*)
      added="${added}${line}"
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|patch:*|hotfix:*)
      fixed="${fixed}${line}"
      ;;
    remove:*|remove\(*|removed:*|delete:*|delete\(*|drop:*|drop\(*)
      removed="${removed}${line}"
      ;;
    *)
      changed="${changed}${line}"
      ;;
  esac
done < <(
  if [[ -n "$range_arg" ]]; then
    git -C "$repo" log "$range_arg" --pretty=format:'%s%x09%h' --no-merges
  else
    git -C "$repo" log --pretty=format:'%s%x09%h' --no-merges
  fi
)

write_section() {
  local title="$1"
  local lines="$2"

  printf '\n## %s\n\n' "$title"
  if [[ -z "$lines" ]]; then
    printf -- '- No changes.\n'
    return
  fi

  printf '%s' "$lines"
}

{
  printf '# Changelog\n\n'
  printf 'Generated from git history %s.\n\n' "$range_label"
  printf '## %s\n' "$version"
  write_section "Added" "$added"
  write_section "Fixed" "$fixed"
  write_section "Changed" "$changed"
  write_section "Removed" "$removed"
} > "$output"

echo "Wrote ${output} from ${commit_count} commit(s)."
