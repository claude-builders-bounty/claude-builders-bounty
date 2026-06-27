#!/usr/bin/env bash
# Auto-generated for bounty: structured CHANGELOG from git history
set -euo pipefail
OUT="${1:-CHANGELOG.md}"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
RANGE=""
if [ -n "$LAST_TAG" ]; then
  RANGE="$LAST_TAG..HEAD"
  echo "# Changelog since $LAST_TAG" > "$OUT"
else
  RANGE="HEAD"
  echo "# Changelog" > "$OUT"
fi
echo "" >> "$OUT"

declare -A sections
sections[Added]=
sections[Fixed]=
sections[Changed]=
sections[Removed]=

while IFS= read -r line; do
  msg=$(echo "$line" | cut -d' ' -f2-)
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
  if echo "$lower" | grep -qE '^fix|bug|patch'; then key=Fixed
  elif echo "$lower" | grep -qE '^remove|delete|drop'; then key=Removed
  elif echo "$lower" | grep -qE '^change|update|refactor|chore'; then key=Changed
  else key=Added
  fi
  sections[$key]+="- $msg\n"
done < <(git log $RANGE --pretty=format:%s 2>/dev/null | head -200)

for key in Added Fixed Changed Removed; do
  if [ -n "${sections[$key]}" ]; then
    echo "## $key" >> "$OUT"
    echo -e "${sections[$key]}" >> "$OUT"
    echo "" >> "$OUT"
  fi
done
echo "Wrote $OUT"
