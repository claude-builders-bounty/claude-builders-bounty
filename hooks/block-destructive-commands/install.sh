#!/usr/bin/env bash
# Installer for the block-destructive PreToolUse hook (Claude Code).
#
# One-liner:   curl -fsSL <RAW_URL>/install.sh | bash
# From clone:  bash install.sh
#
# Copies the hook to $HOME/.claude/hooks/ and merges the PreToolUse entry into
# $HOME/.claude/settings.json (keeping a .bak of the previous file).
set -eu

SRC_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd || echo .)"
HOOK_DIR="${CLAUDE_HOOK_DIR:-$HOME/.claude/hooks}"
SETTINGS="${CLAUDE_SETTINGS:-$HOME/.claude/settings.json}"
RAW_BASE="${RAW_BASE:-https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-destructive-commands}"
HOOK_PATH="$HOOK_DIR/block-destructive.sh"

mkdir -p "$HOOK_DIR" "$(dirname "$SETTINGS")"

if [ -f "$SRC_DIR/block-destructive.sh" ]; then
  cp "$SRC_DIR/block-destructive.sh" "$HOOK_PATH"
else
  curl -fsSL "$RAW_BASE/block-destructive.sh" -o "$HOOK_PATH"
fi
chmod +x "$HOOK_PATH"

# Merge the hook entry into settings.json without touching existing config.
MERGE_PY='
import json, os, shutil, sys
settings, hook_path = sys.argv[1], sys.argv[2]
data = {}
if os.path.exists(settings) and os.path.getsize(settings) > 0:
    shutil.copyfile(settings, settings + ".bak")
    with open(settings) as fh:
        data = json.load(fh)
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
for group in pre:
    for h in group.get("hooks", []):
        if h.get("command") == hook_path:
            print("already installed; settings.json untouched")
            sys.exit(0)
pre.append({
    "matcher": "Bash|PowerShell",
    "hooks": [{"type": "command", "command": hook_path, "args": []}],
})
with open(settings, "w") as fh:
    json.dump(data, fh, indent=2)
    fh.write("\n")
print("installed")
'
MERGE_JS='
const fs = require("fs");
const [settings, hookPath] = process.argv.slice(1);
let data = {};
if (fs.existsSync(settings) && fs.statSync(settings).size > 0) {
  fs.copyFileSync(settings, settings + ".bak");
  data = JSON.parse(fs.readFileSync(settings, "utf8"));
}
data.hooks = data.hooks || {};
data.hooks.PreToolUse = data.hooks.PreToolUse || [];
for (const group of data.hooks.PreToolUse) {
  for (const h of group.hooks || []) {
    if (h.command === hookPath) { console.log("already installed; settings.json untouched"); process.exit(0); }
  }
}
data.hooks.PreToolUse.push({ matcher: "Bash|PowerShell", hooks: [{ type: "command", command: hookPath, args: [] }] });
fs.writeFileSync(settings, JSON.stringify(data, null, 2) + "\n");
console.log("installed");
'

if command -v python3 >/dev/null 2>&1; then
  python3 -c "$MERGE_PY" "$SETTINGS" "$HOOK_PATH"
elif command -v node >/dev/null 2>&1; then
  node -e "$MERGE_JS" "$SETTINGS" "$HOOK_PATH"
else
  echo "Necesitas python3 o node para fusionar la configuracion."
  echo "Anade esto a $SETTINGS manualmente:"
  printf '{"hooks":{"PreToolUse":[{"matcher":"Bash|PowerShell","hooks":[{"type":"command","command":"%s","args":[]}]}]}}\n' "$HOOK_PATH"
  exit 0
fi

echo
echo "Hook instalado en: $HOOK_PATH"
echo "Configurado en:    $SETTINGS"
echo "Prueba el bloqueo: echo '{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"rm -rf /tmp/x\"},\"cwd\":\"$PWD\"}' | $HOOK_PATH"
echo "Log de bloqueos:   $HOOK_DIR/blocked.log"
echo "Reinicia Claude Code para que cargue la configuracion."
