#!/usr/bin/env bash
# Build a CHANGELOG.md from commits after the latest git tag.
# Usage: changelog.sh [repo-dir]
# Categories come from the commit subject prefix: feat, fix, refactor, remove.
set -euo pipefail
root="${1:-.}"
cd "$root"
git rev-parse --is-inside-work-tree >/dev/null

tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$tag" ]; then
  range="${tag}..HEAD"
  since="since ${tag}"
else
  range="HEAD"
  since="since the start of the repository"
fi

added="" fixed="" changed="" removed="" other=""
while IFS= read -r line; do
  [ -z "$line" ] && continue
  hash="${line%% *}"
  subject="${line#* }"
  prefix="${subject%%:*}"
  prefix="$(printf '%s' "$prefix" | tr '[:upper:]' '[:lower:]')"
  item="- ${subject} (${hash})"
  case "$prefix" in
    feat|add|added) added="${added}${item}"$'\n' ;;
    fix|fixed) fixed="${fixed}${item}"$'\n' ;;
    refactor|change|changed|chore|perf) changed="${changed}${item}"$'\n' ;;
    remove|removed|revert) removed="${removed}${item}"$'\n' ;;
    *) other="${other}${item}"$'\n' ;;
  esac
done < <(git log --reverse --pretty=format:'%h %s' $range; echo)

out="CHANGELOG.md"
{
  echo "# Changelog"
  echo
  echo "Generated ${since}."
  echo
  for name in Added Fixed Changed Removed Other; do
    case "$name" in
      Added) block="${added-}" ;;
      Fixed) block="${fixed-}" ;;
      Changed) block="${changed-}" ;;
      Removed) block="${removed-}" ;;
      Other) block="${other-}" ;;
    esac
    [ -z "$block" ] && continue
    echo "## ${name}"
    echo
    printf '%s' "$block"
    echo
  done
} > "$out"
echo "wrote ${root}/${out} range=${range}"
