#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Reads conventional-commit messages (feat!, fix!, etc.) and produces a
# Keep-a-Changelog-style document grouped by version and category.
#
# Usage:
#   bash changelog.sh                    # all tags + unreleased
#   bash changelog.sh v1.2.0             # from v1.2.0 to HEAD
#   bash changelog.sh v1.1.0 v1.2.0      # v1.1.0..v1.2.0 only
#
# Categories (auto-detected from commit prefixes):
#   feat:     → Added
#   fix:      → Fixed
#   refactor: → Changed
#   perf:     → Changed
#   docs:     → Changed
#   style:    → Changed
#   test:     → Changed
#   chore:    → Changed
#   ci:       → Changed
#   build:    → Changed
#   remove:   → Removed
#   deprecate:→ Deprecated
#   breaking: → Removed  (feat!, fix!, or BREAKING CHANGE footer)
#
# ---------------------------------------------------------------------------

set -euo pipefail

# ── Colours (only when stdout is a terminal) ─────────────────────────────
if [[ -t 1 ]]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
  NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; NC=''
fi

# ── Helpers ──────────────────────────────────────────────────────────────
info()  { printf "${GREEN}[INFO]${NC}  %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$*"; }
error() { printf "${RED}[ERROR]${NC} %s\n" "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
changelog.sh — Generate CHANGELOG.md from git history

USAGE
  bash changelog.sh [FROM_TAG] [TO_TAG]

ARGUMENTS
  FROM_TAG   Start of range (default: earliest tag)
  TO_TAG     End of range   (default: HEAD)

OPTIONS
  -o, --output FILE   Output file  (default: CHANGELOG.md)
  -h, --help          Show this help message

EXAMPLES
  bash changelog.sh                        # full history
  bash changelog.sh v1.2.0                 # v1.2.0 → HEAD
  bash changelog.sh v1.1.0 v1.2.0          # v1.1.0 → v1.2.0
  bash changelog.sh -o RELEASES.md          # write to RELEASES.md
EOF
  exit 0
}

# ── Argument parsing ─────────────────────────────────────────────────────
OUTPUT="CHANGELOG.md"
FROM_TAG=""
TO_TAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output) OUTPUT="$2"; shift 2 ;;
    -h|--help)   usage ;;
    *)
      if [[ -z "$FROM_TAG" ]]; then FROM_TAG="$1"
      elif [[ -z "$TO_TAG" ]]; then TO_TAG="$1"
      else error "Unexpected argument: $1"; fi
      shift
      ;;
  esac
done

# ── Pre-flight checks ────────────────────────────────────────────────────
command -v git >/dev/null 2>&1 || error "git is not installed"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || error "not inside a git repository"

cd "$(git rev-parse --show-toplevel)"

# ── Determine tag ranges ────────────────────────────────────────────────
# Build an ordered list of tags (oldest → newest)
mapfile -t ALL_TAGS < <(git tag --sort=version:refname 2>/dev/null)

if [[ ${#ALL_TAGS[@]} -eq 0 ]]; then
  warn "No git tags found — treating entire history as unreleased"
  RANGES=("HEAD")
else
  # Create ranges: each tag covers commits back to the previous tag
  RANGES=()
  for i in "${!ALL_TAGS[@]}"; do
    if [[ "$i" -eq 0 ]]; then
      RANGES+=("${ALL_TAGS[$i]}")
    else
      RANGES+=("${ALL_TAGS[$((i-1))]}..${ALL_TAGS[$i]}")
    fi
  done
  # Add unreleased (last tag → HEAD)
  RANGES+=("${ALL_TAGS[-1]}..HEAD")
fi

# If the user specified a range, filter to just that range
if [[ -n "$FROM_TAG" ]]; then
  if [[ -n "$TO_TAG" ]]; then
    RANGES=("${FROM_TAG}..${TO_TAG}")
  else
    RANGES=("${FROM_TAG}..HEAD")
  fi
fi

# ── Commit → category mapping ───────────────────────────────────────────
categorize_one() {
  local msg="$1"

  # Check for BREAKING CHANGE in footer first
  if echo "$msg" | tail -n +2 | grep -qiE "^BREAKING[ -]CHANGE:"; then
    echo "Removed"
    return
  fi

  local prefix
  prefix=$(echo "$msg" | head -1 | sed -E 's/^([a-z]+)(\(.+\))?!?:.*/\1/')

  # Detect breaking-change bang  (feat!, fix!, etc.)
  if echo "$msg" | head -1 | grep -qE '^[a-z]+(\(.+\))?!:'; then
    echo "Removed"
    return
  fi

  case "$prefix" in
    feat)      echo "Added"      ;;
    fix)       echo "Fixed"      ;;
    remove)    echo "Removed"    ;;
    deprecate) echo "Deprecated" ;;
    refactor|perf|docs|style|test|chore|ci|build) echo "Changed" ;;
    *)         echo "Changed"    ;;
  esac
}

# ── Format a single commit line ──────────────────────────────────────────
format_commit() {
  local msg="$1"
  local hash="$2"
  # Strip the type[(scope)]!: prefix, keep the description
  local desc
  desc=$(echo "$msg" | head -1 | sed -E 's/^[a-z]+(\(.+\))?!?:[[:space:]]*//')
  # Append scope if present
  local scope
  scope=$(echo "$msg" | head -1 | sed -nE 's/^[a-z]+\((.+)\)!?:.*/\1/p')
  if [[ -n "$scope" ]]; then
    echo "- **${scope}:** ${desc} (${hash})"
  else
    echo "- ${desc} (${hash})"
  fi
}

# ── Build the CHANGELOG ─────────────────────────────────────────────────
TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo "Generated by \`changelog.sh\` from git history."
  echo ""

  for RANGE in "${RANGES[@]}"; do
    # Determine the version title
    if [[ "$RANGE" == "HEAD" ]]; then
      VERSION="Unreleased"
      DATE=""
    elif [[ "$RANGE" == *"..HEAD" ]]; then
      TAG="${RANGE%..HEAD}"
      VERSION="Unreleased"
      DATE=""
    elif [[ "$RANGE" == *".."* ]]; then
      TO="${RANGE##*..}"
      VERSION="$TO"
      TAG_DATE=$(git log -1 --format="%ai" "$TO" 2>/dev/null || echo "")
      if [[ -n "$TAG_DATE" ]]; then
        DATE=" - $(echo "$TAG_DATE" | cut -d' ' -f1)"
      else
        DATE=""
      fi
    else
      VERSION="$RANGE"
      TAG_DATE=$(git log -1 --format="%ai" "$RANGE" 2>/dev/null || echo "")
      if [[ -n "$TAG_DATE" ]]; then
        DATE=" - $(echo "$TAG_DATE" | cut -d' ' -f1)"
      else
        DATE=""
      fi
    fi

    # Get commits in this range (skip merge commits)
    mapfile -t COMMITS < <(
      git log --no-merges --format="%H___SEPARATOR___%B___ENDCOMMIT___" "$RANGE" 2>/dev/null || true
    )

    # Parse commits into categories
    declare -A CATEGORIES
    CATEGORIES[Added]=""
    CATEGORIES[Fixed]=""
    CATEGORIES[Changed]=""
    CATEGORIES[Removed]=""
    CATEGORIES[Deprecated]=""

    FOUND_ANY=0

    for ENTRY in "${COMMITS[@]}"; do
      # Skip empty entries
      [[ -z "$ENTRY" ]] && continue

      HASH=$(echo "$ENTRY" | sed -E 's/^([a-f0-9]+)___SEPARATOR___.*/\1/')
      MSG=$(echo "$ENTRY" | sed 's/^[a-f0-9]*___SEPARATOR___//; s/___ENDCOMMIT___$//')

      # Skip empty messages
      [[ -z "$(echo "$MSG" | tr -d '[:space:]')" ]] && continue

      CAT=$(categorize_one "$MSG")
      LINE=$(format_commit "$MSG" "${HASH:0:7}")
      CATEGORIES[$CAT]="${CATEGORIES[$CAT]}${LINE}"$'\n'
      FOUND_ANY=1
    done

    if [[ "$FOUND_ANY" -eq 1 ]]; then
      echo "## ${VERSION}${DATE}"
      echo ""

      for CAT in "Added" "Fixed" "Changed" "Deprecated" "Removed"; do
        if [[ -n "${CATEGORIES[$CAT]}" ]]; then
          echo "### $CAT"
          echo ""
          echo "${CATEGORIES[$CAT]}"
        fi
      done
    fi

    unset CATEGORIES
  done

} > "$TMPFILE"

# ── Clean up extra blank lines ───────────────────────────────────────────
# Collapse 3+ consecutive blank lines into 2 (section separator)
sed -i '/^$/{ N;/^\n$/d; }' "$TMPFILE" 2>/dev/null || true

# ── Write output ─────────────────────────────────────────────────────────
mv "$TMPFILE" "$OUTPUT"
info "CHANGELOG written to $OUTPUT"
