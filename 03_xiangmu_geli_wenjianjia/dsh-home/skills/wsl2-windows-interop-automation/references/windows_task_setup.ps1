<#>
.SYNOPSIS
    Register cua-driver as a Windows Scheduled Task that runs at startup in the user's interactive session (Session 1).
    This ensures the daemon has desktop access for UI Automation.

.NOTES
    - Must run as Administrator
    - Task runs as the CURRENT USER (Interactive logon type)
    - Runs at startup and on demand
    - Logs to %LOCALAPPDATA%\cua-driver.log

#>
param(
    [string]$CuaDriverPath = "$env:LOCALAPPDATA\Programs\Cua\cua-driver\bin\cua-driver.exe",
    [string]$TaskName = "cua-driver-serve",
    [string]$Arguments = "serve"
)

# Verify binary exists
if (-not (Test-Path $CuaDriverPath)) {
    Write-Error "cua-driver not found at: $CuaDriverPath"
    Write-Error "Install it first: scoop install cua-driver"
    exit 1
}

# Delete existing task if present
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "Removing existing task: $TaskName"
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create action: run cua-driver.exe serve
$action = New-ScheduledTaskAction -Execute $CuaDriverPath -Argument $Arguments

# Trigger: at startup
$trigger = New-ScheduledTaskTrigger -AtStartup

# Settings: run on battery, don't stop on battery, start when available, run only if network available
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)  # No time limit

# Principal: current user, interactive logon, highest privileges
$principal = New-ScheduledTaskPrincipal `
    -UserId (whoami) `
    -LogonType Interactive `
    -RunLevel Highest

# Register the task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Force `
    -Description "cua-driver daemon for WSL2 interop GUI automation. Runs in user session (Session 1) with desktop access."

Write-Host "Task '$TaskName' registered successfully."

# Start immediately
Write-Host "Starting task..."
schtasks /Run /TN $TaskName

# Verify
Start-Sleep 3
$status = schtasks /Query /TN $TaskName /V /FO LIST 2>$null
if ($status -match "Running") {
    Write-Host "SUCCESS: $TaskName is running."
} else {
    Write-Warning "Task may not be running yet. Check manually: schtasks /Query /TN $TaskName /V /FO LIST"
}

# Show log location
Write-Host "Logs: $env:LOCALAPPDATA\cua-driver.log (stdout) / cua-driver-error.log (stderr)"