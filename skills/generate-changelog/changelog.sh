#!/usr/bin/env bash
# changelog.sh — Generate CHANGELOG.md dari git history (Conventional Commits)
set -euo pipefail

REPO="${1:-.}"
OUT="${2:-CHANGELOG.md}"
cd "$REPO"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then RANGE="${LAST_TAG}..HEAD"; else RANGE="HEAD"; fi

declare -A CAT
order=(Added Fixed Changed Removed)
for k in "${order[@]}"; do CAT[$k]=""; done

classify() {
  local subj="$1"
  local low; low="$(printf '%s' "$subj" | tr '[:upper:]' '[:lower:]')"
  # Ambil prefix konvensional di awal baris saja: type(scope)!?: desc
  local prefix=""
  if [[ "$low" =~ ^([a-z]+)(\([^\)]*\))?!?: ]]; then
    prefix="${BASH_REMATCH[1]}"
  else
    # tanpa prefix: pakai kata kunci awal kalimat saja
    firstword="${low%% *}"
    prefix="$firstword"
  fi
  case "$prefix" in
    feat|feature|add|new|added) echo "Added";;
    fix|bugfix|hotfix|fixed)    echo "Fixed";;
    refactor|style|change|changed|update|perf|perf:) echo "Changed";;
    remove|removed|delete|rm|deprecat|deprecated) echo "Removed";;
    *) echo "Changed";;
  esac
}

while IFS=$'\t' read -r hash subject; do
  [ -z "${subject:-}" ] && continue
  case "$subject" in Merge*) continue;; esac
  target="$(classify "$subject")"
  clean="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//')"
  CAT[$target]+="- ${clean} ([${hash:0:7}](../../commit/${hash}))"$'\n'
done < <( { git log --no-merges --pretty=format:'%H%x09%s' $RANGE 2>/dev/null || true; echo; } )

{
  echo "# Changelog"
  echo
  echo "## [Unreleased]"
  echo
  any=0
  for k in "${order[@]}"; do
    if [ -n "${CAT[$k]}" ]; then
      any=1; echo "### $k"; printf '%s' "${CAT[$k]}"; echo
    fi
  done
  [ "$any" -eq 0 ] && echo "_Tidak ada perubahan._"
} > "$OUT"

echo "CHANGELOG ditulis ke $OUT"
