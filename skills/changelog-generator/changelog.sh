#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

cat > "$OUTPUT" <<'EOF'
# Changelog

EOF

for section in "Added" "Fixed" "Changed" "Removed"; do
  lcase=$(echo "$section" | tr '[:upper:]' '[:lower:]')
  commits=$(git log "$LAST_TAG"..HEAD --pretty=format:"- %s" --grep="$lcase" 2>/dev/null || true)
  if [ -n "$commits" ]; then
    echo -e "\n## $section\n" >> "$OUTPUT"
    echo "$commits" >> "$OUTPUT"
  fi
done

echo "Generated $OUTPUT"
