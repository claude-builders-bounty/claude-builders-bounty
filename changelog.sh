#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="${1:-CHANGELOG.md}"
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || printf 'none')"
RANGE=""
TITLE="Initial history"
if [ "$LAST_TAG" != "none" ]; then
  RANGE="$LAST_TAG..HEAD"
  TITLE="$LAST_TAG...HEAD"
fi

add=()
fix=()
change=()
remove=()

if [ -z "$RANGE" ]; then
  LOG_CMD=(git log --pretty=format:'%h	%s')
else
  LOG_CMD=(git log --pretty=format:'%h	%s' "$RANGE")
fi

while IFS=$'\t' read -r hash msg; do
  lower="$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')"

  if printf '%s' "$lower" | grep -Eq '(\bfeat\b|\bfeature\b|\badd\b|\badded\b)'; then
    add+=("- \`$msg\`")
  elif printf '%s' "$lower" | grep -Eq '(\bfix\b|\bpatched\b|\bbug\b)'; then
    fix+=("- \`$msg\`")
  elif printf '%s' "$lower" | grep -Eq '(\bremove\b|\bremoved\b|\bdeleted\b|\bdelete\b|\bdrop\b|\bdeprec\b)'; then
    remove+=("- \`$msg\`")
  elif printf '%s' "$lower" | grep -Eq '(\brefactor\b|\bchange\b|\bupdated\b|\bupgrade\b)'; then
    change+=("- \`$msg\`")
  else
    change+=("- \`$msg\`")
  fi

done < <("${LOG_CMD[@]}")

{
  echo "# Changelog"
  echo
  echo "## Unreleased"
  echo
  echo "### Added"
  if (( ${#add[@]} )); then
    printf '%s\n' "${add[@]}"
  else
    echo "- No added items in this release"
  fi
  echo
  echo "### Fixed"
  if (( ${#fix[@]} )); then
    printf '%s\n' "${fix[@]}"
  else
    echo "- No fixed items in this release"
  fi
  echo
  echo "### Changed"
  if (( ${#change[@]} )); then
    printf '%s\n' "${change[@]}"
  else
    echo "- No changed items in this release"
  fi
  echo
  echo "### Removed"
  if (( ${#remove[@]} )); then
    printf '%s\n' "${remove[@]}"
  else
    echo "- No removed items in this release"
  fi
} > "$OUT_FILE"

echo "Generated $OUT_FILE from $TITLE"
