#!/usr/bin/env bash
# Generate CHANGELOG section from commits since last tag (or last 50 commits).
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  RANGE="$(git describe --tags --abbrev=0)..HEAD"
else
  RANGE="HEAD~50..HEAD"
fi
TMP="$(mktemp)"
git log --no-merges --pretty=format:'%s' "$RANGE" > "$TMP" || true
added=""; fixed=""; changed=""; removed=""; other=""
while IFS= read -r line; do
  low="$(echo "$line" | tr '[:upper:]' '[:lower:]')"
  case "$low" in
    add*|feat*|feature*) added+="- $line"$'\n' ;;
    fix*|bug*) fixed+="- $line"$'\n' ;;
    change*|refactor*|update*|improve*) changed+="- $line"$'\n' ;;
    remove*|delete*|drop*) removed+="- $line"$'\n' ;;
    *) other+="- $line"$'\n' ;;
  esac
done < "$TMP"
rm -f "$TMP"
{
  echo "## Unreleased"
  echo
  echo "### Added"; echo "${added:-(none)}"; echo
  echo "### Fixed"; echo "${fixed:-(none)}"; echo
  echo "### Changed"; echo "${changed:-(none)}"; echo
  echo "### Removed"; echo "${removed:-(none)}"
  if [[ -n "$other" ]]; then echo; echo "### Other"; echo "$other"; fi
} 
