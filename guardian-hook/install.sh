#!/usr/bin/env bash
# Install the Guardian pre-tool-use hook for Claude Code
# Installs in ~/.claude/hooks/ and registers in ~/.claude/settings.json

set -euo pipefail

HOOKS_DIR="${HOME}/.claude/hooks"
SETTINGS_FILE="${HOME}/.claude/settings.json"
SCRIPT_NAME="pre-tool-use-guardian.py"
SCRIPT_SRC="$(cd "$(dirname "$0")" && pwd)/hooks/${SCRIPT_NAME}"
SCRIPT_DEST="${HOOKS_DIR}/${SCRIPT_NAME}"

echo "=== Claude Code Guardian Hook Installer ==="
echo ""

# 1. Create hooks directory
mkdir -p "${HOOKS_DIR}"

# 2. Copy the hook script
cp "${SCRIPT_SRC}" "${SCRIPT_DEST}"
chmod +x "${SCRIPT_DEST}"
echo "✓ Installed hook script to ${SCRIPT_DEST}"

# 3. Register hook in settings.json
HOOK_ENTRY=$(cat <<'ENDJSON'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use-guardian.py"
          }
        ]
      }
    ]
  }
}
ENDJSON
)

if [ -f "${SETTINGS_FILE}" ]; then
    # Merge the hook into existing settings
    python3 -c "
import json, sys

with open('${SETTINGS_FILE}') as f:
    settings = json.load(f)

hook = json.loads('''${HOOK_ENTRY}''')

# Merge hooks.PreToolUse
if 'hooks' not in settings:
    settings['hooks'] = {}
if 'PreToolUse' not in settings['hooks']:
    settings['hooks']['PreToolUse'] = []

# Check if our hook is already registered
existing_commands = []
for h in settings['hooks']['PreToolUse']:
    for sub in h.get('hooks', []):
        existing_commands.append(sub.get('command', ''))

new_command = hook['hooks']['PreToolUse'][0]['hooks'][0]['command']
if any(new_command in c for c in existing_commands):
    print('⚠ Hook already registered in settings.json, skipping.')
    sys.exit(0)

# Add our hook
settings['hooks']['PreToolUse'].extend(hook['hooks']['PreToolUse'])

with open('${SETTINGS_FILE}', 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')

print('✓ Hook registered in ${SETTINGS_FILE}')
"
else
    # Create new settings file
    echo "${HOOK_ENTRY}" | python3 -c "
import json, sys
data = json.load(sys.stdin)
with open('${SETTINGS_FILE}', 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
"
    echo "✓ Created ${SETTINGS_FILE} with hook registration"
fi

echo ""
echo "=== Installation Complete ==="
echo "The Guardian will now block:"
echo "  • rm -rf (recursive force removal)"
echo "  • git push --force / --force-with-lease"
echo "  • DROP TABLE / DROP DATABASE"
echo "  • TRUNCATE TABLE"
echo "  • DELETE FROM without WHERE clause"
echo ""
echo "Blocked attempts are logged to: ${HOOKS_DIR}/blocked.log"
echo ""
echo "To uninstall: rm ${SCRIPT_DEST}"
echo "               (remove PreToolUse hook from ${SETTINGS_FILE})"
