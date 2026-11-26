#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$hook = Join-Path $root 'block-destructive.ps1'
$log = Join-Path $env:TEMP 'block-destructive-test.log'
if (Test-Path $log) { Remove-Item $log -Force }

$env:CLAUDE_HOOK_LOG = $log
$env:CLAUDE_PROJECT_DIR = 'C:\test\project'

function Invoke-Hook {
    param([string]$Command)
    $payload = @{
        tool_name  = 'Bash'
        tool_input = @{ command = $Command }
        cwd        = 'C:\test\project'
    } | ConvertTo-Json -Depth 4 -Compress
    $output = $payload | & powershell -NoProfile -ExecutionPolicy Bypass -File $hook 2>&1
    return [string]($output -join "`n")
}

$denyCases = @(
    'rm -rf /tmp/build',
    'rm -fr ./dist && echo done',
    'rm -r -f ./cache',
    'mysql -e "DROP TABLE users;"',
    'psql -c "TRUNCATE TABLE orders"',
    'git push --force origin main',
    'git push -f origin main',
    'psql -c "DELETE FROM users"',
    'Remove-Item -Recurse -Force C:\temp\old'
)

$allowCases = @(
    'npm test',
    'rm file.txt',
    'psql -c "DELETE FROM users WHERE id = 7"',
    'git push origin main',
    'echo "rm -rf is dangerous"',
    'Get-ChildItem C:\temp'
)

$failures = 0
foreach ($case in $denyCases) {
    $out = Invoke-Hook -Command $case
    if ($out -notmatch '"permissionDecision"\s*:\s*"deny"') {
        Write-Host "FAIL (expected deny): $case"
        $failures++
    }
}
foreach ($case in $allowCases) {
    $out = Invoke-Hook -Command $case
    if ($out -match '"permissionDecision"\s*:\s*"deny"') {
        Write-Host "FAIL (expected allow): $case"
        $failures++
    }
}

$logLines = @()
if (Test-Path $log) { $logLines = @(Get-Content $log) }
if ($logLines.Count -ne $denyCases.Count) {
    Write-Host "FAIL: log has $($logLines.Count) entries, expected $($denyCases.Count)"
    $failures++
}
foreach ($line in $logLines) {
    $entry = $line | ConvertFrom-Json
    if (-not $entry.timestamp -or -not $entry.attempted_command -or
        -not $entry.project_path -or -not $entry.matched_pattern) {
        Write-Host "FAIL: incomplete log entry: $line"
        $failures++
    }
}

Write-Host "Cases: $($denyCases.Count) deny + $($allowCases.Count) allow. Log entries: $($logLines.Count). Failures: $failures"
if ($failures -gt 0) { exit 1 }
Write-Host 'ALL TESTS PASSED'
