#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history.
# Fallback for environments without Claude Code. For the Claude-powered version, use SKILL.md.
#
# Usage:
#   bash changelog.sh                      # auto-detect last tag, write CHANGELOG.md
#   bash changelog.sh --since v1.2.0       # start from a specific tag or SHA
#   bash changelog.sh --output RELEASE.md  # write to a different file
#   bash changelog.sh --version 2.0.0      # override the version label
#   bash changelog.sh --preview            # print to stdout, do not write to disk

set -eo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
OUTPUT="CHANGELOG.md"
SINCE=""
VERSION=""
PREVIEW=0

# ── Argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since|-s)   SINCE="$2";   shift 2 ;;
    --output|-o)  OUTPUT="$2";  shift 2 ;;
    --version|-v) VERSION="$2"; shift 2 ;;
    --preview|-p) PREVIEW=1;    shift   ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ── Verify we're in a git repo ────────────────────────────────────────────────
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "❌ Not a git repository." >&2; exit 1
fi

# ── Determine starting ref ────────────────────────────────────────────────────
USE_FULL_HISTORY=0
if [[ -z "$SINCE" ]]; then
  SINCE="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi
if [[ -z "$SINCE" ]]; then
  SINCE="$(git rev-list --max-parents=0 HEAD 2>/dev/null)"
  USE_FULL_HISTORY=1
fi

# ── Version label ─────────────────────────────────────────────────────────────
if [[ -z "$VERSION" ]]; then
  VERSION="$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")"
fi

# ── Detect GitHub remote for commit links ─────────────────────────────────────
GITHUB_BASE=""
REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
if [[ "$REMOTE_URL" =~ github\.com[:/]([^/]+/[^/.]+)(\.git)?$ ]]; then
  GITHUB_BASE="https://github.com/${BASH_REMATCH[1]}/commit"
fi

# ── Collect commits ───────────────────────────────────────────────────────────
if [[ "$USE_FULL_HISTORY" -eq 1 ]]; then
  COMMITS_RAW="$(git log --format="%H|%s" --no-merges 2>/dev/null || true)"
else
  COMMITS_RAW="$(git log "${SINCE}..HEAD" --format="%H|%s" --no-merges 2>/dev/null || true)"
fi

if [[ -z "$COMMITS_RAW" ]]; then
  echo "ℹ️  No commits found since ${SINCE}." >&2; exit 0
fi

# ── Categorization helpers ────────────────────────────────────────────────────
classify() {
  local msg="$1"
  local prefix
  prefix="$(echo "${msg%%:*}" | sed 's/(.*//' | tr '[:upper:]' '[:lower:]' | tr -d '!')"
  case "$prefix" in
    feat|feature|add|new|implement|create|introduce) echo "added"   ;;
    fix|bugfix|hotfix|bug|patch|repair|correct)      echo "fixed"   ;;
    remove|delete|deprecate|drop|revert|clean)       echo "removed" ;;
    *)                                               echo "changed" ;;
  esac
}

clean_msg() {
  local raw="$1"
  local cleaned
  cleaned="$(echo "$raw" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//')"
  [[ -z "$cleaned" ]] && cleaned="$raw"
  local first rest
  first="$(echo "${cleaned:0:1}" | tr '[:lower:]' '[:upper:]')"
  rest="${cleaned:1}"
  echo "${first}${rest}"
}

sha_ref() {
  local sha="$1"
  local short="${sha:0:7}"
  if [[ -n "$GITHUB_BASE" ]]; then
    echo "[\`${short}\`](${GITHUB_BASE}/${sha})"
  else
    echo "\`${short}\`"
  fi
}

# ── Bucket commits ────────────────────────────────────────────────────────────
declare -a ADDED FIXED CHANGED REMOVED

while IFS= read -r entry; do
  [[ -z "$entry" ]] && continue
  sha="${entry%%|*}"
  msg="${entry#*|}"
  cat="$(classify "$msg")"
  label="$(clean_msg "$msg")"
  ref="$(sha_ref "$sha")"
  item="- ${label} (${ref})"
  case "$cat" in
    added)   ADDED+=("$item")   ;;
    fixed)   FIXED+=("$item")   ;;
    removed) REMOVED+=("$item") ;;
    *)       CHANGED+=("$item") ;;
  esac
done <<< "$COMMITS_RAW"

TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))

# ── Build the new section ─────────────────────────────────────────────────────
DATE="$(date +%Y-%m-%d)"

section() {
  local heading="$1" emoji="$2"
  shift 2
  if [[ $# -gt 0 ]]; then
    printf '### %s %s\n\n' "$emoji" "$heading"
    printf '%s\n' "$@"
    echo
  fi
}

NEW_SECTION="$(
  printf '## [%s] – %s\n\n' "$VERSION" "$DATE"
  section "Added"   "✨" "${ADDED[@]+"${ADDED[@]}"}"
  section "Fixed"   "🐛" "${FIXED[@]+"${FIXED[@]}"}"
  section "Changed" "🔧" "${CHANGED[@]+"${CHANGED[@]}"}"
  section "Removed" "🗑️" "${REMOVED[@]+"${REMOVED[@]}"}"
)"

# ── Write output ──────────────────────────────────────────────────────────────
if [[ "$PREVIEW" -eq 1 ]]; then
  printf '# Changelog\n\n%s\n' "$NEW_SECTION"
else
  if [[ -f "$OUTPUT" ]] && grep -q '^# Changelog' "$OUTPUT"; then
    # Insert after the first "# Changelog" line
    python3 - "$OUTPUT" "$NEW_SECTION" <<'PYEOF'
import sys, pathlib
path, section = sys.argv[1], sys.argv[2]
lines = pathlib.Path(path).read_text().splitlines(keepends=True)
out = []
inserted = False
for line in lines:
    out.append(line)
    if not inserted and line.strip() == '# Changelog':
        out.append('\n')
        out.append(section + '\n')
        inserted = True
pathlib.Path(path).write_text(''.join(out))
PYEOF
  else
    printf '# Changelog\n\n%s\n' "$NEW_SECTION" > "$OUTPUT"
  fi
  echo "✅ ${TOTAL} commits → ${OUTPUT}  (added: ${#ADDED[@]}, fixed: ${#FIXED[@]}, changed: ${#CHANGED[@]}, removed: ${#REMOVED[@]})"
fi
