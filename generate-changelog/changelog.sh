#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history since the last tag.
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${ROOT_DIR}" ]]; then
  echo "error: not inside a git repository" >&2
  exit 1
fi
cd "$ROOT_DIR"

OUT_FILE="${1:-CHANGELOG.md}"
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  HEADER_NOTE="Changes since \`${LAST_TAG}\`"
else
  RANGE="HEAD"
  HEADER_NOTE="All commits (no tags found)"
fi

# Collect subject lines only
mapfile -t COMMITS < <(git log "$RANGE" --pretty=format:'%s' --no-merges)

added=(); fixed=(); changed=(); removed=()

classify() {
  local s="$1"
  local lower
  lower="$(printf '%s' "$s" | tr '[:upper:]' '[:lower:]')"
  if [[ "$lower" =~ ^(remove|removed|delete|deleted|drop|dropped)([:[:space:]-]|$) ]] || [[ "$lower" =~ (^|[^a-z])remove(d)?([^a-z]|$) ]]; then
    removed+=("$s"); return
  fi
  if [[ "$lower" =~ ^(fix|fixed|bugfix|hotfix|patch)([:[:space:]-]|$) ]] || [[ "$lower" =~ (^|[^a-z])fix(es|ed)?([^a-z]|$) ]]; then
    fixed+=("$s"); return
  fi
  if [[ "$lower" =~ ^(add|added|feat|feature|implement|implemented|create|created|introduce|introduced)([:[:space:]-]|$) ]]; then
    added+=("$s"); return
  fi
  if [[ "$lower" =~ ^(change|changed|update|updated|refactor|improve|improved|chore|docs|style|perf)([:[:space:]-]|$) ]]; then
    changed+=("$s"); return
  fi
  # Conventional commit prefixes
  if [[ "$lower" =~ ^feat(\(.+\))?(!)?: ]]; then added+=("$s"); return; fi
  if [[ "$lower" =~ ^fix(\(.+\))?(!)?: ]]; then fixed+=("$s"); return; fi
  if [[ "$lower" =~ ^(refactor|perf|style|docs|chore|build|ci)(\(.+\))?(!)?: ]]; then changed+=("$s"); return; fi
  if [[ "$lower" =~ ^revert ]]; then removed+=("$s"); return; fi
  changed+=("$s")
}

for c in "${COMMITS[@]:-}"; do
  [[ -z "$c" ]] && continue
  classify "$c"
done

today="$(date -u +%Y-%m-%d)"
{
  echo "# Changelog"
  echo
  echo "## Unreleased ($today)"
  echo
  echo "_${HEADER_NOTE}_"
  echo
  echo "### Added"
  if ((${#added[@]})); then for i in "${added[@]}"; do echo "- $i"; done; else echo "- _(none)_"; fi
  echo
  echo "### Fixed"
  if ((${#fixed[@]})); then for i in "${fixed[@]}"; do echo "- $i"; done; else echo "- _(none)_"; fi
  echo
  echo "### Changed"
  if ((${#changed[@]})); then for i in "${changed[@]}"; do echo "- $i"; done; else echo "- _(none)_"; fi
  echo
  echo "### Removed"
  if ((${#removed[@]})); then for i in "${removed[@]}"; do echo "- $i"; done; else echo "- _(none)_"; fi
  echo
} > "$OUT_FILE"

echo "Wrote $OUT_FILE ($HEADER_NOTE; commits: ${#COMMITS[@]})"
