#!/usr/bin/env bash
set -euo pipefail

out="${1:-CHANGELOG.md}"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${repo_root}" ]]; then
  echo "error: run inside a git repo" >&2
  exit 1
fi

cd "$repo_root"

last_tag=""
if last_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  range="${last_tag}..HEAD"
else
  range="HEAD"
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

{
  echo "# Changelog"
  echo
  if [[ -n "${last_tag}" ]]; then
    echo "Generated from commits since \`${last_tag}\`."
  else
    echo "Generated from the full git history."
  fi
  echo
  echo "## Added"
  echo
  echo "## Fixed"
  echo
  echo "## Changed"
  echo
  echo "## Removed"
  echo
} >"$tmp"

declare -A bullets=(
  [Added]=""
  [Fixed]=""
  [Changed]=""
  [Removed]=""
)

while IFS=$'\t' read -r subject hash; do
  [[ -z "${subject}" ]] && continue
  lower="${subject,,}"
  section="Changed"

  case "$lower" in
    feat*|add*|build\(*|new* )
      section="Added"
      ;;
    fix*|bug*|hotfix*|patch* )
      section="Fixed"
      ;;
    remove*|deleted*|delete*|deprecate* )
      section="Removed"
      ;;
    refactor*|docs*|doc*|chore*|ci*|style*|test*|perf*|revert* )
      section="Changed"
      ;;
  esac

  bullets["$section"]+="- ${subject} (\`${hash}\`)\n"
done < <(git log --no-merges --pretty=format:'%s%x09%h' "$range")

{
  echo "# Changelog"
  echo
  if [[ -n "${last_tag}" ]]; then
    echo "Generated from commits since \`${last_tag}\`."
  else
    echo "Generated from the full git history."
  fi
  echo

  for section in Added Fixed Changed Removed; do
    echo "## ${section}"
    echo
    if [[ -n "${bullets[$section]}" ]]; then
      printf '%b' "${bullets[$section]}"
    else
      echo "_No ${section,,} commits found._"
    fi
    echo
  done
} >"$out"

echo "Wrote ${out}"
