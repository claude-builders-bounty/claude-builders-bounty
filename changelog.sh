#!/usr/bin/env bash
# Generate a categorized CHANGELOG.md from commits since the latest reachable git tag.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--repo PATH] [--output PATH] [--since TAG]

Options:
  --repo PATH    Git repository (default: current directory)
  --output PATH  Output file (default: CHANGELOG.md inside the repository)
  --since TAG    Use this tag instead of the latest reachable tag
  -h, --help     Show this help
USAGE
}
repo="$(pwd)"
output=""
since_tag=""
while (($#)); do
  case "$1" in
    --repo) [[ $# -ge 2 ]] || { echo "Missing value for --repo" >&2; exit 2; }; repo="$2"; shift 2 ;;
    --output) [[ $# -ge 2 ]] || { echo "Missing value for --output" >&2; exit 2; }; output="$2"; shift 2 ;;
    --since) [[ $# -ge 2 ]] || { echo "Missing value for --since" >&2; exit 2; }; since_tag="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done
command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 1; }
repo="$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null)" || { echo "Not a git repository: $repo" >&2; exit 1; }
if [[ -z "$output" ]]; then output="$repo/CHANGELOG.md"; elif [[ "$output" != /* ]]; then output="$repo/$output"; fi
if [[ -n "$since_tag" ]]; then
  git -C "$repo" rev-parse --verify "refs/tags/$since_tag^{commit}" >/dev/null 2>&1 || { echo "Tag not found: $since_tag" >&2; exit 1; }
  range="$since_tag..HEAD"
else
  since_tag="$(git -C "$repo" describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "$since_tag" ]]; then range="$since_tag..HEAD"; else range="HEAD"; fi
fi
# Use NUL separators so unusual commit subjects cannot corrupt the parser.
mapfile -d '' -t commits < <(git -C "$repo" log "$range" --format='%H%x00%s%x00' 2>/dev/null | python3 -c 'import sys; d=sys.stdin.buffer.read().split(b"\0"); sys.stdout.buffer.write(b"\0".join(d[:-1]) + (b"\0" if len(d)>1 else b""))')
if ((${#commits[@]} % 2 != 0)); then echo "Could not parse git history" >&2; exit 1; fi
added=(); fixed=(); changed=(); removed=(); other=()
for ((i=0; i<${#commits[@]}; i+=2)); do
  subject="${commits[i+1]}"
  # Strip conventional-commit scope and optional breaking marker before classification.
  normalized="${subject#*: }"
  case "${subject,,}" in
    feat:*|feat\(*\):*|feature:*|add:*|added:*) added+=("$subject") ;;
    fix:*|fix\(*\):*|bugfix:*|bug:*|hotfix:*) fixed+=("$subject") ;;
    refactor:*|perf:*|perf\(*\):*|change:*|changed:*|docs:*|style:*|test:*|build:*|ci:*|chore:*) changed+=("$subject") ;;
    remove:*|removed:*|delete:*|deleted:*|revert:*|revert\(*\):*) removed+=("$subject") ;;
    *) other+=("$subject") ;;
  esac
done
{
  echo "# Changelog"
  echo
  if [[ -n "$since_tag" ]]; then printf "Changes since %s.\n" "$since_tag"; else echo "Changes from repository history (no reachable tag was found)."; fi
  echo
  for category in Added Fixed Changed Removed; do
    case "$category" in Added) entries=("${added[@]}");; Fixed) entries=("${fixed[@]}");; Changed) entries=("${changed[@]}");; Removed) entries=("${removed[@]}");; esac
    if ((${#entries[@]})); then
      echo "## $category"; echo
      for entry in "${entries[@]}"; do printf -- '- %s\n' "$entry"; done
      echo
    fi
  done
  if ((${#other[@]})); then
    echo "## Changed (uncategorized)"; echo
    for entry in "${other[@]}"; do printf -- '- %s\n' "$entry"; done
    echo
  fi
  if ((${#commits[@]} == 0)); then echo "No commits found in the selected range."; echo; fi
} > "$output"
printf 'Wrote %s (%s commits)\n' "$output" "$((${#commits[@]} / 2))"
