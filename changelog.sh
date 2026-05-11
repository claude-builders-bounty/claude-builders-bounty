#!/bin/bash
OUTPUT="${1:-CHANGELOG.md}"
SINCE="${2:-$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)}"
if [ ! -d .git ]; then echo "Error: not a git repo"; exit 1; fi
echo "# Changelog" > "$OUTPUT"; echo "" >> "$OUTPUT"; echo "All notable changes since ${SINCE}." >> "$OUTPUT"; echo "" >> "$OUTPUT"
write_section() { local h="$1" p="$2"; local c=$(git log "$SINCE"..HEAD --pretty=format:"%s" --grep="$p" 2>/dev/null); if [ -n "$c" ]; then echo "## $h" >> "$OUTPUT"; echo "" >> "$OUTPUT"; echo "$c" | while IFS= read -r l; do local cl=$(echo "$l" | sed -E 's/^(feat|fix|chore|docs|refactor|perf|test|style|build|ci|revert)(\(.*\))?!?: *//'); echo "- $cl" >> "$OUTPUT"; done; echo "" >> "$OUTPUT"; fi; }
write_section "Added" "^feat"; write_section "Fixed" "^fix"; write_section "Changed" "^(refactor|perf|chore|style)"; write_section "Removed" "^revert"
echo "Changelog generated at $OUTPUT"
