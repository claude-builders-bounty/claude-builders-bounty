#!/usr/bin/env bash
set -euo pipefail

repo="${1:-.}"
out="${2:-CHANGELOG.md}"

cd "$repo"

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
range="HEAD"
if [[ -n "${latest_tag}" ]]; then
  range="${latest_tag}..HEAD"
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

git log --no-merges --reverse --pretty=format:'%h%x09%s' $range > "$tmp" || true

section() {
  local title="$1"
  local key="$2"
  awk -F '\t' -v k="$key" '
    BEGIN { found=0 }
    {
      subj=$2
      low=tolower(subj)
      if (k=="Added" && low ~ /^(feat|feature)(\(.+\))?: /) { print "- " subj " (" $1 ")"; found=1 }
      else if (k=="Fixed" && low ~ /^fix(\(.+\))?: /) { print "- " subj " (" $1 ")"; found=1 }
      else if (k=="Removed" && (low ~ /^remove(\(.+\))?: / || low ~ /^revert: / || low ~ /^breaking(\(.+\))?: /)) { print "- " subj " (" $1 ")"; found=1 }
      else if (k=="Changed" && low ~ /^(docs|refactor|style|perf|build|ci|test|chore)(\(.+\))?: /) { print "- " subj " (" $1 ")"; found=1 }
    }
    END { exit(found?0:1) }
  ' "$tmp" > /tmp/changelog-section.$$ 2>/dev/null || true
  if [[ -s /tmp/changelog-section.$$ ]]; then
    printf '### %s\n' "$title"
    cat /tmp/changelog-section.$$
    printf '\n'
  fi
  rm -f /tmp/changelog-section.$$
}

{
  printf '# Changelog\n\n'
  if [[ -n "${latest_tag}" ]]; then
    printf '## [Unreleased]\n\n'
  else
    printf '## [Initial]\n\n'
  fi
  section Added Added
  section Fixed Fixed
  section Changed Changed
  section Removed Removed
} > "$out"

echo "Wrote $out"
