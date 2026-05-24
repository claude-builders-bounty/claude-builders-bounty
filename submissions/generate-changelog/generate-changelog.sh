#!/usr/bin/env bash
set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────
OUTPUT="${OUTPUT:-CHANGELOG.md}"
REPO_URL="${REPO_URL:-}"
COMPARE_URL="${COMPARE_URL:-}"

# ─── Help ─────────────────────────────────────────────────────────
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: ./generate-changelog.sh [--since <tag|commit>] [--output <file>]

Generates a structured CHANGELOG.md from git history between the latest
two tags (or since a specific tag/commit).

Options:
  --since <ref>    Start from this tag or commit (default: second-to-last tag)
  --output <file>  Write to this file (default: CHANGELOG.md)
  --repo-url <url> GitHub repo URL for compare links
  -h, --help       Show this help

Categorization rules:
  feat:     → Added
  fix:      → Fixed
  refactor: → Changed
  perf:     → Changed
  revert:   → Removed
  chore/docs/style/test/ci/build → Changed (misc)
  Everything else → Changed (uncategorized)

Examples:
  ./generate-changelog.sh                           # between last two tags
  ./generate-changelog.sh --since v1.0.0            # since v1.0.0
  ./generate-changelog.sh --output ../docs/CHANGELOG.md
  REPO_URL=https://github.com/user/repo ./generate-changelog.sh

Env vars:
  OUTPUT      Output file path (default: CHANGELOG.md)
  REPO_URL    GitHub repo URL for compare links
  COMPARE_URL Custom compare URL template ({from}...{to})
EOF
  exit 0
fi

# ─── Parse arguments ──────────────────────────────────────────────
SINCE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --repo-url) REPO_URL="$2"; shift 2 ;;
    *) echo "Unknown option: $1 (use -h for help)" >&2; exit 1 ;;
  esac
done

# ─── Ensure we're in a git repo ───────────────────────────────────
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not in a git repository" >&2
  exit 1
fi

# ─── Determine range ──────────────────────────────────────────────
TAGS=($(git tag --sort=-creatordate 2>/dev/null || true))

if [[ -n "$SINCE" ]]; then
  FROM="$SINCE"
  TO="HEAD"
elif [[ ${#TAGS[@]} -ge 2 ]]; then
  FROM="${TAGS[1]}"   # second-to-last tag
  TO="${TAGS[0]}"      # latest tag
elif [[ ${#TAGS[@]} -eq 1 ]]; then
  FROM="${TAGS[0]}"
  TO="HEAD"
else
  # No tags at all — use first commit as "from"
  FROM=$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "HEAD~50")
  TO="HEAD"
fi

# ─── Build compare URL ────────────────────────────────────────────
if [[ -z "$COMPARE_URL" && -n "$REPO_URL" ]]; then
  COMPARE_URL="${REPO_URL}/compare/${FROM}...${TO}"
fi

# ─── Collect commits ──────────────────────────────────────────────
echo "→ Scanning commits: ${FROM} → ${TO}"
COMMITS=$(git log "${FROM}..${TO}" --pretty=format:"%h %s" --no-merges 2>/dev/null || echo "")

if [[ -z "$COMMITS" ]]; then
  echo "→ No commits found in range ${FROM}..${TO}"
  COMMITS=$(git log "${FROM}..${TO}" --pretty=format:"%h %s" 2>/dev/null || echo "")
  if [[ -z "$COMMITS" ]]; then
    echo "→ Still no commits. Trying last 50 commits..."
    COMMITS=$(git log -50 --pretty=format:"%h %s" --no-merges 2>/dev/null || echo "")
    FROM="HEAD~50"
    TO="HEAD"
  fi
fi

# ─── Categorize ───────────────────────────────────────────────────
declare -a ADDED=() FIXED=() CHANGED=() REMOVED=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  hash="${line:0:7}"
  msg="${line:8}"

  # Conventional commit detection
  if [[ "$msg" =~ ^feat(\(.*\))?[!:]\  ]]; then
    ADDED+=("- ${msg} (${hash})")
  elif [[ "$msg" =~ ^fix(\(.*\))?[!:]\  ]]; then
    FIXED+=("- ${msg} (${hash})")
  elif [[ "$msg" =~ ^revert(\(.*\))?:\  ]]; then
    REMOVED+=("- ${msg} (${hash})")
  elif [[ "$msg" =~ ^(refactor|perf)(\(.*\))?[!:]\  ]]; then
    CHANGED+=("- ${msg} (${hash})")
  elif [[ "$msg" =~ ^(chore|docs|style|test|ci|build)(\(.*\))?[!:]\  ]]; then
    CHANGED+=("- ${msg} (${hash})")
  else
    CHANGED+=("- ${msg} (${hash})")
  fi
done <<< "$COMMITS"

# ─── Count ────────────────────────────────────────────────────────
TOTAL=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]}))

# ─── Generate header ──────────────────────────────────────────────
DATE=$(date +%Y-%m-%d)
VERSION="${TO#v}"  # strip leading 'v' if present
[[ "$TO" == "HEAD" ]] && VERSION="Unreleased"

cat > "$OUTPUT" <<CHANGELOG_HEADER
# Changelog

## [${VERSION}] - ${DATE}

CHANGELOG_HEADER

if [[ -n "$COMPARE_URL" ]]; then
  echo "[Full changelog](${COMPARE_URL})" >> "$OUTPUT"
fi

echo "" >> "$OUTPUT"

# ─── Write sections ───────────────────────────────────────────────
write_section() {
  local title="$1"
  local arrname="$2"
  # Use eval to get array length (compatible with bash 3.2 on macOS)
  local count
  eval "count=\${#${arrname}[@]}"
  if [[ $count -gt 0 ]]; then
    echo "### ${title}" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    eval "
      for item in \"\${${arrname}[@]}\"; do
        echo \"\$item\" >> \"\$OUTPUT\"
      done
    "
    echo "" >> "$OUTPUT"
  fi
}

write_section "Added"   ADDED
write_section "Fixed"   FIXED
write_section "Changed" CHANGED
write_section "Removed" REMOVED

# ─── Summary ──────────────────────────────────────────────────────
echo "✅ CHANGELOG written to ${OUTPUT}"
echo "   ${TOTAL} commits: +${#ADDED[@]} added, ~${#FIXED[@]} fixed, ≈${#CHANGED[@]} changed, -${#REMOVED[@]} removed"
echo "   Range: ${FROM} → ${TO}"
