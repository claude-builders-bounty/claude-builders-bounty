#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# changelog.sh — Auto-generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh              # write CHANGELOG.md
#   bash changelog.sh --dry-run    # print to stdout, don't write file
#   bash changelog.sh --since v1.2 # start from a specific tag
#   bash changelog.sh --help
#
# The script fetches all commits since the most recent git tag (or the very
# first commit if no tag exists) and categorises them using conventional-commit
# keywords into: Added / Fixed / Changed / Removed.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────────────
OUTPUT_FILE="CHANGELOG.md"
DRY_RUN=false
SINCE_TAG=""
VERSION_LABEL=""

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()  { echo -e "${CYAN}ℹ${RESET}  $*"; }
ok()    { echo -e "${GREEN}✓${RESET}  $*"; }
warn()  { echo -e "${YELLOW}⚠${RESET}  $*" >&2; }
die()   { echo -e "${RED}✗${RESET}  $*" >&2; exit 1; }

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)       DRY_RUN=true; shift ;;
    --since)         SINCE_TAG="$2"; shift 2 ;;
    --output|-o)     OUTPUT_FILE="$2"; shift 2 ;;
    --version)       VERSION_LABEL="$2"; shift 2 ;;
    --help|-h)
      cat <<EOF
Usage: bash changelog.sh [OPTIONS]

OPTIONS:
  --dry-run          Print the changelog to stdout instead of writing a file
  --since <tag>      Start from a specific tag (default: last tag in repo)
  --output <file>    Output file path (default: CHANGELOG.md)
  --version <label>  Version label for the new section (default: Unreleased)
  --help             Show this help

EXAMPLES:
  bash changelog.sh
  bash changelog.sh --dry-run
  bash changelog.sh --since v1.0.0 --version v1.1.0
EOF
      exit 0 ;;
    *)
      die "Unknown argument: $1  (run with --help for usage)" ;;
  esac
done

# ── Sanity checks ─────────────────────────────────────────────────────────────
command -v git &>/dev/null || die "git is not installed."
git rev-parse --git-dir &>/dev/null 2>&1 || die "Not inside a git repository."

# ── Determine the start ref ───────────────────────────────────────────────────
if [[ -n "$SINCE_TAG" ]]; then
  LAST_TAG="$SINCE_TAG"
  git rev-parse --verify "$LAST_TAG^{}" &>/dev/null \
    || die "Tag '$LAST_TAG' not found in this repository."
else
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
fi

if [[ -z "$LAST_TAG" ]]; then
  warn "No git tags found. Generating changelog from the very first commit."
  GIT_RANGE=""
else
  info "Generating changelog since tag: ${BOLD}${LAST_TAG}${RESET}"
  GIT_RANGE="${LAST_TAG}..HEAD"
fi

# ── Version label ─────────────────────────────────────────────────────────────
[[ -z "$VERSION_LABEL" ]] && VERSION_LABEL="Unreleased"
TODAY=$(date +%Y-%m-%d)

# ── Fetch commits ──────────────────────────────────────────────────────────────
# Format: <short-hash> <subject>
mapfile -t COMMITS < <(
  git log ${GIT_RANGE} --no-merges --pretty=format:"%h %s" 2>/dev/null || true
)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
  warn "No commits found since ${LAST_TAG:-the beginning}. Nothing to generate."
  exit 0
fi

info "Found ${#COMMITS[@]} commit(s) to categorise."

# ── Categorisation arrays ──────────────────────────────────────────────────────
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

categorise() {
  local hash="$1"
  local subject="$2"

  # Strip conventional-commit type prefix for cleaner display
  local clean_subject
  clean_subject=$(echo "$subject" \
    | sed -E 's/^(feat|fix|refactor|chore|docs|style|test|perf|ci|build|revert)(\([^)]*\))?[!]?:\s*//' \
    | sed -E 's/^[[:upper:]]/\l&/')   # lowercase first char for consistent style

  local lower_subject="${subject,,}"   # bash lowercase

  case "$lower_subject" in
    feat*|add*|new*|introduce*|implement*|"feature"*)
      ADDED+=("- ${clean_subject} (\`${hash}\`)")
      ;;
    fix*|bug*|patch*|hotfix*|correct*|resolve*|repair*)
      FIXED+=("- ${clean_subject} (\`${hash}\`)")
      ;;
    remove*|delete*|drop*|deprecate*|revert*)
      REMOVED+=("- ${clean_subject} (\`${hash}\`)")
      ;;
    refactor*|change*|update*|upgrade*|migrate*|improve*|enhance*|bump*|perf*|style*|chore*|docs*|test*|ci*|build*)
      CHANGED+=("- ${clean_subject} (\`${hash}\`)")
      ;;
    *)
      # Fallback: try to infer from keywords anywhere in subject
      if echo "$lower_subject" | grep -qE '\b(add|new|feat|creat|introduc|implement)\b'; then
        ADDED+=("- ${clean_subject} (\`${hash}\`)")
      elif echo "$lower_subject" | grep -qE '\b(fix|bug|patch|hotfix|resolv|repair|correct)\b'; then
        FIXED+=("- ${clean_subject} (\`${hash}\`)")
      elif echo "$lower_subject" | grep -qE '\b(remov|delet|drop|deprecat|revert)\b'; then
        REMOVED+=("- ${clean_subject} (\`${hash}\`)")
      else
        CHANGED+=("- ${clean_subject} (\`${hash}\`)")
      fi
      ;;
  esac
}

for commit in "${COMMITS[@]}"; do
  hash="${commit%% *}"
  subject="${commit#* }"
  categorise "$hash" "$subject"
done

# ── Build the new section ─────────────────────────────────────────────────────
build_section() {
  local title="$1"
  shift
  local items=("$@")

  if [[ ${#items[@]} -gt 0 ]]; then
    echo ""
    echo "### $title"
    echo ""
    for item in "${items[@]}"; do
      echo "$item"
    done
  fi
}

NEW_SECTION=""
NEW_SECTION+="## [${VERSION_LABEL}] — ${TODAY}"$'\n'

NEW_SECTION+="$(build_section "Added"   "${ADDED[@]+"${ADDED[@]}"}")"
NEW_SECTION+="$(build_section "Fixed"   "${FIXED[@]+"${FIXED[@]}"}")"
NEW_SECTION+="$(build_section "Changed" "${CHANGED[@]+"${CHANGED[@]}"}")"
NEW_SECTION+="$(build_section "Removed" "${REMOVED[@]+"${REMOVED[@]}"}")"

# ── Output ────────────────────────────────────────────────────────────────────
HEADER="# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Commits follow [Conventional Commits](https://www.conventionalcommits.org/) where possible.

"

if $DRY_RUN; then
  echo -e "${HEADER}${NEW_SECTION}"
else
  # Prepend new section to existing CHANGELOG.md (or create fresh)
  if [[ -f "$OUTPUT_FILE" ]]; then
    # Strip the static header if it already exists to avoid duplication
    EXISTING=$(tail -n +8 "$OUTPUT_FILE" 2>/dev/null || cat "$OUTPUT_FILE")
    printf '%s\n%s\n\n%s' "$HEADER" "$NEW_SECTION" "$EXISTING" > "$OUTPUT_FILE"
    ok "Updated ${OUTPUT_FILE} (new section prepended)."
  else
    printf '%s\n%s\n' "$HEADER" "$NEW_SECTION" > "$OUTPUT_FILE"
    ok "Created ${OUTPUT_FILE}."
  fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Summary:${RESET}"
echo "  Added:   ${#ADDED[@]}"
echo "  Fixed:   ${#FIXED[@]}"
echo "  Changed: ${#CHANGED[@]}"
echo "  Removed: ${#REMOVED[@]}"
echo ""
