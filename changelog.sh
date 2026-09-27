#!/usr/bin/env bash
# changelog.sh — structured CHANGELOG.md from git history (bash 3.2+, no deps).
#   bash changelog.sh [--since TAG] [--version VER] [--out FILE] [--repo DIR]
#                     [--preview] [--append]
# Categories: Breaking / Added / Fixed / Changed / Removed (conventional-commit
# prefixes). Fail-closed: unknown --since or empty range exits 1, writes nothing.
set -uo pipefail

SINCE="" VER="Unreleased" OUT="CHANGELOG.md" REPO="." PREVIEW=0 APPEND=0
while [[ $# -gt 0 ]]; do case "$1" in
  --since) SINCE="$2"; shift 2;;
  --version) VER="$2"; shift 2;;
  --out) OUT="$2"; shift 2;;
  --repo) REPO="$2"; shift 2;;
  --preview) PREVIEW=1; shift;;
  --append) APPEND=1; shift;;
  *) echo "usage: bash changelog.sh [--since TAG] [--version VER] [--out FILE] [--repo DIR] [--preview] [--append]" >&2; exit 1;;
esac done

cd "$REPO"
git rev-parse --git-dir >/dev/null 2>&1 || { echo "error: not a git repo: $REPO" >&2; exit 1; }

if [[ -z "$SINCE" ]]; then
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi
if [[ -n "$SINCE" ]] && ! git rev-parse --verify -q "$SINCE" >/dev/null; then
  echo "error: unknown tag/ref: $SINCE" >&2; exit 1
fi
RANGE="HEAD"; [[ -n "$SINCE" ]] && RANGE="$SINCE..HEAD"

TMP=$(mktemp)
git log "$RANGE" --pretty=format:'%H %s' > "$TMP" 2>/dev/null || true
N=$(grep -c . "$TMP" || true)
if [[ "$N" -eq 0 ]]; then echo "error: no commits in range $RANGE" >&2; rm -f "$TMP"; exit 1; fi

breaking=(); added=(); fixed=(); changed=(); removed=()
set +u  # bash 3.2: empty-array expansion under set -u
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  sha=${line%% *}; subj=${line#* }; short=$(git rev-parse --short "$sha" 2>/dev/null || echo "${sha:0:7}")
  entry="$subj ($short)"
  low=$(echo "$subj" | tr '[:upper:]' '[:lower:]')
  if [[ "$low" == *"breaking change"* ]] || echo "$low" | grep -Eq '^[a-z]+(\([^)]*\))?!:'; then
    breaking+=("$entry")
  else
    case "$low" in
      feat*|add*|new*|*" new "*) added+=("$entry");;
      fix*|bug*|hotfix*|patch*|security*|cve*) fixed+=("$entry");;
      remove*|delete*|drop*|deprecat*) removed+=("$entry");;
      *) changed+=("$entry");;
    esac
  fi
done < "$TMP"
rm -f "$TMP"

DATE=$(date -u +%F)
print_sec() {
  local name="$1"; shift
  echo "### $name"
  if [[ $# -eq 0 ]]; then echo "- (none)"; else local i; for i in "$@"; do echo "- $i"; done; fi
  echo ""
}
TOTAL=$((${#breaking[@]} + ${#added[@]} + ${#fixed[@]} + ${#changed[@]} + ${#removed[@]}))
BODY=$( {
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project. Format follows Keep a Changelog."
  echo ""
  echo "## [$VER] - $DATE ($TOTAL commits since ${SINCE:-beginning})"
  echo ""
  print_sec "Breaking Changes" "${breaking[@]}"
  print_sec "Added" "${added[@]}"
  print_sec "Fixed" "${fixed[@]}"
  print_sec "Changed" "${changed[@]}"
  print_sec "Removed" "${removed[@]}"
} )
set -u

if [[ $PREVIEW -eq 1 ]]; then echo "$BODY"; exit 0; fi
if [[ $APPEND -eq 1 && -f "$OUT" ]]; then
  OLD=$(grep -v '^# Changelog' "$OUT" | grep -v '^All notable changes' || true)
  printf '%s\n%s\n' "$BODY" "$OLD" > "$OUT"
else
  printf '%s\n' "$BODY" > "$OUT"
fi
echo "wrote $TOTAL commits (B:${#breaking[@]} A:${#added[@]} F:${#fixed[@]} C:${#changed[@]} R:${#removed[@]}) -> $OUT"
