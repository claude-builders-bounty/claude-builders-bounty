#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$HOME/.local/bin"
mkdir -p "$TARGET_DIR"

install -m 755 "$SOURCE_DIR/claude-review" "$TARGET_DIR/claude-review"
install -m 755 "$SOURCE_DIR/claude_review.py" "$TARGET_DIR/claude_review.py"

echo "Installed: $TARGET_DIR/claude-review"
if [[ ":$PATH:" != *":$TARGET_DIR:"* ]]; then
  echo "Add $TARGET_DIR to PATH to run 'claude-review' directly."
fi
