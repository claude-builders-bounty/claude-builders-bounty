#!/usr/bin/env bash
set -euo pipefail

output_file="CHANGELOG.md"
stdout=false
since_ref=""

usage() {
  cat <<'EOF'
Usage: bash changelog.sh [--output CHANGELOG.md] [--stdout] [--since REF]

Generate a structured CHANGELOG.md from commits since the last git tag.

Options:
  --output FILE   Write changelog to FILE (default: CHANGELOG.md)
  --stdout        Print changelog instead of writing a file
  --since REF     Override the starting ref/tag
  -h, --help      Show this help
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output)
      output_file="${2:?--output requires a file path}"
      shift 2
      ;;
    --stdout)
      stdout=true
      shift
      ;;
    --since)
      since_ref="${2:?--since requires a git ref}"
      shift 2
      ;;
    -h | --help)
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

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository" >&2
  exit 1
fi

if [ -z "$since_ref" ]; then
  since_ref="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

range="HEAD"
if [ -n "$since_ref" ]; then
  range="${since_ref}..HEAD"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added="$tmp_dir/added"
fixed="$tmp_dir/fixed"
changed="$tmp_dir/changed"
removed="$tmp_dir/removed"
: >"$added"
: >"$fixed"
: >"$changed"
: >"$removed"

categorize_commit() {
  subject_lower="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$subject_lower" in
    add* | "add "* | feat:* | feat\(* | "feat "* | create* | introduce* | implement*)
      printf 'Added'
      ;;
    fix* | "fix "* | bug* | patch* | hotfix* | correct* | repair* | security*)
      printf 'Fixed'
      ;;
    remove* | delete* | drop* | deprecat* | "rm "*)
      printf 'Removed'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

commit_count=0
while IFS="$(printf '\t')" read -r hash subject; do
  [ -n "$hash" ] || continue
  category="$(categorize_commit "$subject")"
  line="- ${subject} (${hash})"
  case "$category" in
    Added) printf '%s\n' "$line" >>"$added" ;;
    Fixed) printf '%s\n' "$line" >>"$fixed" ;;
    Removed) printf '%s\n' "$line" >>"$removed" ;;
    *) printf '%s\n' "$line" >>"$changed" ;;
  esac
  commit_count=$((commit_count + 1))
done <<EOF
$(git log --no-merges --pretty=format:'%h%x09%s' "$range")
EOF

repo_name="$(basename "$(git rev-parse --show-toplevel)")"
head_ref="$(git rev-parse --short HEAD)"
today="$(date +%F)"

write_section() {
  title="$1"
  file="$2"
  printf '\n### %s\n\n' "$title"
  if [ -s "$file" ]; then
    cat "$file"
  else
    printf '_No %s changes._\n' "$(printf '%s' "$title" | tr '[:upper:]' '[:lower:]')"
  fi
}

render_changelog() {
  printf '# Changelog\n\n'
  printf 'Generated from `%s` at `%s` on %s.\n\n' "$repo_name" "$head_ref" "$today"
  if [ -n "$since_ref" ]; then
    printf 'Commit range: `%s..HEAD`.\n\n' "$since_ref"
  else
    printf 'Commit range: full repository history because no git tag was found.\n\n'
  fi

  if [ "$commit_count" -eq 0 ]; then
    printf '_No commits found for this range._\n'
    return
  fi

  printf '## Unreleased - %s\n' "$today"
  write_section "Added" "$added"
  write_section "Fixed" "$fixed"
  write_section "Changed" "$changed"
  write_section "Removed" "$removed"
}

if [ "$stdout" = true ]; then
  render_changelog
else
  render_changelog >"$output_file"
  echo "Wrote $output_file"
fi
