
Enter file contents here
#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh [--output CHANGELOG.md] [--since <ref>] [--unreleased]
#
# Flags:
#   --output FILE   Output file (default: CHANGELOG.md)
#   --since REF     Generate commits since this ref (default: last tag)
#   --unreleased    Label section as "Unreleased" instead of version
#   --help          Show this help
set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE=""
UNRELEASED=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT="$2"; shift 2 ;;
    --since)  SINCE="$2"; shift 2 ;;
    --unreleased) UNRELEASED=true; shift ;;
    --help)   sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# Resolve the starting ref: explicit --since, else last git tag, else all history.
if [[ -z "$SINCE" ]]; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -n "$LAST_TAG" ]]; then
    SINCE="$LAST_TAG"
  else
    SINCE=""
  fi
fi

# Determine version label.
if [[ "$UNRELEASED" == true ]]; then
  VERSION_LABEL="Unreleased"
elif [[ -n "${LAST_TAG:-}" ]]; then
  VERSION_LABEL="$LAST_TAG"
else
  VERSION_LABEL="Unreleased"
fi

DATE_LABEL=$(date -u +%Y-%m-%d)

# Collect commits. Use --first-parent to avoid noisy merge commits unless needed.
if [[ -n "$SINCE" ]]; then
  COMMITS=$(git log "${SINCE}..HEAD" --pretty=format:"%s" 2>/dev/null || echo "")
else
  COMMITS=$(git log --pretty=format:"%s" 2>/dev/null || echo "")
fi

if [[ -z "$COMMITS" ]]; then
  echo "No commits found since '${SINCE:-beginning}'." >&2
  exit 0
fi

# Categorize commits into Added / Fixed / Changed / Removed.
# Conventional commits: feat=Added, fix=Fixed, perf/refactor=Changed,
# chore/build/ci=Changed, docs=Changed, BREAKING=Changed, revert=Removed.
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')

  if [[ "$lower" =~ ^feat(\(|\!): ]] || [[ "$lower" =~ ^add ]]; then
    ADDED+=("$line")
  elif [[ "$lower" =~ ^fix(\()? ]] || [[ "$lower" =~ ^bugfix ]] || [[ "$lower" =~ ^hotfix ]]; then
    FIXED+=("$line")
  elif [[ "$lower" =~ ^(removed|delete|drop)(\(|\!): ]] || [[ "$lower" =~ ^remove ]]; then
    REMOVED+=("$line")
  elif [[ "$lower" =~ ^(chore|build|ci|refactor|perf|docs|style|test|revert|change)(\(|\!): ]] || [[ "$lower" =~ ^changed ]]; then
    CHANGED+=("$line")
  else
    # Uncategorised commits go to Changed by default.
    CHANGED+=("$line")
  fi
done <<< "$COMMITS"

# Write the changelog.
{
  echo "## ${VERSION_LABEL} — ${DATE_LABEL}"
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    echo ""
    for c in "${ADDED[@]}"; do echo "- $c"; done
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    echo ""
    for c in "${FIXED[@]}"; do echo "- $c"; done
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    echo ""
    for c in "${CHANGED[@]}"; do echo "- $c"; done
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    echo ""
    for c in "${REMOVED[@]}"; do echo "- $c"; done
    echo ""
  fi
} > "$OUTPUT"

echo "Wrote ${OUTPUT} (${VERSION_LABEL}, $(echo "$COMMITS" | wc -l | tr -d ' ') commits)."
