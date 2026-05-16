#!/bin/sh
# install.sh — Install claude-review in one command
# Usage: curl -sSL https://... | sh
# Or: bash install.sh

set -e

INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "$INSTALL_DIR"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="${SCRIPT_DIR}/claude_review.py"
DEST="${INSTALL_DIR}/claude-review"

if [ -f "$SRC" ]; then
    cp "$SRC" "$DEST"
else
    # Remote install — download from GitHub
    echo "Downloading claude-review..."
    curl -sfL "https://raw.githubusercontent.com/claude-builders-bounty/claude-review/main/claude_review.py" \
        -o "$DEST" 2>/dev/null || {
        echo "❌ Download failed. Install manually."
        exit 1
    }
fi

chmod +x "$DEST"

# Add to PATH if not already there
case ":$PATH:" in
    *:"$INSTALL_DIR":*) ;;
    *)
        echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "${HOME}/.bashrc"
        echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "${HOME}/.zshrc" 2>/dev/null || true
        echo "✅ Added $INSTALL_DIR to PATH in ~/.bashrc"
        ;;
esac

echo "✅ claude-review installed to $DEST"
echo "   Run: claude-review --pr https://github.com/owner/repo/pull/123"
echo "   Or:  claude-review --help"

# Check Python availability
python3 --version >/dev/null 2>&1 && echo "✅ Python 3 found: $(python3 --version 2>&1)"
PYEOF