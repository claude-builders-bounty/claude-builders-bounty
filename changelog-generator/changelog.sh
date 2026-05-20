#!/usr/bin/env bash
# ============================================================
# changelog.sh — structured CHANGELOG from git history
#
# Usage:
#   ./changelog.sh                  # since last tag -> CHANGELOG.md
#   ./changelog.sh --all            # full history
#   ./changelog.sh v1.0.0..HEAD     # custom range
#   ./changelog.sh --output=RELEASE_NOTES.md
# ============================================================

set -euo pipefail

# --- defaults -------------------------------------------------
OUTPUT="${OUTPUT:-CHANGELOG.md}"
RANGE=""
INCLUDE_UNRELEASED=true

# --- colours (auto-detect tty) --------------------------------
if [ -t 1 ]; then
  C_RESET='\033[0m'
  C_BOLD='\033[1m'
  C_GREEN='\033[32m'
  C_CYAN='\033[36m'
else
  C_RESET='' C_BOLD='' C_GREEN='' C_CYAN=''
fi

# --- usage ----------------------------------------------------
usage() {
  cat <<EOF
Usage: changelog.sh [OPTIONS]

OPTIONS:
  --all               Include all commits, not just since last tag
  --range=<RANGE>     Custom git revision range (e.g. v1.0.0..HEAD)
  --output=<FILE>     Output file (default: CHANGELOG.md)
  --no-unreleased     Skip the "Unreleased" section
  -h, --help          Show this help

EXAMPLES:
  ./changelog.sh
  ./changelog.sh --all
  ./changelog.sh --range=v2.0.0..v3.0.0 --output=RELEASE_NOTES.md
EOF
  exit 0
}

# --- parse args -----------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)           RANGE="ALL"; shift ;;
    --range=*)       RANGE="${1#*=}"; shift ;;
    --range)         RANGE="$2"; shift 2 ;;
    --output=*)      OUTPUT="${1#*=}"; shift ;;
    --output)        OUTPUT="$2"; shift 2 ;;
    --no-unreleased) INCLUDE_UNRELEASED=false; shift ;;
    -h|--help)       usage ;;
    *)               echo "Unknown option: $1"; usage ;;
  esac
done

# --- determine range ------------------------------------------
if [ -z "$RANGE" ]; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [ -n "$LAST_TAG" ]; then
    RANGE="${LAST_TAG}..HEAD"
  else
    RANGE="ALL"
    echo -e "${C_CYAN}No tags found — using full history${C_RESET}" >&2
  fi
fi

if [ "$RANGE" = "ALL" ]; then
  COMMITS=$(git log --oneline --no-merges --format="%s (%h, %an)" 2>/dev/null || true)
else
  COMMITS=$(git log --oneline --no-merges --format="%s (%h, %an)" "$RANGE" 2>/dev/null || true)
fi

if [ -z "$COMMITS" ]; then
  echo -e "${C_GREEN}No commits to document — exiting${C_RESET}" >&2
  exit 0
fi

# --- categorisation helpers -----------------------------------
declare -A CATS
CATS_ORDER=("Added" "Fixed" "Changed" "Deprecated" "Removed" "Security" "Other")

cat_init() { for K in "${CATS_ORDER[@]}"; do CATS["$K"]=""; done; }
cat_append() { CATS["$1"]+="$2"$'\n'; }

categorise() {
  local line="$1"

  # --- conventional-commit prefixes (highest confidence) ------
  if echo "$line" | grep -qiE '^feat[\(:]';    then echo "Added";      return; fi
  if echo "$line" | grep -qiE '^fix[\(:]';     then echo "Fixed";      return; fi
  if echo "$line" | grep -qiE '^chore[\(:]';   then echo "Changed";    return; fi
  if echo "$line" | grep -qiE '^refactor[\(:]';then echo "Changed";    return; fi
  if echo "$line" | grep -qiE '^perf[\(:]';    then echo "Changed";    return; fi
  if echo "$line" | grep -qiE '^docs[\(:]';    then echo "Changed";    return; fi
  if echo "$line" | grep -qiE '^style[\(:]';   then echo "Changed";    return; fi
  if echo "$line" | grep -qiE '^test[\(:]';    then echo "Changed";    return; fi
  if echo "$line" | grep -qiE '^ci[\(:]';      then echo "Changed";    return; fi
  if echo "$line" | grep -qiE '^build[\(:]';   then echo "Changed";    return; fi
  if echo "$line" | grep -qiE '^revert[\(:]';  then echo "Removed";    return; fi
  if echo "$line" | grep -qiE '^security[\(:]';then echo "Security";   return; fi
  if echo "$line" | grep -qiE '^deprecate';    then echo "Deprecated"; return; fi

  # --- keyword heuristics (fallback) --------------------------
  local lower
  lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')

  if echo "$lower" | grep -qiE '\b(fix|bug|hotfix|patch|repair|resolve|correct)\b'; then echo "Fixed"; return; fi
  if echo "$lower" | grep -qiE '\b(remove|drop|delete|eliminate|revert|deprecat)\b'; then echo "Removed"; return; fi
  if echo "$lower" | grep -qiE '\b(add|new|introduce|implement|support|create|allow|initial)\b'; then echo "Added"; return; fi
  if echo "$lower" | grep -qiE '\b(secur|vuln|exploit|cve|auth|inject|csrf|xss)\b'; then echo "Security"; return; fi
  if echo "$lower" | grep -qiE '\b(deprecat|obsolete|sunset)\b'; then echo "Deprecated"; return; fi

  echo "Changed"
}

# --- formatting -----------------------------------------------
fmt_commit() {
  # Pretty-print a commit: keep first ~80 chars, append hash & author in small text
  local msg="$1"
  echo "$msg" | sed 's/^/- /'
}

# --- generate -------------------------------------------------
RANGE_LABEL="$RANGE"
[ "$RANGE" = "ALL" ] && RANGE_LABEL="full history"

DATE=$(date +%Y-%m-%d)
PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo 'project')")

cat_init

# Process each commit line
while IFS= read -r line; do
  [ -z "$line" ] && continue
  CAT=$(categorise "$line")
  cat_append "$CAT" "$(fmt_commit "$line")"
done <<< "$COMMITS"

# --- write output ---------------------------------------------
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to **$PROJECT** are documented in this file."
  echo "This file is auto-generated by \`changelog.sh\`."
  echo ""

  if $INCLUDE_UNRELEASED; then
    echo "## [Unreleased] — $DATE"
    echo ""
    echo "> Range: \`$RANGE_LABEL\`"
    echo ""
  fi

  printed_first=false
  for K in "${CATS_ORDER[@]}"; do
    content="${CATS[$K]}"
    if [ -n "$content" ]; then
      echo "### $K"
      echo ""
      echo "$content"
      printed_first=true
    fi
  done

  if ! $printed_first; then
    echo "_No categorized commits found._"
  fi

  echo ""
  echo "---"
  echo ""
  echo "📅 Generated on $DATE by [changelog.sh](./changelog.sh)"
} > "$OUTPUT"

# --- summary --------------------------------------------------
COUNT=$(echo "$COMMITS" | grep -c . || echo 0)
echo -e "${C_GREEN}✓ Wrote ${COUNT} commits to ${C_BOLD}${OUTPUT}${C_RESET}" >&2
for K in "${CATS_ORDER[@]}"; do
  c=$(echo "${CATS[$K]}" | grep -c '^- ' 2>/dev/null || echo 0)
  [ "$c" -gt 0 ] && echo -e "  ${C_CYAN}${K}${C_RESET}: ${c}" >&2
done
