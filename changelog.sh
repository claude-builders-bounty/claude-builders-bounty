#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: changelog.sh [--repo PATH] [--since REF] [--output PATH|-]

Generate a structured CHANGELOG.md from commits after the latest tag.
USAGE
}

repo="$(pwd)"
since=""
output="-"

while (($#)); do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || { echo "--repo needs a path" >&2; exit 2; }
      repo=$2; shift 2 ;;
    --since)
      [[ $# -ge 2 ]] || { echo "--since needs a git ref" >&2; exit 2; }
      since=$2; shift 2 ;;
    --output)
      [[ $# -ge 2 ]] || { echo "--output needs a path or -" >&2; exit 2; }
      output=$2; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! -d "$repo/.git" && ! -f "$repo/.git" ]]; then
  echo "Not a git repository: $repo" >&2
  exit 1
fi
repo=$(git -C "$repo" rev-parse --show-toplevel)

if [[ -z "$since" ]]; then
  since=$(git -C "$repo" describe --tags --abbrev=0 2>/dev/null || true)
fi

range="HEAD"
if [[ -n "$since" ]]; then
  git -C "$repo" rev-parse --verify "$since^{commit}" >/dev/null 2>&1 || {
    echo "Unknown git ref: $since" >&2
    exit 1
  }
  range="$since..HEAD"
fi

added=(); fixed=(); changed=(); removed=(); other=()
while IFS=$'\t' read -r subject hash; do
  [[ -n "$subject" ]] || continue
  type=${subject%%:*}
  normalized=$(printf '%s' "$type" | tr '[:upper:]' '[:lower:]')
  line="- $subject ($hash)"
  case "$normalized" in
    feat|feature|add|added|new) added+=("$line") ;;
    fix|fixed|bug|bugfix|hotfix) fixed+=("$line") ;;
    remove|removed|delete|deprecate) removed+=("$line") ;;
    refactor|perf|performance|change|changed|docs|doc|test|tests|chore|ci|build|style|revert) changed+=("$line") ;;
    *) other+=("$line") ;;
  esac
done < <(git -C "$repo" log --no-merges --format='%s%x09%h' "$range")

if ((${#other[@]})); then
  changed+=("${other[@]}")
fi

if [[ -n "$since" ]]; then
  source_line="since $since"
else
  source_line="from repository history"
fi

print_section() {
  local title=$1
  shift
  printf '## %s\n\n' "$title"
  if (($#)); then
    printf '%s\n' "$@"
  else
    printf '%s\n' '- None'
  fi
  printf '\n'
}

generate() {
  printf '# Changelog\n\nGenerated %s on %s.\n\n' "$source_line" "$(date -u +%Y-%m-%d)"
  if ((${#added[@]})); then print_section 'Added' "${added[@]}"; else print_section 'Added'; fi
  if ((${#fixed[@]})); then print_section 'Fixed' "${fixed[@]}"; else print_section 'Fixed'; fi
  if ((${#changed[@]})); then print_section 'Changed' "${changed[@]}"; else print_section 'Changed'; fi
  if ((${#removed[@]})); then print_section 'Removed' "${removed[@]}"; else print_section 'Removed'; fi
}

if [[ "$output" == "-" ]]; then
  generate
else
  mkdir -p "$(dirname "$output")"
  generate > "$output"
  echo "Wrote $output" >&2
fi
