#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG from git history
# Usage: ./changelog.sh [--since <date|tag>] [--output <file>] [--dry-run] [--no-color]
set -euo pipefail

# ── Color helpers ────────────────────────────────────────────────────────────
COLOR=${CHANGELOG_COLOR:-auto}
if [[ "$COLOR" == "auto" ]]; then
  [[ -t 1 ]] && COLOR=yes || COLOR=no
fi

if [[ "$COLOR" == "yes" ]]; then
  BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'
  GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'
else
  BOLD=''; DIM=''; RESET=''; GREEN=''; BLUE=''; YELLOW=''; RED=''; CYAN=''
fi

info()    { echo -e "${BLUE}ℹ${RESET} $*" >&2; }
success() { echo -e "${GREEN}✔${RESET} $*" >&2; }
warn()    { echo -e "${YELLOW}⚠${RESET} $*" >&2; }
die()     { echo -e "${RED}✖${RESET} $*" >&2; exit 1; }

# ── Defaults ─────────────────────────────────────────────────────────────────
SINCE=""
OUTPUT="CHANGELOG.md"
DRY_RUN=false
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || die "Not inside a git repository."
VERSION=""

# ── Argument parsing ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)      SINCE="$2";     shift 2 ;;
    --output|-o)  OUTPUT="$2";    shift 2 ;;
    --dry-run)    DRY_RUN=true;   shift   ;;
    --no-color)   COLOR=no;       BOLD=''; DIM=''; RESET=''; GREEN=''; BLUE=''; YELLOW=''; RED=''; CYAN=''; shift ;;
    --version)    VERSION="$2";   shift 2 ;;
    --help|-h)
      echo "Usage: $0 [--since <date|tag>] [--output <file>] [--dry-run] [--no-color] [--version <v1.x.x>]"
      exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
done

# ── Determine commit range ────────────────────────────────────────────────────
if [[ -n "$SINCE" ]]; then
  # User-supplied: could be a tag name, a date string, or a commit hash
  if git rev-parse --verify "$SINCE^{commit}" &>/dev/null; then
    RANGE="${SINCE}..HEAD"
    RANGE_LABEL="since $SINCE"
  else
    # Treat as a date
    RANGE="HEAD"
    DATE_FILTER="--since=${SINCE}"
    RANGE_LABEL="since $SINCE"
  fi
else
  # Auto-detect: last tag, else first commit
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  DATE_FILTER=""
  if [[ -n "$LAST_TAG" ]]; then
    RANGE="${LAST_TAG}..HEAD"
    RANGE_LABEL="since tag ${LAST_TAG}"
  else
    FIRST_COMMIT=$(git rev-list --max-parents=0 HEAD)
    RANGE="${FIRST_COMMIT}..HEAD"
    RANGE_LABEL="since first commit (no tags found)"
    warn "No git tags found — using all commits from first commit."
  fi
fi

# ── Resolve version label ─────────────────────────────────────────────────────
if [[ -z "$VERSION" ]]; then
  VERSION=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -z "$VERSION" ]]; then
    VERSION="Unreleased"
  else
    # Suggest next patch version
    if [[ "$VERSION" =~ ^v?([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
      MAJOR="${BASH_REMATCH[1]}"; MINOR="${BASH_REMATCH[2]}"; PATCH="${BASH_REMATCH[3]}"
      VERSION="v${MAJOR}.${MINOR}.$((PATCH + 1))"
    else
      VERSION="Unreleased"
    fi
  fi
fi

# ── Fetch commits ─────────────────────────────────────────────────────────────
info "Collecting commits (${RANGE_LABEL})…"

GIT_CMD=(git log "$RANGE" ${DATE_FILTER:-} --no-merges --pretty=format:"%H|%s|%an")
mapfile -t RAW_COMMITS < <("${GIT_CMD[@]}" 2>/dev/null || true)

TOTAL=${#RAW_COMMITS[@]}
if [[ $TOTAL -eq 0 ]]; then
  warn "No commits found for the given range."
fi
info "Found ${TOTAL} commit(s) to categorize."

# ── Categorize commits ────────────────────────────────────────────────────────
declare -a CAT_ADDED=() CAT_FIXED=() CAT_CHANGED=() CAT_REMOVED=() CAT_OTHER=()

# Conventional commit prefix → category mapping
categorize() {
  local hash="$1" subject="$2" author="$3"
  local short="${hash:0:7}"
  local entry="- ${subject} ([\`${short}\`](../../commit/${hash})) — *${author}*"

  # Conventional commits: feat / fix / chore / refactor / docs / style / test / perf / ci / build / revert / remove
  local lower; lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  if   [[ "$lower" =~ ^(feat|feature|add)[:(\ )] ]];            then CAT_ADDED+=("$entry")
  elif [[ "$lower" =~ ^(fix|bug|hotfix|patch)[:(\ )] ]];        then CAT_FIXED+=("$entry")
  elif [[ "$lower" =~ ^(remove|delete|drop|deprecat)[:(\ )] ]]; then CAT_REMOVED+=("$entry")
  elif [[ "$lower" =~ ^(refactor|perf|chore|build|ci|style|docs|test|revert|update|change|bump)[:(\ )] ]]; then CAT_CHANGED+=("$entry")
  # Fallback: keyword scan in subject
  elif [[ "$lower" =~ (added|new feature|implement|introduce) ]]; then CAT_ADDED+=("$entry")
  elif [[ "$lower" =~ (fix(ed)?|resolv|patch|correct|repair) ]]; then CAT_FIXED+=("$entry")
  elif [[ "$lower" =~ (remov|delet|drop|deprecat) ]];            then CAT_REMOVED+=("$entry")
  elif [[ "$lower" =~ (chang|updat|refactor|improv|optimiz|revert) ]]; then CAT_CHANGED+=("$entry")
  else CAT_OTHER+=("$entry")
  fi
}

for line in "${RAW_COMMITS[@]}"; do
  IFS='|' read -r hash subject author <<< "$line"
  categorize "$hash" "$subject" "$author"
done

# ── Build output ──────────────────────────────────────────────────────────────
TODAY=$(date +%Y-%m-%d)

build_section() {
  local title="$1"; shift
  local items=("$@")
  if [[ ${#items[@]} -gt 0 ]]; then
    printf "### %s\n\n" "$title"
    for item in "${items[@]}"; do
      printf "%s\n" "$item"
    done
    printf "\n"
  fi
}

CONTENT="# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [${VERSION}] — ${TODAY}

> _${TOTAL} commit(s) ${RANGE_LABEL}_

"

# Append each section
append_section() {
  local title="$1"; shift
  local items=("$@")
  if [[ ${#items[@]} -gt 0 ]]; then
    CONTENT+="$(build_section "$title" "${items[@]}")"
  fi
}

append_section "Added"   "${CAT_ADDED[@]+"${CAT_ADDED[@]}"}"
append_section "Fixed"   "${CAT_FIXED[@]+"${CAT_FIXED[@]}"}"
append_section "Changed" "${CAT_CHANGED[@]+"${CAT_CHANGED[@]}"}"
append_section "Removed" "${CAT_REMOVED[@]+"${CAT_REMOVED[@]}"}"

if [[ "${#CAT_OTHER[@]}" -gt 0 ]]; then
  append_section "Other"   "${CAT_OTHER[@]+"${CAT_OTHER[@]}"}"
fi

CONTENT+="---
_Generated by [changelog.sh](https://github.com/claude-builders-bounty/claude-builders-bounty) on ${TODAY}_
"

# ── Output ────────────────────────────────────────────────────────────────────
if $DRY_RUN; then
  echo -e "${CYAN}${BOLD}── DRY RUN — CHANGELOG PREVIEW ────────────────────────────────────${RESET}"
  echo "$CONTENT"
  echo -e "${CYAN}${BOLD}────────────────────────────────────────────────────────────────────${RESET}"
  success "Dry-run complete. No files written."
else
  echo "$CONTENT" > "${REPO_ROOT}/${OUTPUT}"
  success "Wrote ${OUTPUT}"
fi

# ── Terminal summary ──────────────────────────────────────────────────────────
echo -e ""
echo -e "${BOLD}Summary${RESET}"
echo -e "  ${GREEN}Added   ${RESET} ${#CAT_ADDED[@]}"
echo -e "  ${RED}Fixed   ${RESET} ${#CAT_FIXED[@]}"
echo -e "  ${YELLOW}Changed ${RESET} ${#CAT_CHANGED[@]}"
echo -e "  ${DIM}Removed ${RESET} ${#CAT_REMOVED[@]}"
[[ "${#CAT_OTHER[@]}" -gt 0 ]] && echo -e "  ${DIM}Other   ${RESET} ${#CAT_OTHER[@]}"
echo ""
