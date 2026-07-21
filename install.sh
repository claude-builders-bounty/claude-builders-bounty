#!/bin/bash
set -euo pipefail

mkdir -p "$HOME/.claude/hooks"
cp "$(dirname "$0")/pre-tool-use-hook.sh" "$HOME/.claude/hooks/"
chmod +x "$HOME/.claude/hooks/pre-tool-use-hook.sh"
echo ""
echo "  Hook installed to ~/.claude/hooks/pre-tool-use-hook.sh"
echo ""
echo "  Next, add to ~/.claude/settings.json or .claude/settings.json:"
echo ""
echo '  {'
echo '    "hooks": {'
echo '      "PreToolUse": ['
echo '        {'
echo '          "matcher": "Bash",'
echo '          "hooks": ['
echo '            {'
echo '              "type": "command",'
echo '              "command": "'"$HOME/.claude/hooks/pre-tool-use-hook.sh"'"'
echo '            }'
echo '          ]'
echo '        }'
echo '      ]'
echo '    }'
echo '  }'
echo ""
echo "  Done."
