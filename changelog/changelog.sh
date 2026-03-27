#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  changelog.sh — Generate structured CHANGELOG from git      ║
# ║                                                              ║
# ║  Auto-categorizes commits into Added / Fixed / Changed /     ║
# ║  Removed using conventional-commit prefixes and keywords.    ║
# ╚══════════════════════════════════════════════════════════════╝

set -uo pipefail

VERSION=""
SINCE=""
OUTPUT="CHANGELOG.md"
DRY_RUN=false

# ─── Parse Arguments ──────────────────────────────────────────
usage() {
  echo "Usage: changelog.sh [options]"
  echo ""
  echo "Options:"
  echo "  -v, --version VERSION   Version label (default: auto-detect from git tag or 'Unreleased')"
  echo "  -s, --since TAG/HASH    Starting point (default: last git tag)"
  echo "  -o, --output FILE       Output file (default: CHANGELOG.md)"
  echo "  -d, --dry-run           Print to stdout instead of writing file"
  echo "  -h, --help              Show this help"
  exit 0
}

while [[ $# -gt 0 ]]; do
  case $1 in
    -v|--version) VERSION="$2"; shift 2 ;;
    -s|--since) SINCE="$2"; shift 2 ;;
    -o|--output) OUTPUT="$2"; shift 2 ;;
    -d|--dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

# ─── Detect Boundaries ───────────────────────────────────────
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: not a git repository" >&2
  exit 1
fi

# Find the last tag if no --since given
if [ -z "$SINCE" ]; then
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Auto-detect version label
if [ -z "$VERSION" ]; then
  if [ -n "$SINCE" ]; then
    # Bump from last tag (suggest next patch)
    VERSION="$SINCE → HEAD"
  else
    VERSION="Unreleased"
  fi
fi

# Build git log range
if [ -n "$SINCE" ]; then
  RANGE="${SINCE}..HEAD"
  COMMIT_COUNT=$(git rev-list --count "$RANGE" 2>/dev/null || echo "0")
else
  RANGE="HEAD"
  COMMIT_COUNT=$(git rev-list --count HEAD 2>/dev/null || echo "0")
fi

if [ "$COMMIT_COUNT" = "0" ]; then
  echo "No commits found since ${SINCE:-repository start}." >&2
  exit 0
fi

DATE=$(date +%Y-%m-%d)

# ─── Categorize Commits ──────────────────────────────────────
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line; do
  # Extract hash and message
  HASH=$(echo "$line" | cut -d' ' -f1)
  MSG=$(echo "$line" | cut -d' ' -f2-)

  # Skip merge commits
  if echo "$MSG" | grep -qiP '^Merge (pull request|branch)'; then
    continue
  fi

  # Categorize by conventional commit prefix or keywords
  ENTRY="- ${MSG} (\`${HASH}\`)"

  if echo "$MSG" | grep -qiP '^(feat|add|new)[(:!]|^feat\b|added?\b|create[ds]?\b|implement'; then
    ADDED="${ADDED}\n${ENTRY}"
  elif echo "$MSG" | grep -qiP '^fix[(:!]|^fix\b|fixed?\b|bug|patch|resolve[ds]?|hotfix'; then
    FIXED="${FIXED}\n${ENTRY}"
  elif echo "$MSG" | grep -qiP '^(remove|delete|drop|deprecat)[(:!ds]|removed?\b|deleted?\b'; then
    REMOVED="${REMOVED}\n${ENTRY}"
  elif echo "$MSG" | grep -qiP '^(refactor|chore|style|perf|ci|build|docs|test|update|upgrade|rename|move|config)[(:!]|changed?\b|updat|refactor|migrat|improv'; then
    CHANGED="${CHANGED}\n${ENTRY}"
  else
    # Default: treat as Changed
    CHANGED="${CHANGED}\n${ENTRY}"
  fi
done < <(git log --oneline --no-merges $RANGE 2>/dev/null)

# ─── Generate Markdown ────────────────────────────────────────
CHANGELOG="# Changelog\n\n"
CHANGELOG+="## [${VERSION}] — ${DATE}\n\n"

if [ -n "$ADDED" ]; then
  CHANGELOG+="### Added\n${ADDED}\n\n"
fi

if [ -n "$FIXED" ]; then
  CHANGELOG+="### Fixed\n${FIXED}\n\n"
fi

if [ -n "$CHANGED" ]; then
  CHANGELOG+="### Changed\n${CHANGED}\n\n"
fi

if [ -n "$REMOVED" ]; then
  CHANGELOG+="### Removed\n${REMOVED}\n\n"
fi

# ─── Output ───────────────────────────────────────────────────
if $DRY_RUN; then
  echo -e "$CHANGELOG"
else
  echo -e "$CHANGELOG" > "$OUTPUT"
  echo "✅ CHANGELOG written to ${OUTPUT} (${COMMIT_COUNT} commits categorized)"
fi
