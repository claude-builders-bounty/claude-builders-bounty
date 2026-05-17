#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [repo_path] [output_file]
# Accepts 0-2 positional args; falls back to current dir and CHANGELOG.md.

set -euo pipefail
REPO="${1:-.}"
OUTPUT="${2:-CHANGELOG.md}"

cd "$REPO"

# Get last tag; fall back to first commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
echo "📦 Generating changelog from $LAST_TAG to HEAD..."

# Header
{
  echo "# Changelog"
  echo ""
  echo "## $(git tag --sort=-creatordate | head -1 || echo 'Unreleased') ($(date +%Y-%m-%d))"
  echo ""
} > "$OUTPUT"

declare -A SECTIONS
SECTIONS=(["Added"]="" ["Fixed"]="" ["Changed"]="" ["Removed"]="")

while IFS= read -r line; do
  msg="${line#* }"
  # Skip merge commits and empty messages
  [[ "$msg" == "Merge "* ]] && continue
  [[ -z "$msg" ]] && continue

  if   [[ "$msg" =~ ^([Ff]eat|[Aa]dd) ]]; then
    SECTIONS["Added"]+="  - ${msg#*: }"$'\n'
  elif [[ "$msg" =~ ^([Ff]ix|[Bb]ug|[Hh]otfix) ]]; then
    SECTIONS["Fixed"]+="  - ${msg#*: }"$'\n'
  elif [[ "$msg" =~ ^([Rr]emove|[Dd]elete|[Dd]rop) ]]; then
    SECTIONS["Removed"]+="  - ${msg#*: }"$'\n'
  else
    SECTIONS["Changed"]+="  - $msg"$'\n'
  fi
done < <(git log "${LAST_TAG}..HEAD" --oneline --no-merges 2>/dev/null || echo "")

for section in Added Fixed Changed Removed; do
  content="${SECTIONS[$section]}"
  if [[ -n "$content" ]]; then
    {
      echo "### $section"
      echo "$content"
    } >> "$OUTPUT"
  fi
done

echo "✅ Changelog written to $OUTPUT ($(wc -l < "$OUTPUT") lines)"
