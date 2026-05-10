#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash changelog.sh [--from <ref>] [--to <ref>] [--repo <path>] [--output <file>] [--stdout]

Generates a Markdown changelog from Git commit history.

Options:
  --from <ref>     Start ref. Defaults to the latest reachable tag, or the
                   first commit when the repository has no tags.
  --to <ref>       End ref. Defaults to HEAD.
  --repo <path>    Repository path. Defaults to the current directory.
  --output <file>  Write Markdown to a file. Defaults to CHANGELOG.md.
  --stdout         Print Markdown to stdout instead of writing a file.
  -h, --help       Show this help.
EOF
}

repo="."
from_ref=""
to_ref="HEAD"
output_file=""
write_stdout=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)
      from_ref="${2:-}"
      shift 2
      ;;
    --to)
      to_ref="${2:-}"
      shift 2
      ;;
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --output)
      output_file="${2:-}"
      shift 2
      ;;
    --stdout)
      write_stdout=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

git_cmd() {
  git -C "$repo" "$@"
}

if ! git_cmd rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a Git repository: $repo" >&2
  exit 1
fi

if [[ -z "$from_ref" ]]; then
  if from_ref="$(git_cmd describe --tags --abbrev=0 "$to_ref" 2>/dev/null)"; then
    range="$from_ref..$to_ref"
  else
    range="$to_ref"
  fi
else
  range="$from_ref..$to_ref"
fi

if ! git_cmd rev-parse --verify "$to_ref^{commit}" >/dev/null 2>&1; then
  echo "Invalid --to ref: $to_ref" >&2
  exit 1
fi

if [[ "$range" == *".."* ]] && ! git_cmd rev-parse --verify "$from_ref^{commit}" >/dev/null 2>&1; then
  echo "Invalid --from ref: $from_ref" >&2
  exit 1
fi

commit_count="$(git_cmd rev-list --count "$range")"
generated_on="$(date -u +"%Y-%m-%d")"
repo_root="$(git_cmd rev-parse --show-toplevel)"
repo_name="$(basename "$repo_root")"

section_order=(added fixed changed removed)

section_title() {
  case "$1" in
    added) echo "Added" ;;
    fixed) echo "Fixed" ;;
    removed) echo "Removed" ;;
    *) echo "Changed" ;;
  esac
}

category_for_type() {
  case "$1" in
    feat|add|added) echo "added" ;;
    fix|fixed|bugfix) echo "fixed" ;;
    remove|removed|delete|deleted) echo "removed" ;;
    *) echo "changed" ;;
  esac
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

conventional_commit_pattern='^([a-zA-Z]+)(\([^)]+\))?(!)?:[[:space:]]*(.+)$'

for key in "${section_order[@]}"; do
  : > "$tmp_dir/$key"
done

while IFS=$'\t' read -r hash subject author date || [[ -n "$hash" ]]; do
  [[ -n "$hash" ]] || continue

  category="changed"
  description="$subject"

  if [[ "$subject" =~ $conventional_commit_pattern ]]; then
    detected_type="$(printf '%s' "${BASH_REMATCH[1]}" | tr '[:upper:]' '[:lower:]')"
    description="${BASH_REMATCH[4]}"
    category="$(category_for_type "$detected_type")"
  elif [[ "$subject" =~ ^[Rr]emov(e|ed)[[:space:]] || "$subject" =~ ^[Dd]elet(e|ed)[[:space:]] ]]; then
    category="removed"
  fi

  printf -- '- %s (%s, %s, %s)\n' "$description" "$hash" "$author" "$date" >> "$tmp_dir/$category"
done < <(git_cmd log "$range" --no-merges --date=short --pretty=format:'%h%x09%s%x09%an%x09%ad')

render_changelog() {
  cat <<EOF
# Changelog

Generated from \`${repo_name}\` on ${generated_on}.

- Range: \`${range}\`
- Commits: ${commit_count}

EOF

  if [[ "$commit_count" == "0" ]]; then
    echo "No commits found for this range."
    return
  fi

  for key in "${section_order[@]}"; do
    if [[ -s "$tmp_dir/$key" ]]; then
      echo "## $(section_title "$key")"
      cat "$tmp_dir/$key"
      echo
    fi
  done
}

if [[ "$write_stdout" == true ]]; then
  render_changelog
else
  if [[ -z "$output_file" ]]; then
    output_file="$repo_root/CHANGELOG.md"
  fi
  render_changelog > "$output_file"
  echo "Wrote changelog to $output_file"
fi

