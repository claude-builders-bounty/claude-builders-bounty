#!/usr/bin/env bash
#
# install.sh -- two-step installer for the safe-bash pre-tool-use hook.
#
# Usage (from a clone of this repo):
#   bash hooks/safe-bash/install.sh
#
# What this does:
#   1. Copies hooks/safe-bash/ into ~/.claude/hooks/safe-bash/ and marks the
#      Python script executable.
#   2. Merges (or prints) the PreToolUse hook config so ~/.claude/settings.json
#      picks it up. If the file already exists, the script prints the snippet
#      you need to add and exits without overwriting anything.

set -euo pipefail

REPO_HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="${HOME}/.claude/hooks/safe-bash"
SETTINGS_FILE="${HOME}/.claude/settings.json"

# Step 1 — install the script files.
mkdir -p "${DEST_DIR}"
cp "${REPO_HOOK_DIR}/pre_tool_use.py" "${DEST_DIR}/pre_tool_use.py"
chmod +x "${DEST_DIR}/pre_tool_use.py"
echo "Installed pre_tool_use.py to ${DEST_DIR}"

# Step 2 — register the hook in settings.json.
read -r -d '' SNIPPET <<'EOF' || true
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "$HOME/.claude/hooks/safe-bash/pre_tool_use.py" }
        ]
      }
    ]
  }
}
EOF

if [[ ! -f "${SETTINGS_FILE}" ]]; then
  mkdir -p "$(dirname "${SETTINGS_FILE}")"
  echo "${SNIPPET}" > "${SETTINGS_FILE}"
  echo "Created ${SETTINGS_FILE} with PreToolUse hook registered."
else
  echo
  echo "${SETTINGS_FILE} already exists — not overwriting."
  echo "Merge this PreToolUse block into the existing JSON:"
  echo
  echo "${SNIPPET}"
fi

echo
echo "safe-bash hook installed. Test with:  bash ${REPO_HOOK_DIR}/test.sh"
