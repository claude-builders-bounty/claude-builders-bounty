#Requires -Version 5.1
<#
.SYNOPSIS
PreToolUse hook that denies destructive shell commands and logs every denial.
.DESCRIPTION
Reads Claude Code's PreToolUse JSON from stdin. Emits a deny decision for
rm -rf, DROP TABLE, git push --force, TRUNCATE, and DELETE FROM without WHERE.
Safe commands produce no output and exit 0, so normal permission flow applies.
#>

$ErrorActionPreference = 'Stop'

$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }

try {
    $event = $raw | ConvertFrom-Json
} catch {
    exit 0
}

$command = ''
if ($event.tool_input -and $event.tool_input.command) {
    $command = [string]$event.tool_input.command
}
if (-not $command) { exit 0 }

$projectPath = $env:CLAUDE_PROJECT_DIR
if ($event.cwd) { $projectPath = [string]$event.cwd }
if (-not $projectPath) { $projectPath = (Get-Location).Path }

function Find-DestructivePattern {
    param([string]$Statement)

    if ($Statement -match '(?i)\bDROP\s+TABLE\b') { return 'DROP TABLE' }
    if ($Statement -match '(?i)\bTRUNCATE\b') { return 'TRUNCATE' }

    if ($Statement -match '(?i)\bgit\s+push\b' -and
        $Statement -match '(?i)(?:--force(?:-with-lease)?|(?:^|\s)-f(?:\s|$))') {
        return 'git push --force'
    }

    if ($Statement -match '(?i)\bDELETE\s+FROM\b' -and $Statement -notmatch '(?i)\bWHERE\b') {
        return 'DELETE FROM without WHERE'
    }

    if ($Statement -match '(?i)(?:^|[\s;&|])rm(?:\s|$)') {
        $options = @($Statement -split '\s+' | Where-Object { $_ -like '-*' } |
            ForEach-Object { $_.TrimStart('-').ToLowerInvariant() }) -join ''
        if ($options -match 'r' -and $options -match 'f') { return 'rm -rf / rm -fr' }
        if ($options -match 'recursive' -and $options -match 'force') {
            return 'rm --recursive --force'
        }
    }

    if ($Statement -match '(?i)\bRemove-Item\b' -and
        $Statement -match '(?i)-Recurse' -and $Statement -match '(?i)-Force') {
        return 'Remove-Item -Recurse -Force'
    }

    return $null
}

$match = $null
foreach ($statement in ($command -split '[\r\n;]|&&|\|\|')) {
    $match = Find-DestructivePattern -Statement $statement
    if ($match) { break }
}

if (-not $match) { exit 0 }

$logPath = $env:CLAUDE_HOOK_LOG
if (-not $logPath) {
    $logPath = Join-Path $HOME '.claude\hooks\blocked.log'
}
$logDir = Split-Path -Parent $logPath
if ($logDir -and -not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$entry = [ordered]@{
    timestamp         = (Get-Date).ToUniversalTime().ToString('o')
    attempted_command = $command
    project_path      = $projectPath
    matched_pattern   = $match
} | ConvertTo-Json -Compress -Depth 3

Add-Content -Path $logPath -Value $entry -Encoding UTF8

$reason = "Safety hook blocked a destructive command ($match). The command was NOT executed. Use a scoped, reversible alternative and ask the user before deleting or overwriting data."

@{
    hookSpecificOutput = @{
        hookEventName         = 'PreToolUse'
        permissionDecision    = 'deny'
        permissionDecisionReason = $reason
    }
} | ConvertTo-Json -Depth 5
