#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage:
#   ./changelog.sh                     # commits since last tag → CHANGELOG.md
#   ./changelog.sh v1.0.0..v1.1.0     # specific range
#   ./changelog.sh --range v1.0.0..v1.1.0
#   ./changelog.sh --output mylog.md
#   ./changelog.sh --format markdown|json

set -euo pipefail

# ─── Defaults ───────────────────────────────────────────────
OUTPUT="CHANGELOG.md"
FORMAT="markdown"
RANGE=""

# ─── Parse args ─────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --range)   RANGE="$2"; shift 2 ;;
    --output)  OUTPUT="$2"; shift 2 ;;
    --format)  FORMAT="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS] [RANGE]"
      echo "  --range REF1..REF2   Commit range"
      echo "  --output FILE        Output file (default: CHANGELOG.md)"
      echo "  --format FORMAT      Output format: markdown|json (default: markdown)"
      echo "  RANGE                Shorthand for --range (e.g. v1.0..v2.0)"
      echo "  If no range given, uses last tag..HEAD"
      exit 0
      ;;
    *)         RANGE="$1"; shift ;;
  esac
done

# ─── Resolve range ──────────────────────────────────────────
if [[ -z "$RANGE" ]]; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -z "$LAST_TAG" ]]; then
    RANGE="HEAD"
  else
    RANGE="${LAST_TAG}..HEAD"
  fi
fi

# ─── Fetch commits ──────────────────────────────────────────
declare -A ADDED=() FIXED=() CHANGED=() REMOVED=()
declare -A OTHER=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  msg="${line#*|}"
  msg="$(echo "$msg" | sed 's/^[[:space:]]*//')"
  [[ -z "$msg" ]] && continue

  # Skip merge commits
  [[ "$msg" =~ ^[Mm]erge ]] && continue
  # Skip deps/CI bumps
  [[ "$msg" =~ ^(deps|ci|chore)\(dependabot\)|^Bump ]] && continue

  # Categorize by commit prefix (Conventional Commits style)
  if [[ "$msg" =~ ^feat\(.*\)?:|^add|^new ]]; then
    ADDED["$msg"]=1
  elif [[ "$msg" =~ ^fix\(.*\)?:|^bug|^patch ]]; then
    FIXED["$msg"]=1
  elif [[ "$msg" =~ ^refactor\(.*\)?:|^improve|^update|^change|^rename|^move ]]; then
    CHANGED["$msg"]=1
  elif [[ "$msg" =~ ^remove|^drop|^delete|^deprecat ]]; then
    REMOVED["$msg"]=1
  else
    OTHER["$msg"]=1
  fi
done < <(git log "$RANGE" --pretty=format:"%s" --no-merges 2>/dev/null || echo "")

# ─── Output ─────────────────────────────────────────────────
if [[ "$FORMAT" == "json" ]]; then
  echo "{"
  echo '  "added": ['
  first=true; for k in "${!ADDED[@]}"; do $first || echo ","; printf '    "%s"' "$k"; first=false; done
  echo ""
  echo '  ],'
  echo '  "fixed": ['
  first=true; for k in "${!FIXED[@]}"; do $first || echo ","; printf '    "%s"' "$k"; first=false; done
  echo ""
  echo '  ],'
  echo '  "changed": ['
  first=true; for k in "${!CHANGED[@]}"; do $first || echo ","; printf '    "%s"' "$k"; first=false; done
  echo ""
  echo '  ],'
  echo '  "removed": ['
  first=true; for k in "${!REMOVED[@]}"; do $first || echo ","; printf '    "%s"' "$k"; first=false; done
  echo ""
  echo '  ]'
  echo "}"
else
  # Markdown CHANGELOG
  COMMIT_COUNT=0
  for k in "${!ADDED[@]}" "${!FIXED[@]}" "${!CHANGED[@]}" "${!REMOVED[@]}" "${!OTHER[@]}"; do
    ((COMMIT_COUNT++)) || true
  done

  if [[ $COMMIT_COUNT -eq 0 ]]; then
    echo "No commits found in range $RANGE" >&2
    exit 0
  fi

  # Header
  VERSION="Unreleased"
  TAG_FROM=$(echo "$RANGE" | sed 's/\.\..*//')
  TAG_TO=$(echo "$RANGE" | sed 's/.*\.\.//')
  [[ -n "$TAG_TO" && "$TAG_TO" != "HEAD" ]] && VERSION="$TAG_TO"
  [[ -n "$TAG_FROM" && "$TAG_FROM" != "HEAD" && "$TAG_FROM" != "." ]] && VERSION="$VERSION ($TAG_FROM..$TAG_TO)"
  [[ "$RANGE" == "HEAD" ]] && VERSION="Unreleased"

  {
    echo "## $VERSION"
    echo ""

    emit_section() {
      local title="$1" emoji="$2"
      local -n arr=$3
      if [[ ${#arr[@]} -gt 0 ]]; then
        echo "### ${emoji} ${title}"
        echo ""
        for k in "${!arr[@]}"; do
          echo "- $k"
        done
        echo ""
      fi
    }

    emit_section "Added" "🆕" ADDED
    emit_section "Fixed" "🐛" FIXED
    emit_section "Changed" "🔄" CHANGED
    emit_section "Removed" "🗑️" REMOVED

    # Anything that didn't fit goes in Other
    if [[ ${#OTHER[@]} -gt 0 ]]; then
      echo "### 📝 Other"
      echo ""
      for k in "${!OTHER[@]}"; do
        echo "- $k"
      done
      echo ""
    fi
  } > "$OUTPUT"

  echo "✓ Changelog written to $OUTPUT ($COMMIT_COUNT commits in range $RANGE)"
fi
