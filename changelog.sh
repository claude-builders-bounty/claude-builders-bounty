#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh              # output to CHANGELOG.md
#   bash changelog.sh --preview    # print to stdout
#   bash changelog.sh --since v1.0.0  # specify a starting tag
#
set -euo pipefail

# ── Config ──────────────────────────────────────────────────────────
OUTPUT_FILE="CHANGELOG.md"
SINCE_ARG=""

# ── Parse args ──────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --preview) OUTPUT_FILE="" ;;
    --since)   shift; SINCE_ARG="$1" ;;
    *)         echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

# ── Determine tag range ─────────────────────────────────────────────
if [[ -z "$SINCE_ARG" ]]; then
  # Find the most recent tag, or use initial commit
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -z "$LAST_TAG" ]]; then
    SINCE_ARG=$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
  else
    SINCE_ARG="$LAST_TAG"
  fi
fi

if [[ -z "$SINCE_ARG" ]]; then
  echo "❌ No commits found in this repository."
  exit 1
fi

# ── Collect commits since last tag ──────────────────────────────────
COMMITS=$(git log "$SINCE_ARG"..HEAD --format="%s|||%h|||%an|||%ai" 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
  echo "ℹ️  No new commits since $SINCE_ARG. Nothing to generate."
  exit 0
fi

# ── Categorise commits ──────────────────────────────────────────────
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  msg="${line%%|||*}"
  rest="${line#*|||}"
  hash="${rest%%|||*}"
  rest="${rest#*|||}"
  author="${rest%%|||*}"
  date="${rest#*|||}"

  entry="- ${msg} ([${hash}](https://github.com/FAKE/REPO/commit/${hash}))"

  # Conventional commit parsing
  lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
  if [[ "$lower_msg" == feat* ]] || [[ "$lower_msg" == feature* ]] || [[ "$lower_msg" == add* ]]; then
    ADDED+=("$entry")
  elif [[ "$lower_msg" == fix* ]] || [[ "$lower_msg" == bug* ]] || [[ "$lower_msg" == hotfix* ]]; then
    FIXED+=("$entry")
  elif [[ "$lower_msg" == chore* ]] || [[ "$lower_msg" == refactor* ]] || [[ "$lower_msg" == update* ]] || [[ "$lower_msg" == perf* ]]; then
    CHANGED+=("$entry")
  elif [[ "$lower_msg" == remove* ]] || [[ "$lower_msg" == delete* ]] || [[ "$lower_msg" == deprecat* ]]; then
    REMOVED+=("$entry")
  else
    OTHER+=("$entry")
  fi
done <<< "$COMMITS"

# ── Build markdown ──────────────────────────────────────────────────
NEW_TAG=$(date +%Y.%m.%d)
DATE_NOW=$(date +%Y-%m-%d)

CONTENT="# Changelog\n\n"
CONTENT+="## [${NEW_TAG}] - ${DATE_NOW}\n"
CONTENT+="\n"
CONTENT+="_Generated from $(echo "$COMMITS" | wc -l | tr -d ' ') commits since ${SINCE_ARG}._\n\n"

write_section() {
  local heading="$1" emoji="$2"
  shift 2
  local items=("$@")
  if [[ ${#items[@]} -gt 0 ]]; then
    CONTENT+="### ${emoji} ${heading}\n\n"
    for item in "${items[@]}"; do
      CONTENT+="${item}\n"
    done
    CONTENT+="\n"
  fi
}

# Convert arrays from indexed to split form
ADDED_LIST=("${ADDED[@]}")
FIXED_LIST=("${FIXED[@]}")
CHANGED_LIST=("${CHANGED[@]}")
REMOVED_LIST=("${REMOVED[@]}")
OTHER_LIST=("${OTHER[@]}")

write_section "Added" "✨" "${ADDED_LIST[@]}"
write_section "Fixed" "🐛" "${FIXED_LIST[@]}"
write_section "Changed" "🔄" "${CHANGED_LIST[@]}"
write_section "Removed" "🗑️" "${REMOVED_LIST[@]}"
write_section "Other" "📦" "${OTHER_LIST[@]}"

# ── Output ──────────────────────────────────────────────────────────
if [[ -z "$OUTPUT_FILE" ]]; then
  echo -e "$CONTENT"
else
  echo -e "$CONTENT" > "$OUTPUT_FILE"
  echo "✅ Generated $(pwd)/$OUTPUT_FILE"
fi
