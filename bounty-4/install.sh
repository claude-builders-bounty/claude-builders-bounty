#!/bin/sh
set -eu
DEST="${HOME}/.local/bin"
mkdir -p "$DEST"
SRC=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ln -sf "$SRC/claude-review" "$DEST/claude-review"
chmod +x "$SRC/claude-review" "$SRC/claude_review.py"
printf 'Installed %s\n' "$DEST/claude-review"
printf 'Ensure %s is on PATH.\n' "$DEST"
