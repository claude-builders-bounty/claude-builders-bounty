#!/usr/bin/env bash
# Generate/update CHANGELOG.md from git commits since the last tag.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "${LAST_TAG}" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  RANGE_LABEL="${LAST_TAG}..HEAD"
else
  RANGE="HEAD"
  RANGE_LABEL="all history"
fi

SHORT_SHA="$(git rev-parse --short HEAD)"
DATE="$(git log -1 --format=%cs 2>/dev/null || date +%F)"

added=()
fixed=()
changed=()
removed=()

while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue
  [[ "$subject" =~ ^Merge\  ]] && continue

  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  if [[ "$lower" =~ (^|[^a-z])(feat|add|added|new)([^a-z]|$) ]]; then
    added+=("- ${subject}")
  elif [[ "$lower" =~ (^|[^a-z])(fix|fixed|bug|patch)([^a-z]|$) ]]; then
    fixed+=("- ${subject}")
  elif [[ "$lower" =~ (^|[^a-z])(remove|removed|delete|deleted|drop|dropped|deprecat)([^a-z]|$) ]]; then
    removed+=("- ${subject}")
  else
    changed+=("- ${subject}")
  fi
done < <(git log ${RANGE} --pretty=format:'%s')

NEW_SECTION="$(mktemp)"
REST="$(mktemp)"
trap 'rm -f "$NEW_SECTION" "$REST"' EXIT

{
  echo "## [Unreleased] — ${SHORT_SHA} (${DATE})"
  echo
  echo "_Range: ${RANGE_LABEL}_"
  echo
  if ((${#added[@]})); then
    echo "### Added"
    printf '%s\n' "${added[@]}"
    echo
  fi
  if ((${#fixed[@]})); then
    echo "### Fixed"
    printf '%s\n' "${fixed[@]}"
    echo
  fi
  if ((${#changed[@]})); then
    echo "### Changed"
    printf '%s\n' "${changed[@]}"
    echo
  fi
  if ((${#removed[@]})); then
    echo "### Removed"
    printf '%s\n' "${removed[@]}"
    echo
  fi
  if ((${#added[@]} + ${#fixed[@]} + ${#changed[@]} + ${#removed[@]} == 0)); then
    echo "_No commits in range._"
    echo
  fi
} > "$NEW_SECTION"

TITLE="# Changelog"$'\n'
if [[ -f CHANGELOG.md ]]; then
  # Keep everything after the previous Unreleased heading
  awk '
    BEGIN { skip=0 }
    /^## \[Unreleased\]/ { skip=1; next }
    skip==1 && /^## / { skip=0 }
    skip==0 { print }
  ' CHANGELOG.md > "$REST"
else
  : > "$REST"
fi

{
  printf '%s\n\n' "$TITLE"
  cat "$NEW_SECTION"
  # avoid double blank at junction
  if [[ -s "$REST" ]]; then
    echo
    cat "$REST"
  fi
} > CHANGELOG.md

echo "Wrote CHANGELOG.md (${RANGE_LABEL})"
echo "  Added=${#added[@]} Fixed=${#fixed[@]} Changed=${#changed[@]} Removed=${#removed[@]}"
