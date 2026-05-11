#!/usr/bin/env bash
set -eo pipefail

repo="."
from_ref=""
to_ref="HEAD"
output_file="CHANGELOG.md"
version="Unreleased"
write_stdout="false"

usage() {
  printf '%s\n' \
    "Usage: bash scripts/changelog.sh [options]" \
    "" \
    "Options:" \
    "  --repo PATH        Git repository path (default: .)" \
    "  --from REF         Start after this ref (default: latest tag)" \
    "  --to REF           End ref (default: HEAD)" \
    "  --output PATH      Output changelog path (default: CHANGELOG.md)" \
    "  --version TEXT     Changelog version heading (default: Unreleased)" \
    "  --stdout           Print changelog instead of writing a file" \
    "  -h, --help         Show this help"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:?--repo requires a path}"
      shift 2
      ;;
    --from)
      from_ref="${2:?--from requires a ref}"
      shift 2
      ;;
    --to)
      to_ref="${2:?--to requires a ref}"
      shift 2
      ;;
    --output)
      output_file="${2:?--output requires a path}"
      shift 2
      ;;
    --version)
      version="${2:?--version requires text}"
      shift 2
      ;;
    --stdout)
      write_stdout="true"
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

git -C "$repo" rev-parse --is-inside-work-tree >/dev/null

if [[ -z "$from_ref" ]]; then
  from_ref="$(git -C "$repo" describe --tags --abbrev=0 "$to_ref" 2>/dev/null || true)"
fi

if [[ -n "$from_ref" ]]; then
  range="${from_ref}..${to_ref}"
else
  range="$to_ref"
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

strip_conventional_prefix() {
  local subject="$1"
  local conventional_re='^[A-Za-z]+(\([^)]+\))?!?:[[:space:]]*(.*)$'
  if [[ "$subject" =~ $conventional_re ]]; then
    printf '%s\n' "${BASH_REMATCH[2]}"
  else
    printf '%s\n' "$subject"
  fi
}

add_entry() {
  local category="$1"
  local entry="$2"

  case "$category" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    removed) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
}

categorize_subject() {
  local subject_lc="$1"
  local feat_re='^(feat|feature)(\([^)]+\))?!?: '
  local fix_re='^(fix|bugfix|hotfix)(\([^)]+\))?!?: '
  local remove_re='^(remove|removed|delete|deleted|drop|dropped|deprecate)(\([^)]+\))?!?:?'

  if [[ "$subject_lc" =~ $feat_re ]] ||
    [[ "$subject_lc" =~ ^(add|added)[[:space:]] ]]; then
    printf 'added\n'
  elif [[ "$subject_lc" =~ $fix_re ]] ||
    [[ "$subject_lc" =~ ^(fix|fixed)[[:space:]] ]]; then
    printf 'fixed\n'
  elif [[ "$subject_lc" =~ $remove_re ]] ||
    [[ "$subject_lc" =~ ^(remove|removed|delete|deleted|drop|dropped|deprecate)[[:space:]] ]]; then
    printf 'removed\n'
  else
    printf 'changed\n'
  fi
}

while IFS= read -r -d $'\x1e' record; do
  record="${record#$'\n'}"
  [[ -z "$record" ]] && continue
  IFS=$'\x1f' read -r hash subject body <<< "$record"
  [[ -z "${hash:-}" || -z "${subject:-}" ]] && continue

  subject_lc="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  category="$(categorize_subject "$subject_lc")"
  message="$(strip_conventional_prefix "$subject")"
  entry="- ${message} (${hash:0:7})"

  if [[ "${body:-}" == *"BREAKING CHANGE"* ]]; then
    entry="${entry} - BREAKING CHANGE"
  fi

  add_entry "$category" "$entry"
done < <(git -C "$repo" log --reverse --no-merges --format='%H%x1f%s%x1f%b%x1e' "$range")

render_section() {
  local heading="$1"
  shift
  local entries=("$@")

  printf '### %s\n\n' "$heading"
  if [[ ${#entries[@]} -eq 0 ]]; then
    printf -- '- No changes.\n'
  else
    printf '%s\n' "${entries[@]}"
  fi
  printf '\n'
}

changelog="$(
  printf '# Changelog\n\n'
  if [[ -n "$from_ref" ]]; then
    printf '## %s\n\nChanges since `%s`.\n\n' "$version" "$from_ref"
  else
    printf '## %s\n\nAll commits through `%s`.\n\n' "$version" "$to_ref"
  fi
  render_section "Added" "${added[@]}"
  render_section "Fixed" "${fixed[@]}"
  render_section "Changed" "${changed[@]}"
  render_section "Removed" "${removed[@]}"
)"

if [[ "$write_stdout" == "true" ]]; then
  printf '%s\n' "$changelog"
else
  printf '%s\n' "$changelog" > "$output_file"
  printf 'Wrote %s\n' "$output_file"
fi
