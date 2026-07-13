#!/usr/bin/env bash
set -euo pipefail

# ==========================================================================
# Claude Code Safety Hook — Installer
# ==========================================================================
# Installs the pre-tool-use safety hook into ~/.claude/hooks/ and
# configures it in ~/.claude/settings.json.
#
# Usage:
#   curl -sSL <raw-url>/install.sh | bash
#   # or
#   ./install.sh
# ==========================================================================

HOOK_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colours
RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ------------------------------------------------------------------
# 1. Pre-flight checks
# ------------------------------------------------------------------
if ! command -v python3 &>/dev/null; then
    error "python3 is required but not found. Please install Python 3.8+."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Python version: $PYTHON_VERSION"

# ------------------------------------------------------------------
# 2. Create hooks directory
# ------------------------------------------------------------------
mkdir -p "$HOOK_DIR"
ok "Hooks directory ready: $HOOK_DIR"

# ------------------------------------------------------------------
# 3. Copy files
# ------------------------------------------------------------------
cp "$SCRIPT_DIR/pre_tool_use_hook.py" "$HOOK_DIR/pre_tool_use_hook.py"
chmod +x "$HOOK_DIR/pre_tool_use_hook.py"
ok "Installed pre_tool_use_hook.py"

if [[ -f "$SCRIPT_DIR/hook_config.json" ]]; then
    if [[ -f "$HOOK_DIR/hook_config.json" ]]; then
        warn "hook_config.json already exists — keeping your version"
        warn "New config saved as hook_config.json.new for reference"
        cp "$SCRIPT_DIR/hook_config.json" "$HOOK_DIR/hook_config.json.new"
    else
        cp "$SCRIPT_DIR/hook_config.json" "$HOOK_DIR/hook_config.json"
        ok "Installed hook_config.json"
    fi
fi

# ------------------------------------------------------------------
# 4. Configure Claude Code settings
# ------------------------------------------------------------------
HOOK_ENTRY=$(cat <<'JSONEOF'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use_hook.py"
          }
        ]
      }
    ]
  }
}
JSONEOF
)

if [[ -f "$SETTINGS_FILE" ]]; then
    # Check if hooks are already configured
    if python3 -c "
import json, sys
with open('$SETTINGS_FILE') as f:
    d = json.load(f)
hooks = d.get('hooks', {}).get('PreToolUse', [])
for h in hooks:
    for hh in h.get('hooks', []):
        if 'pre_tool_use_hook' in hh.get('command', ''):
            sys.exit(0)
sys.exit(1)
" 2>/dev/null; then
        ok "Hook already configured in settings.json — skipping"
    else
        # Merge hook into existing settings
        python3 -c "
import json
with open('$SETTINGS_FILE') as f:
    settings = json.load(f)
hook_cfg = json.loads('''$HOOK_ENTRY''')
if 'hooks' not in settings:
    settings['hooks'] = {}
if 'PreToolUse' not in settings['hooks']:
    settings['hooks']['PreToolUse'] = []
settings['hooks']['PreToolUse'].extend(hook_cfg['hooks']['PreToolUse'])
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=2)
"
        ok "Updated $SETTINGS_FILE with hook configuration"
    fi
else
    # Create new settings file
    mkdir -p "$(dirname "$SETTINGS_FILE")"
    echo "$HOOK_ENTRY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(data, f, indent=2)
"
    ok "Created $SETTINGS_FILE with hook configuration"
fi

# ------------------------------------------------------------------
# 5. Verify
# ------------------------------------------------------------------
echo ""
info "Running quick verification..."
TEST_INPUT='{"tool_name":"Bash","tool_input":{"command":"rm -rf /"},"project_path":"/tmp/test"}'
RESULT=$(echo "$TEST_INPUT" | python3 "$HOOK_DIR/pre_tool_use_hook.py" 2>/dev/null || true)

if echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['hookSpecificOutput']['permissionDecision']=='deny'" 2>/dev/null; then
    ok "Verification passed — dangerous commands are blocked!"
else
    error "Verification failed — please check the installation"
    exit 1
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅  Safety hook installed successfully!                 ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Hook:   ~/.claude/hooks/pre_tool_use_hook.py           ║${NC}"
echo -e "${GREEN}║  Config: ~/.claude/hooks/hook_config.json               ║${NC}"
echo -e "${GREEN}║  Log:    ~/.claude/hooks/blocked.log                    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
info "Edit hook_config.json to customise rules, whitelists, and logging."
info "Restart Claude Code to activate the hook."
