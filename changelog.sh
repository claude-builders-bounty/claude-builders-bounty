#!/usr/bin/env bash
set -euo pipefail

output=CHANGELOG.md
while getopts ':o:h' option; do
  case "$option" in
    o) output=$OPTARG ;;
    h)
      printf 'Usage: %s [-o OUTPUT]\n' "${0##*/}"
      exit 0
      ;;
    :)
      printf 'Missing argument for -%s\n' "$OPTARG" >&2
      exit 2
      ;;
    \?)
      printf 'Unknown option: -%s\n' "$OPTARG" >&2
      exit 2
      ;;
  esac
done
shift "$((OPTIND - 1))"
if (($#)); then
  printf 'Unexpected argument: %s\n' "$1" >&2
  exit 2
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  printf 'Run this script from inside a Git repository.\n' >&2
  exit 1
fi

last_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [[ -n "$last_tag" ]]; then
  range="$last_tag..HEAD"
else
  range=HEAD
fi

# Capture separately so Git failures propagate instead of being hidden by mapfile.
commit_log=$(git log --reverse --format='%h%x09%s' "$range")
commits=()
if [[ -n "$commit_log" ]]; then
  mapfile -t commits <<<"$commit_log"
fi

classify() {
  local subject=${1,,}
  case "$subject" in
    feat\(*|add\(*|new\(*|feat:*|feat!:*|add:*|add!:*|new:*|new!:*) echo Added ;;
    fix\(*|bug\(*|hotfix\(*|fix:*|fix!:*|bug:*|bug!:*|hotfix:*|hotfix!:*) echo Fixed ;;
    remove\(*|delete\(*|drop\(*|remove:*|remove!:*|delete:*|delete!:*|drop:*|drop!:*) echo Removed ;;
    *)
      case "$subject" in
        add\ *|added\ *|new\ *) echo Added ;;
        fix\ *|fixed\ *|bug\ *|hotfix\ *) echo Fixed ;;
        remove\ *|removed\ *|delete\ *|deleted\ *|drop\ *) echo Removed ;;
        *) echo Changed ;;
      esac
      ;;
  esac
}

added=() fixed=() changed=() removed=()
for commit in "${commits[@]}"; do
  short_id=${commit%%$'\t'*}
  subject=${commit#*$'\t'}
  entry="- ${subject} (${short_id})"
  case "$(classify "$subject")" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
    Changed) changed+=("$entry") ;;
  esac
done

output_dir=$(dirname -- "$output")
mkdir -p -- "$output_dir"
tmp=$(mktemp "${output}.tmp.XXXXXX")
cleanup() { rm -f -- "$tmp"; }
trap cleanup EXIT

{
  printf '# Changelog\n\n'
  if [[ -n "$last_tag" ]]; then
    printf '## Unreleased (since %s)\n\n' "$last_tag"
  else
    printf '## Unreleased\n\n'
  fi
  printf '_Generated on %s from Git history._\n\n' "$(date -u +%Y-%m-%d)"
  for category in Added Fixed Changed Removed; do
    printf '### %s\n\n' "$category"
    case "$category" in
      Added) entries=("${added[@]}") ;;
      Fixed) entries=("${fixed[@]}") ;;
      Changed) entries=("${changed[@]}") ;;
      Removed) entries=("${removed[@]}") ;;
    esac
    if ((${#entries[@]})); then
      printf '%s\n' "${entries[@]}"
    else
      printf '_None._\n'
    fi
    if [[ "$category" != Removed ]]; then
      printf '\n'
    fi
  done
} >"$tmp"
mv -- "$tmp" "$output"
printf 'Wrote %s (%d commits)\n' "$output" "${#commits[@]}"
