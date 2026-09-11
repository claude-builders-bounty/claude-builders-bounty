#!/usr/bin/env bash
# Generate structured CHANGELOG.md from git history since last tag (or SINCE_REF).
set -euo pipefail

STDOUT_ONLY=0
REPO_DIR="${REPO_DIR:-.}"
OUT_FILE="${OUT_FILE:-CHANGELOG.md}"

for arg in "$@"; do
  case "$arg" in
    --stdout-only) STDOUT_ONLY=1 ;;
    --help|-h)
      echo "Usage: bash scripts/changelog.sh [--stdout-only]"
      echo "Env: REPO_DIR SINCE_REF OUT_FILE"
      exit 0
      ;;
  esac
done

cd "$REPO_DIR"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not a git repository: $REPO_DIR" >&2
  exit 1
fi

if [[ -n "${SINCE_REF:-}" ]]; then
  RANGE_START="$SINCE_REF"
  RANGE_NOTE="since ref $SINCE_REF"
else
  if LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
    RANGE_START="$LAST_TAG"
    RANGE_NOTE="since tag $LAST_TAG"
  else
    RANGE_START=$(git rev-list --max-parents=0 HEAD | tail -n1)
    RANGE_NOTE="full history (no tags found); lower bound first commit"
  fi
fi

mapfile -t COMMITS < <(git log --no-merges --pretty=format:'%h%x09%s' "${RANGE_START}..HEAD" 2>/dev/null || true)

added=(); fixed=(); changed=(); removed=(); other=()

categorize() {
  local msg="$1"
  local lower
  lower=$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')
  if [[ "$lower" =~ (^|[^a-z])(add|added|feat|feature|implement|introduce|create|new)([^a-z]|$) ]] || [[ "$lower" == feat:* ]] || [[ "$lower" == feature:* ]]; then
    echo added
  elif [[ "$lower" =~ (^|[^a-z])(fix|fixed|bug|bugfix|hotfix|patch|resolve|repair)([^a-z]|$) ]] || [[ "$lower" == fix:* ]]; then
    echo fixed
  elif [[ "$lower" =~ (^|[^a-z])(remove|removed|delete|deleted|drop|dropped|deprecate)([^a-z]|$) ]] || [[ "$lower" == remove:* ]] || [[ "$lower" == chore\(remove\):* ]]; then
    echo removed
  elif [[ "$lower" =~ (^|[^a-z])(change|changed|update|updated|refactor|improve|rename|move|modify|chore|docs|style|perf)([^a-z]|$) ]] || [[ "$lower" == chore:* ]] || [[ "$lower" == refactor:* ]] || [[ "$lower" == docs:* ]]; then
    echo changed
  else
    echo other
  fi
}

for line in "${COMMITS[@]:-}"; do
  [[ -z "$line" ]] && continue
  hash="${line%%$'\t'*}"
  subj="${line#*$'\t'}"
  catg=$(categorize "$subj")
  entry="- ${subj} (${hash})"
  case "$catg" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    removed) removed+=("$entry") ;;
    changed) changed+=("$entry") ;;
    *) other+=("$entry") ;;
  esac
done

# Uncategorized -> Changed (keep changelog complete)
if ((${#other[@]})); then
  changed+=("${other[@]}")
fi

DATE=$(date -u +%Y-%m-%d)
HEADER_REF="$RANGE_START"
if [[ "$RANGE_NOTE" == full* ]]; then HEADER_REF="Unreleased"; fi

{
  echo "# Changelog"
  echo
  echo "## ${HEADER_REF} → HEAD (${DATE})"
  echo
  echo "_Generated ${RANGE_NOTE}._"
  echo
  echo "### Added"
  if ((${#added[@]})); then printf '%s\n' "${added[@]}"; else echo "- _(none)_"; fi
  echo
  echo "### Fixed"
  if ((${#fixed[@]})); then printf '%s\n' "${fixed[@]}"; else echo "- _(none)_"; fi
  echo
  echo "### Changed"
  if ((${#changed[@]})); then printf '%s\n' "${changed[@]}"; else echo "- _(none)_"; fi
  echo
  echo "### Removed"
  if ((${#removed[@]})); then printf '%s\n' "${removed[@]}"; else echo "- _(none)_"; fi
  echo
} > /tmp/changelog_out_$$.md

if [[ "$STDOUT_ONLY" -eq 1 ]]; then
  cat /tmp/changelog_out_$$.md
else
  # Prepend to existing CHANGELOG if present
  if [[ -f "$OUT_FILE" ]]; then
    {
      cat /tmp/changelog_out_$$.md
      echo
      cat "$OUT_FILE"
    } > /tmp/changelog_merged_$$.md
    mv /tmp/changelog_merged_$$.md "$OUT_FILE"
  else
    cp /tmp/changelog_out_$$.md "$OUT_FILE"
  fi
  cat /tmp/changelog_out_$$.md
  echo "Wrote $OUT_FILE" >&2
fi
rm -f /tmp/changelog_out_$$.md
