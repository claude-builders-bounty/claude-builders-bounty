# Claude Code PreToolUse Hook Installer for Windows PowerShell
$ErrorActionPreference = "Stop"

$HookDir = Join-Path $HOME ".claude\hooks"
if (!(Test-Path $HookDir)) {
    New-Item -ItemType Directory -Path $HookDir -Force | Out-Null
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Copy-Item "$ScriptDir\hooks\pre-tool-use\block_destructive_commands.py" "$HookDir\block_destructive_commands.py" -Force

Write-Host "✅ Claude Code destructive command hook successfully installed to $HookDir\block_destructive_commands.py"
Write-Host "Blocked commands will be logged to $HookDir\blocked.log"
