#!/usr/bin/env bash
# Standalone changelog generator for issue #1 of claude-builders-bounty.
# Requires Bash 4+ and Git. No API, network, or Python dependency.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--repo DIRECTORY] [--output PATH] [--force]

Generates a CHANGELOG.md based on non-merge commit subjects after the nearest
reachable Git tag. If the repository has no tags, uses all commits.

  --repo DIRECTORY  Git repository to inspect (default: current directory)
  --output PATH     Output file (default: CHANGELOG.md in repository root)
  --force           Allow replacing an existing regular output file
  --help            Show this help
USAGE
}

repo="."
output_arg="CHANGELOG.md"
force=0
while (( $# > 0 )); do
  case "$1" in
    --repo)
      (( $# >= 2 )) || { echo 'Missing value for --repo' >&2; exit 2; }
      repo="$2"; shift 2 ;;
    --output)
      (( $# >= 2 )) || { echo 'Missing value for --output' >&2; exit 2; }
      output_arg="$2"; shift 2 ;;
    --force) force=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

command -v git >/dev/null 2>&1 || { echo 'Git must be installed.' >&2; exit 2; }
[[ $(git -C "$repo" rev-parse --is-inside-work-tree 2>/dev/null || true) == true ]] || {
  echo "Not a Git working tree: $repo" >&2; exit 2;
}
repo_root=$(git -C "$repo" rev-parse --show-toplevel)
case "$output_arg" in
  /* | [A-Za-z]:/*) output="$output_arg" ;;
  *) output="$repo_root/$output_arg" ;;
esac
# Avoid symlink overwrites and unintentional replacement of owner files.
[[ ! -L "$output" ]] || { echo "Refusing symlink output: $output" >&2; exit 2; }
[[ ! -d "$output" ]] || { echo "Output is a directory: $output" >&2; exit 2; }
if [[ -e "$output" && $force -ne 1 ]]; then
  echo "Output already exists: $output (use --force to replace)" >&2
  exit 2
fi
[[ -d $(dirname "$output") ]] || { echo 'Output directory does not exist.' >&2; exit 2; }

tag=$(git -C "$repo_root" describe --tags --abbrev=0 HEAD 2>/dev/null || true)
if [[ -n "$tag" ]]; then
  revision="${tag}..HEAD"
  since="tag \`$tag\`"
else
  revision="HEAD"
  since="repository start (no reachable tags)"
fi

# Git output remains data: commit messages are never evaluated as shell code.
subjects=$(git -C "$repo_root" log --no-merges --format='%s' "$revision")
declare -a added=() fixed=() changed=() removed=()
re_added='^(feat|feature|add)(\([^)]*\))?!?:'
re_fixed='^(fix|bugfix|hotfix)(\([^)]*\))?!?:'
re_removed='^(remove|delete|drop)(\([^)]*\))?!?:'
re_changed='^(refactor|perf|docs|style|chore|test|build|ci|change|update)(\([^)]*\))?!?:'

while IFS= read -r message || [[ -n "$message" ]]; do
  [[ -n "$message" ]] || continue
  lowered=${message,,}
  if [[ "$lowered" =~ $re_removed ]] || [[ "$lowered" =~ ^(remove|delete|drop)[[:space:]] ]]; then
    removed+=("$message")
  elif [[ "$lowered" =~ $re_fixed ]] || [[ "$lowered" =~ (^|[[:space:]])(fix|fixed|bugfix|hotfix)[[:space:]] ]]; then
    fixed+=("$message")
  elif [[ "$lowered" =~ $re_added ]] || [[ "$lowered" =~ ^(add|introduce|create)[[:space:]] ]]; then
    added+=("$message")
  elif [[ "$lowered" =~ $re_changed ]]; then
    changed+=("$message")
  else
    changed+=("$message")
  fi
done <<< "$subjects"

# Atomic output minimizes corruption if the process is interrupted while writing.
tmp=$(mktemp "${output}.tmp.XXXXXXXX")
trap 'rm -f -- "$tmp"' EXIT
{
  printf '# Changelog\n\n'
  printf '## [Unreleased] - %s\n\n' "$(date -u +%Y-%m-%d)"
  printf 'Generated from commits since %s.\n\n' "$since"
  for category in Added Fixed Changed Removed; do
    printf '### %s\n\n' "$category"
    case "$category" in
      Added) entries=("${added[@]+"${added[@]}"}") ;;
      Fixed) entries=("${fixed[@]+"${fixed[@]}"}") ;;
      Changed) entries=("${changed[@]+"${changed[@]}"}") ;;
      Removed) entries=("${removed[@]+"${removed[@]}"}") ;;
    esac
    if (( ${#entries[@]} == 0 )); then
      printf '_None._\n'
    else
      for message in "${entries[@]}"; do
        # Subjects may contain arbitrary characters; never interpret them.
        printf -- '- %s\n' "$message"
      done
    fi
    printf '\n'
  done
} > "$tmp"
mv -f -- "$tmp" "$output"
trap - EXIT
printf 'Wrote %s (%s commits; after %s)\n' "$output" "$(( ${#added[@]} + ${#fixed[@]} + ${#changed[@]} + ${#removed[@]} ))" "$since"
