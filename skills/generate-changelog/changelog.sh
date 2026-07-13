#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash changelog.sh [options]

Generate a structured CHANGELOG from commits since the latest reachable tag.

Options:
  --repo PATH       Git repository to inspect (default: current directory)
  --output PATH     Output file, or - for stdout (default: CHANGELOG.md)
  --since REV       Override the starting tag or revision
  --version LABEL   Section label (default: Unreleased)
  --force           Replace an existing output file
  -h, --help        Show this help
EOF
}

die() {
  printf 'generate-changelog: %s\n' "$*" >&2
  exit 1
}

repo=.
output=CHANGELOG.md
since=
version=Unreleased
force=false

while (($#)); do
  case "$1" in
    --repo|--output|--since|--version)
      (($# >= 2)) || die "$1 requires a value"
      option=$1
      value=$2
      shift 2
      case "$option" in
        --repo) repo=$value ;;
        --output) output=$value ;;
        --since) since=$value ;;
        --version) version=$value ;;
      esac
      ;;
    --force) force=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
done

git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  || die "not a git repository: $repo"
git -C "$repo" rev-parse --verify HEAD >/dev/null 2>&1 \
  || die "repository has no commits: $repo"

if [[ -n "$since" ]]; then
  git -C "$repo" rev-parse --verify "$since^{commit}" >/dev/null 2>&1 \
    || die "unknown revision: $since"
  base=$since
else
  base=$(git -C "$repo" describe --tags --abbrev=0 HEAD 2>/dev/null || true)
fi

if [[ -n "$base" ]]; then
  range="$base..HEAD"
  range_label=$base
else
  range=HEAD
  range_label='repository start'
fi

tmpdir=$(mktemp -d "${TMPDIR:-/tmp}/generate-changelog.XXXXXX")
trap 'rm -rf -- "$tmpdir"' EXIT HUP INT TERM
commits_file=$tmpdir/commits
for category in Added Fixed Changed Removed; do
  : >"$tmpdir/$category"
done

git -C "$repo" log --no-merges --reverse --format='%h%x09%s' "$range" >"$commits_file"

classify() {
  local subject=$1 type=
  local conventional_re='^([[:alpha:]]+)(\([^)]*\))?!?:[[:space:]]*(.*)$'
  local added_re='^(add|create|introduce|implement|new)([[:space:]:-]|$)'
  local fixed_re='^(fix|bugfix|hotfix|repair|correct)([[:space:]:-]|$)'
  local removed_re='^(remove|delete|drop|deprecate|revert)([[:space:]:-]|$)'
  shopt -s nocasematch
  if [[ "$subject" =~ $conventional_re ]]; then
    type=${BASH_REMATCH[1]}
    case "$type" in
      feat|feature|add|new) printf Added ;;
      fix|bug|bugfix|hotfix|patch) printf Fixed ;;
      remove|removed|delete|drop|deprecate|revert) printf Removed ;;
      *) printf Changed ;;
    esac
  elif [[ "$subject" =~ $added_re ]]; then
    printf Added
  elif [[ "$subject" =~ $fixed_re ]]; then
    printf Fixed
  elif [[ "$subject" =~ $removed_re ]]; then
    printf Removed
  else
    printf Changed
  fi
  shopt -u nocasematch
}

while IFS=$'\t' read -r short_sha subject || [[ -n "${short_sha:-}" ]]; do
  [[ -n "${short_sha:-}" ]] || continue
  category=$(classify "$subject")
  safe_subject=${subject//\\/\\\\}
  safe_subject=${safe_subject//\`/\\\`}
  printf -- '- %s (`%s`)\n' "$safe_subject" "$short_sha" >>"$tmpdir/$category"
done <"$commits_file"

commit_count=$(wc -l <"$commits_file" | tr -d '[:space:]')
head_date=$(git -C "$repo" show -s --format=%cs HEAD)
document=$tmpdir/CHANGELOG.md
{
  printf '# Changelog\n\n'
  printf 'All notable changes to this project will be documented in this file.\n\n'
  printf '## [%s] - %s\n\n' "$version" "$head_date"
  for category in Added Fixed Changed Removed; do
    printf '### %s\n\n' "$category"
    if [[ -s "$tmpdir/$category" ]]; then
      cat "$tmpdir/$category"
    else
      printf '_No changes._\n'
    fi
    printf '\n'
  done
  printf '<!-- Generated from %s..HEAD; %s commit(s). -->\n' "$range_label" "$commit_count"
} >"$document"

if [[ "$output" == - ]]; then
  cat "$document"
else
  case "$output" in
    /*) output_path=$output ;;
    *) output_path=$repo/$output ;;
  esac
  output_dir=$(dirname -- "$output_path")
  mkdir -p -- "$output_dir"
  [[ ! -d "$output_path" ]] || die "output path is a directory: $output_path"
  if [[ -e "$output_path" && "$force" != true ]]; then
    die "output already exists (use --force to replace it): $output_path"
  fi
  staged=$(mktemp "$output_dir/.CHANGELOG.XXXXXX")
  cp -- "$document" "$staged"
  mv -f -- "$staged" "$output_path"
  printf 'Generated %s from %s commit(s) since %s.\n' "$output_path" "$commit_count" "$range_label"
fi
