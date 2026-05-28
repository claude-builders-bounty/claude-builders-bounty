#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--output CHANGELOG.md] [--repo PATH]

Generate a structured CHANGELOG.md from commits since the last git tag.
USAGE
}

output_file="CHANGELOG.md"
repo_path="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      output_file="${2:-}"
      shift 2
      ;;
    --repo)
      repo_path="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$output_file" || -z "$repo_path" ]]; then
  echo "--output and --repo require non-empty values" >&2
  exit 2
fi

git_cmd() {
  git -C "$repo_path" "$@"
}

git_cmd rev-parse --is-inside-work-tree >/dev/null

latest_tag="$(git_cmd describe --tags --abbrev=0 2>/dev/null || true)"
range="HEAD"
base_label="initial commit"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  base_label="$latest_tag"
fi

if ! git_cmd rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "Repository has no commits" >&2
  exit 1
fi

mapfile -t commits < <(git_cmd log --reverse --format='%h%x1f%s' "$range")

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

trim_subject() {
  local subject="$1"
  subject="${subject#*: }"
  subject="${subject#*) }"
  printf '%s' "$subject"
}

append_commit() {
  local bucket="$1"
  local hash="$2"
  local subject="$3"
  local entry="- $(trim_subject "$subject") (\`$hash\`)"

  case "$bucket" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    removed) removed+=("$entry") ;;
    changed) changed+=("$entry") ;;
  esac
}

for record in "${commits[@]}"; do
  hash="${record%%$'\x1f'*}"
  subject="${record#*$'\x1f'}"
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feature:*|add:*|added:*)
      append_commit added "$hash" "$subject"
      ;;
    fix:*|fixed:*|bugfix:*|repair:*)
      append_commit fixed "$hash" "$subject"
      ;;
    remove:*|removed:*|delete:*|deleted:*)
      append_commit removed "$hash" "$subject"
      ;;
    refactor:*|change:*|changed:*|chore:*|perf:*|docs:*|style:*|test:*|build:*|ci:*)
      append_commit changed "$hash" "$subject"
      ;;
    *)
      if [[ "$lower" =~ (^|[[:space:]])(add|adds|added|implement|implements|implemented|create|creates|created)([[:space:]]|$) ]]; then
        append_commit added "$hash" "$subject"
      elif [[ "$lower" =~ (^|[[:space:]])(fix|fixes|fixed|repair|repairs|repaired|bug)([[:space:]]|$) ]]; then
        append_commit fixed "$hash" "$subject"
      elif [[ "$lower" =~ (^|[[:space:]])(remove|removes|removed|delete|deletes|deleted)([[:space:]]|$) ]]; then
        append_commit removed "$hash" "$subject"
      else
        append_commit changed "$hash" "$subject"
      fi
      ;;
  esac
done

release_name="Unreleased"
today="$(date +%Y-%m-%d)"

tmp="$(mktemp)"
{
  echo "# Changelog"
  echo
  echo "## [$release_name] - $today"
  echo
  echo "_Generated from commits since $base_label._"
  echo

  printed_section=0

  print_section() {
    local title="$1"
    shift
    local entries=("$@")

    if [[ ${#entries[@]} -eq 0 ]]; then
      return
    fi

    if [[ "$printed_section" -eq 1 ]]; then
      echo
    fi

    echo "### $title"
    printf '%s\n' "${entries[@]}"
    printed_section=1
  }

  print_section "Added" "${added[@]}"
  print_section "Fixed" "${fixed[@]}"
  print_section "Changed" "${changed[@]}"
  print_section "Removed" "${removed[@]}"

  if [[ ${#commits[@]} -eq 0 ]]; then
    echo "No changes since $base_label."
  fi
} > "$tmp"

mv "$tmp" "$output_file"
echo "Generated $output_file from ${#commits[@]} commit(s)."
