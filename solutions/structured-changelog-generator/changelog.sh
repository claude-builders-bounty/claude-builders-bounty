#!/usr/bin/env bash
set -euo pipefail

OUTPUT=CHANGELOG.md
FROM_TAG=
TO_REF=HEAD
STDOUT=false

usage() {
  cat <<'EOF'
Usage: bash changelog.sh [options]

Generate a Keep a Changelog-style document from Git commits.

Options:
  --from TAG       Start after TAG (default: latest reachable tag)
  --to REF         End at REF (default: HEAD)
  --output FILE    Write to FILE (default: CHANGELOG.md)
  --stdout         Print without writing a file
  -h, --help       Show this help
EOF
}

while (($#)); do
  case $1 in
    --from) FROM_TAG=${2:?missing tag}; shift 2 ;;
    --to) TO_REF=${2:?missing ref}; shift 2 ;;
    --output) OUTPUT=${2:?missing file}; shift 2 ;;
    --stdout) STDOUT=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo 'Run this command inside a Git repository.' >&2; exit 1; }
git rev-parse --verify "$TO_REF^{commit}" >/dev/null 2>&1 || { echo "Unknown Git ref: $TO_REF" >&2; exit 1; }

if [[ -z $FROM_TAG ]]; then
  FROM_TAG=$(git describe --tags --abbrev=0 "$TO_REF" 2>/dev/null || true)
fi
if [[ -n $FROM_TAG ]]; then
  git rev-parse --verify "$FROM_TAG^{commit}" >/dev/null 2>&1 || { echo "Unknown Git tag/ref: $FROM_TAG" >&2; exit 1; }
  RANGE="$FROM_TAG..$TO_REF"
else
  RANGE=$TO_REF
fi

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
for section in Added Fixed Changed Removed; do : >"$TMP/$section"; done

count=0
while IFS=$'\x1f' read -r hash subject body; do
  [[ -n ${subject:-} ]] || continue
  lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')
  combined=$(printf '%s\n%s' "$subject" "${body:-}")
  breaking_re='^[a-zA-Z]+(\([^)]*\))?!:'
  if [[ $combined =~ BREAKING[[:space:]]CHANGE ]] || [[ $subject =~ $breaking_re ]]; then
    section=Changed
    subject="BREAKING: $subject"
  elif [[ $lower =~ ^(remove|removed|delete|deleted|deprecate|deprecated)(\(|:|[[:space:]]) ]]; then
    section=Removed
  elif [[ $lower =~ ^(fix|fixed|bugfix|hotfix)(\(|:|[[:space:]]) ]]; then
    section=Fixed
  elif [[ $lower =~ ^(feat|feature|add|added|new)(\(|:|[[:space:]]) ]]; then
    section=Added
  else
    section=Changed
  fi
  clean=${subject//$'\n'/ }
  printf -- '- %s (`%s`)\n' "$clean" "$hash" >>"$TMP/$section"
  count=$((count + 1))
done < <(git log --reverse --no-merges --format='%h%x1f%s%x1f%b' "$RANGE")

((count > 0)) || { echo "No non-merge commits found in range $RANGE" >&2; exit 1; }

DOCUMENT=$TMP/document
{
  printf '# Changelog\n\n'
  printf 'All notable changes to this project are documented in this file.\n\n'
  printf 'The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).\n\n'
  printf '## [Unreleased] - %s\n' "$(date -u +%Y-%m-%d)"
  if [[ -n $FROM_TAG ]]; then printf '\nCommits after `%s` through `%s`.\n' "$FROM_TAG" "$TO_REF"; fi
  for section in Added Fixed Changed Removed; do
    if [[ -s $TMP/$section ]]; then
      printf '\n### %s\n\n' "$section"
      cat "$TMP/$section"
    fi
  done
} >"$DOCUMENT"

if $STDOUT; then
  cat "$DOCUMENT"
else
  mkdir -p "$(dirname "$OUTPUT")"
  cp "$DOCUMENT" "$OUTPUT"
  printf 'Generated %s from %d commits (%s).\n' "$OUTPUT" "$count" "$RANGE"
fi
