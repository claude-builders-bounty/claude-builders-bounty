$HooksDir = Join-Path $HOME ".claude\hooks"
if (-not (Test-Path $HooksDir)) {
    New-Item -ItemType Directory -Force -Path $HooksDir | Out-Null
}

Copy-Item "hooks\pre_tool_use_bash_guard.py" -Destination (Join-Path $HooksDir "pre-tool-use.py") -Force
Write-Host "Claude Code Pre-Tool-Use Destructive Command Guard successfully installed to $HooksDir" -ForegroundColor Green
