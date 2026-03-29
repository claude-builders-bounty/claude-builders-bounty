#!/usr/bin/env bash
# changelog.sh - Generate a structured CHANGELOG.md from git history
#
# Usage: bash changelog.sh [OPTIONS]
#
# Options:
#   --output, -o PATH   Output file path (default: CHANGELOG.md)
#   --since TAG|HASH    Start from a specific tag or commit (default: last tag)
#   --version LABEL     Override version label (default: auto-increment)
#   --dry-run           Print to stdout without writing
#   --append            Prepend new section to existing CHANGELOG
#   --no-color          Disable colored output
#   --repo PATH         Path to git repository (default: current dir)
#   --help, -h          Show this help
#
set -euo pipefail

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
USE_COLOR=auto

setup_colors() {
  if [[ "$USE_COLOR" == "auto" ]]; then
    [[ -t 2 ]] && USE_COLOR=yes || USE_COLOR=no
  fi
  if [[ "$USE_COLOR" == "yes" ]]; then
    BOLD='\033[1m' DIM='\033[2m' RESET='\033[0m'
    GREEN='\033[32m' BLUE='\033[34m' YELLOW='\033[33m' RED='\033[31m' CYAN='\033[36m'
  else
    BOLD='' DIM='' RESET='' GREEN='' BLUE='' YELLOW='' RED='' CYAN=''
  fi
}

info()    { echo -e "${BLUE}info${RESET} $*" >&2; }
ok()      { echo -e "${GREEN}done${RESET} $*" >&2; }
warn()    { echo -e "${YELLOW}warn${RESET} $*" >&2; }
die()     { echo -e "${RED}error${RESET} $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
OUTPUT="CHANGELOG.md"
SINCE=""
VERSION=""
DRY_RUN=false
APPEND=false
REPO_PATH="."

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output|-o)  OUTPUT="$2";    shift 2 ;;
    --since)      SINCE="$2";     shift 2 ;;
    --version)    VERSION="$2";   shift 2 ;;
    --dry-run)    DRY_RUN=true;   shift ;;
    --append)     APPEND=true;    shift ;;
    --no-color)   USE_COLOR=no;   shift ;;
    --repo)       REPO_PATH="$2"; shift 2 ;;
    --help|-h)
      awk '/^#!/{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"
      exit 0 ;;
    *) die "Unknown option: $1 (use --help for usage)" ;;
  esac
done

setup_colors

# ---------------------------------------------------------------------------
# Validate git repository
# ---------------------------------------------------------------------------
if ! git -C "$REPO_PATH" rev-parse --is-inside-work-tree &>/dev/null; then
  die "Not inside a git repository: $REPO_PATH"
fi

REPO_ROOT=$(git -C "$REPO_PATH" rev-parse --show-toplevel)

# ---------------------------------------------------------------------------
# Determine commit range
# ---------------------------------------------------------------------------
DATE_FILTER=""

if [[ -n "$SINCE" ]]; then
  if git -C "$REPO_ROOT" rev-parse --verify "$SINCE^{commit}" &>/dev/null 2>&1; then
    RANGE="${SINCE}..HEAD"
    RANGE_LABEL="since $SINCE"
  elif git -C "$REPO_ROOT" rev-parse --verify "$SINCE" &>/dev/null 2>&1; then
    RANGE="${SINCE}..HEAD"
    RANGE_LABEL="since $SINCE"
  else
    RANGE="HEAD"
    DATE_FILTER="--since=${SINCE}"
    RANGE_LABEL="since $SINCE"
  fi
else
  LAST_TAG=$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -n "$LAST_TAG" ]]; then
    RANGE="${LAST_TAG}..HEAD"
    RANGE_LABEL="since tag ${LAST_TAG}"
  else
    RANGE=""
    RANGE_LABEL="all commits (no tags found)"
    warn "No git tags found -- using entire commit history."
  fi
fi

# ---------------------------------------------------------------------------
# Resolve version label
# ---------------------------------------------------------------------------
if [[ -z "$VERSION" ]]; then
  EXISTING_TAG=$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -n "$EXISTING_TAG" && "$EXISTING_TAG" =~ ^v?([0-9]+)\.([0-9]+)\.([0-9]+)(.*)$ ]]; then
    PREFIX=""
    [[ "$EXISTING_TAG" == v* ]] && PREFIX="v"
    MAJOR="${BASH_REMATCH[1]}"
    MINOR="${BASH_REMATCH[2]}"
    PATCH="${BASH_REMATCH[3]}"
    VERSION="${PREFIX}${MAJOR}.${MINOR}.$((PATCH + 1))"
  else
    VERSION="Unreleased"
  fi
fi

# ---------------------------------------------------------------------------
# Fetch commits
# ---------------------------------------------------------------------------
info "Collecting commits ($RANGE_LABEL)..."

GIT_LOG_ARGS=(git -C "$REPO_ROOT" log --no-merges --pretty=format:"%H|%s|%an")
if [[ -n "$RANGE" ]]; then
  GIT_LOG_ARGS+=("$RANGE")
fi
if [[ -n "$DATE_FILTER" ]]; then
  GIT_LOG_ARGS+=("$DATE_FILTER")
fi

mapfile -t RAW < <("${GIT_LOG_ARGS[@]}" 2>/dev/null || true)

TOTAL=${#RAW[@]}
# Filter empty lines
COMMITS=()
for line in "${RAW[@]}"; do
  [[ -n "$line" ]] && COMMITS+=("$line")
done
TOTAL=${#COMMITS[@]}

if [[ "$TOTAL" -eq 0 ]]; then
  warn "No commits found for the given range."
  if $DRY_RUN; then
    echo "# Changelog"
    echo ""
    echo "No changes."
    exit 0
  fi
fi

info "Found $TOTAL commit(s) to categorize."

# ---------------------------------------------------------------------------
# Categorize commits
# ---------------------------------------------------------------------------
declare -a CAT_ADDED=() CAT_FIXED=() CAT_CHANGED=() CAT_REMOVED=() CAT_OTHER=()

categorize() {
  local hash="$1" subject="$2" author="$3"
  local short="${hash:0:7}"

  # Strip the conventional commit prefix for the display message
  local clean_subject="$subject"
  # Use variable for regex to avoid bash parsing issues with parens
  local prefix_re='^[a-zA-Z]+(\([^)]*\))?: (.+)$'
  if [[ "$subject" =~ $prefix_re ]]; then
    clean_subject="${BASH_REMATCH[2]}"
    # Capitalize first letter
    clean_subject="$(echo "${clean_subject:0:1}" | tr '[:lower:]' '[:upper:]')${clean_subject:1}"
  fi

  local entry="- ${clean_subject} (\`${short}\`) -- *${author}*"

  local lower
  lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  # --- Primary: conventional commit prefix detection ---
  # Store regex patterns in variables to avoid bash parsing issues with parens/brackets
  local re_added='^(feat|feature|add|new)[:([:space:]]'
  local re_fixed='^(fix|bug|bugfix|hotfix|patch)[:([:space:]]'
  local re_removed='^(remove|delete|drop|deprecate)[:([:space:]]'
  local re_changed='^(refactor|perf|chore|build|ci|style|docs|test|update|bump|revert|change)[:([:space:]]'

  if   [[ "$lower" =~ $re_added ]];   then CAT_ADDED+=("$entry")
  elif [[ "$lower" =~ $re_fixed ]];   then CAT_FIXED+=("$entry")
  elif [[ "$lower" =~ $re_removed ]]; then CAT_REMOVED+=("$entry")
  elif [[ "$lower" =~ $re_changed ]]; then CAT_CHANGED+=("$entry")
  # --- Fallback: keyword scan in subject ---
  elif [[ "$lower" == *"add"* || "$lower" == *"implement"* || "$lower" == *"introduc"* ]]; then CAT_ADDED+=("$entry")
  elif [[ "$lower" == *"fix"* || "$lower" == *"resolv"* || "$lower" == *"correct"* || "$lower" == *"repair"* ]]; then CAT_FIXED+=("$entry")
  elif [[ "$lower" == *"remov"* || "$lower" == *"delet"* || "$lower" == *"drop"* || "$lower" == *"deprecat"* ]]; then CAT_REMOVED+=("$entry")
  elif [[ "$lower" == *"chang"* || "$lower" == *"updat"* || "$lower" == *"refactor"* || "$lower" == *"improv"* || "$lower" == *"optimiz"* || "$lower" == *"revert"* || "$lower" == *"migrat"* ]]; then CAT_CHANGED+=("$entry")
  else
    CAT_OTHER+=("$entry")
  fi
}

for line in "${COMMITS[@]}"; do
  IFS='|' read -r hash subject author <<< "$line"
  [[ -z "$hash" ]] && continue
  categorize "$hash" "$subject" "$author"
done

# ---------------------------------------------------------------------------
# Build CHANGELOG content
# ---------------------------------------------------------------------------
TODAY=$(date +%Y-%m-%d)

build_section() {
  local title="$1"; shift
  local -a items=("$@")
  if [[ ${#items[@]} -gt 0 ]]; then
    echo "### ${title}"
    echo ""
    for item in "${items[@]}"; do
      echo "$item"
    done
  fi
}

HEADER="# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

"

SECTION="## [${VERSION}] - ${TODAY}

> ${TOTAL} commit(s) ${RANGE_LABEL}

"

# Build sections
BODY=""
for cat_name in "Added:CAT_ADDED" "Fixed:CAT_FIXED" "Changed:CAT_CHANGED" "Removed:CAT_REMOVED" "Other:CAT_OTHER"; do
  IFS=':' read -r label varname <<< "$cat_name"
  declare -n arr="$varname"
  if [[ ${#arr[@]} -gt 0 ]]; then
    BODY+="$(build_section "$label" "${arr[@]}")"$'\n\n'
  fi
done

FOOTER="---
_Generated by [changelog.sh](https://github.com/claude-builders-bounty/claude-builders-bounty) on ${TODAY}_
"

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
if $DRY_RUN; then
  echo -e "${CYAN}${BOLD}-- DRY RUN -- CHANGELOG PREVIEW ----------------------------------------${RESET}" >&2
  if $APPEND; then
    echo "${SECTION}${BODY}"
  else
    echo "${HEADER}${SECTION}${BODY}${FOOTER}"
  fi
  echo -e "${CYAN}${BOLD}------------------------------------------------------------------------${RESET}" >&2
  ok "Dry-run complete. No files written."
elif $APPEND; then
  # Prepend new section after the header separator (first ---)
  TARGET="${REPO_ROOT}/${OUTPUT}"
  if [[ -f "$TARGET" ]]; then
    EXISTING=$(cat "$TARGET")
    # Insert after the first "---" line
    if [[ "$EXISTING" == *"---"* ]]; then
      BEFORE="${EXISTING%%---*}---"
      AFTER="${EXISTING#*---}"
      # Skip leading newlines in AFTER
      AFTER="${AFTER#$'\n'}"
      echo "${BEFORE}

${SECTION}${BODY}---

${AFTER}" > "$TARGET"
    else
      # No separator found, just prepend
      echo "${HEADER}${SECTION}${BODY}${FOOTER}

${EXISTING}" > "$TARGET"
    fi
    ok "Prepended new section to ${OUTPUT}"
  else
    echo "${HEADER}${SECTION}${BODY}${FOOTER}" > "$TARGET"
    ok "Created ${OUTPUT} (no existing file to append to)"
  fi
else
  echo "${HEADER}${SECTION}${BODY}${FOOTER}" > "${REPO_ROOT}/${OUTPUT}"
  ok "Wrote ${OUTPUT}"
fi

# ---------------------------------------------------------------------------
# Terminal summary
# ---------------------------------------------------------------------------
echo "" >&2
echo -e "${BOLD}Summary${RESET}" >&2
echo -e "  ${GREEN}Added  ${RESET} ${#CAT_ADDED[@]}" >&2
echo -e "  ${RED}Fixed  ${RESET} ${#CAT_FIXED[@]}" >&2
echo -e "  ${YELLOW}Changed${RESET} ${#CAT_CHANGED[@]}" >&2
echo -e "  ${DIM}Removed${RESET} ${#CAT_REMOVED[@]}" >&2
[[ ${#CAT_OTHER[@]} -gt 0 ]] && echo -e "  ${DIM}Other  ${RESET} ${#CAT_OTHER[@]}" >&2
echo "" >&2
