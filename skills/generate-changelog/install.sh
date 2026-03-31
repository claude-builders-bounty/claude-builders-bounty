#!/bin/bash
# Install generate-changelog skill

set -e

SKILL_DIR="$HOME/.claude/skills/generate-changelog"

echo "Installing generate-changelog skill..."

# Create skill directory
mkdir -p "$SKILL_DIR"

# Copy files
cp "$(dirname "$0")/SKILL.md" "$SKILL_DIR/"
cp "$(dirname "$0")/changelog.sh" "$SKILL_DIR/"

# Make executable
chmod +x "$SKILL_DIR/changelog.sh"

echo "✓ Installed to $SKILL_DIR"
echo ""
echo "Usage:"
echo "  /generate-changelog    # In Claude Code"
echo "  bash ~/.claude/skills/generate-changelog/changelog.sh    # Direct"