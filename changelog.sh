#!/usr/bin/env bash
set -euo pipefail

SINCE="${2:-$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")}"

if [ -z "$SINCE" ]; then
  echo "Error: no tag found. Use --since <ref>"
  exit 1
fi

CATEGORIES=("Added" "Fixed" "Changed" "Removed")
OUTPUT="CHANGELOG.md"

{
  echo "# Changelog"
  echo
  DATE=$(date +%F)
  echo "_Generated on $DATE since \`$SINCE\`_"
  echo
  for cat in "${CATEGORIES[@]}"; do
    PATTERN=""
    case "$cat" in
      Added)   PATTERN="^[Aa]dd|^[Ff]eat|^[Ii]mplement|^[Ii]ntroduce|^[Nn]ew|^[Cc]reate" ;;
      Fixed)   PATTERN="^[Ff]ix|^[Bb]ug|^[Cc]orrect|^[Pp]atch|^[Rr]esolve|^[Hh]otfix" ;;
      Changed) PATTERN="^[Rr]efactor|^[Uu]pdate|^[Mm]odify|^[Ii]mprove|^[Mm]igrate|^[Rr]ework|^[Cc]hange|^[Rr]eplace" ;;
      Removed) PATTERN="^[Rr]emove|^[Dd]elete|^[Dd]rop|^[Cc]lean|^[Dd]eprecat" ;;
    esac
    COMMITS=$(git log "$SINCE"..HEAD --oneline --format="%s (%h)" 2>/dev/null | grep -iE "$PATTERN" || true)
    if [ -n "$COMMITS" ]; then
      echo "## $cat"
      echo
      echo "$COMMITS" | while IFS= read -r line; do echo "- $line"; done
      echo
    fi
  done
} > "$OUTPUT"

echo "Generated $OUTPUT since $SINCE"
