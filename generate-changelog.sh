#!/usr/bin/env bash
set -euo pipefail
# generate-changelog.sh — 生成结构化 CHANGELOG.md
# 用法: bash changelog.sh [--tag <since-tag>] [--file CHANGELOG.md]
# 自动依据 repo 语境选择 python 或纯 bash (logs via git)

SINCE_TAG="${1:-}"
FILE="CHANGELOG.md"
if [[ "${2:-}" != "" ]]; then FILE="$2"; fi

if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo 'HEAD~0')"
  if [[ "$SINCE_TAG" == 'HEAD~0' ]]; then SINCE_TAG=""; fi
fi

RANGE="${SINCE_TAG:+$SINCE_TAG..}HEAD"

entries_added=()
entries_fixed=()
entries_changed=()
entries_removed=()

prefix_of() {
  local l="${1,,}"
  case "$l" in
    fix\(*|fix:*|fixes:*|bug:*|bugfix:*|hotfix:*|patch:*|fixes\(*) echo added_fixed ;;
    feat\(*|feat:*|feature:*|feature\(*|add:*|add\(*|new:*|implement:*|support:*) echo added_added ;;
    remove\(*|remove:*|drop:*|delete:*|deprecate:*) echo added_removed ;;
    *) echo added_changed ;;
  esac
}

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  case "$(prefix_of "$line")" in
    added_fixed)   entries_fixed+=("$line") ;;
    added_added)   entries_added+=("$line") ;;
    added_removed) entries_removed+=("$line") ;;
    added_changed) entries_changed+=("$line") ;;
  esac
done < <(git log --pretty=format:'%s' "$RANGE" ; echo)

emit_section() {
  local title="$1"; shift
  echo ""
  echo "### $title"
  for e in "$@"; do echo "- $e"; done
}

cat > "$FILE" <<EOF
# Changelog

All notable changes since \`${SINCE_TAG:-beginning}\`.

## $(date +%F)

EOF

if ((${#entries_added[@]})); then emit_section "Added" "${entries_added[@]}" >> "$FILE"; fi
if ((${#entries_fixed[@]})); then emit_section "Fixed" "${entries_fixed[@]}" >> "$FILE"; fi
if ((${#entries_changed[@]})); then emit_section "Changed" "${entries_changed[@]}" >> "$FILE"; fi
if ((${#entries_removed[@]})); then emit_section "Removed" "${entries_removed[@]}" >> "$FILE"; fi
if (( ${#entries_added[@]} + ${#entries_fixed[@]} + ${#entries_changed[@]} + ${#entries_removed[@]} == 0 )); then
  echo "- No notable changes." >> "$FILE"
fi

echo "→ $FILE ($(grep -c '^- ' "$FILE") entries)"