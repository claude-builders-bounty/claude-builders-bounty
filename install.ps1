# Windows PowerShell Installer for Claude Code PreToolUse Safety Hook
$ErrorActionPreference = "Stop"

$HooksDir = Join-Path $HOME ".claude\hooks"
if (-not (Test-Path $HooksDir)) {
    New-Item -ItemType Directory -Path $HooksDir -Force | Out-Null
}

$Dest = Join-Path $HooksDir "pre_tool_use_safety.py"
Copy-Item -Path "hooks\pre_tool_use_safety.py" -Destination $Dest -Force

Write-Host "✅ Claude Code PreToolUse Safety Hook installed successfully to $Dest" -ForegroundColor Green
