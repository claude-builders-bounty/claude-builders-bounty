<# 
.SYNOPSIS
    AI Desktop Pet - Launcher
.DESCRIPTION
    Auto cleanup, check deps, compile, start dev mode
    Full log output to project dir pet-startup-YYYYMMDD-HHMMSS.log
#>

param(
    [switch]$NoPause
)

$ProjectDir = "D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\ai-desktop-pet-tsunade"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile = Join-Path $ProjectDir "pet-startup-$Timestamp.log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $entry = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Message"
    Add-Content -Path $LogFile -Value $entry -Encoding UTF8
    Write-Host $entry
}

function Write-Section {
    param([string]$Title)
    $line = "=" * 60
    Write-Log $line
    Write-Log "  $Title"
    Write-Log $line
}

Write-Section "AI Desktop Pet - Launcher"
Write-Log "Project dir: $ProjectDir"
Write-Log "Log file: $LogFile"
Write-Log ""

try {
    Set-Location -Path $ProjectDir -ErrorAction Stop
}
catch {
    Write-Log "Cannot enter project dir: $($_.Exception.Message)" "ERROR"
    if (-not $NoPause) { Read-Host "Press Enter to exit" }
    exit 1
}

Write-Section "1/4 Cleaning stale processes"
$killed = @()

$electronProcs = Get-Process -Name "electron" -ErrorAction SilentlyContinue
if ($electronProcs) {
    $electronProcs | ForEach-Object {
        Write-Log "Kill Electron process (PID: $($_.Id))"
        $_ | Stop-Process -Force
        $killed += "electron:$($_.Id)"
    }
}

$nodeProcs = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcs) {
    $nodeProcs | ForEach-Object {
        $ports = Get-NetTCPConnection -OwningProcess $_.Id -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 5173 -and $_.State -eq 'Listen' }
        if ($ports) {
            Write-Log "Kill node process on port 5173 (PID: $($_.Id))"
            $_ | Stop-Process -Force
            $killed += "node:$($_.Id)"
        }
    }
}

$portProcs = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
if ($portProcs) {
    $portProcs | ForEach-Object {
        try {
            $proc = Get-Process -Id $_.OwningProcess -ErrorAction Stop
            Write-Log "Kill process by port (PID: $($_.OwningProcess), Name: $($proc.ProcessName))"
            $proc | Stop-Process -Force
            $killed += "port:$($_.OwningProcess)"
        } catch { }
    }
}

if ($killed.Count -gt 0) {
    Write-Log "Cleaned: $($killed -join ', ')"
} else {
    Write-Log "No stale processes"
}
Start-Sleep -Seconds 1

Write-Section "2/4 Checking dependencies"
if (-not (Test-Path -Path "node_modules")) {
    Write-Log "First run, installing dependencies..." "WARN"
    $result = npm install 2>&1 | Tee-Object -Variable npmOut
    $npmOut | ForEach-Object { Write-Log $_ }
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Dependency install failed (exit code: $LASTEXITCODE)" "ERROR"
        if (-not $NoPause) { Read-Host "Press Enter to exit" }
        exit 1
    }
} else {
    Write-Log "Dependencies exist, skipping install"
}

Write-Section "3/4 Compiling main process"
Write-Log "Running: npx tsc -p tsconfig.main.json"
$result = npx tsc -p tsconfig.main.json 2>&1 | Tee-Object -Variable tscOut
$tscOut | ForEach-Object { Write-Log $_ }
if ($LASTEXITCODE -ne 0) {
    Write-Log "Main process compilation failed (exit code: $LASTEXITCODE)" "ERROR"
    if (-not $NoPause) { Read-Host "Press Enter to exit" }
    exit 1
}
Write-Log "Main process compilation successful"

Write-Section "4/4 Starting dev mode"
Write-Log ""
Write-Log "----------------------------------------"
Write-Log "  Pet window: screen (100,100) - transparent frameless"
Write-Log "  Right-click menu: Chat / Settings / Monitor / Reminder / About"
Write-Log "  DevTools: opens automatically, can close manually"
Write-Log "  Close this PowerShell window = exit program"
Write-Log "----------------------------------------"
Write-Log ""

Write-Log "Start command: npm run electron:dev"
Write-Log ""

$proc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run electron:dev" -WorkingDirectory $ProjectDir -PassThru -RedirectStandardOutput (Join-Path $ProjectDir "stdout-$Timestamp.tmp") -RedirectStandardError (Join-Path $ProjectDir "stderr-$Timestamp.tmp")

Write-Log "Process started (PID: $($proc.Id)), waiting for exit..."
$proc.WaitForExit()

Get-Content (Join-Path $ProjectDir "stdout-$Timestamp.tmp") -ErrorAction SilentlyContinue | ForEach-Object { Write-Log $_ }
Get-Content (Join-Path $ProjectDir "stderr-$Timestamp.tmp") -ErrorAction SilentlyContinue | ForEach-Object { Write-Log $_ }

Remove-Item (Join-Path $ProjectDir "stdout-$Timestamp.tmp") -ErrorAction SilentlyContinue
Remove-Item (Join-Path $ProjectDir "stderr-$Timestamp.tmp") -ErrorAction SilentlyContinue

Write-Section "Program exited"
Write-Log "Exit code: $($proc.ExitCode)"
Write-Log "Full log: $LogFile"

if (-not $NoPause) {
    Read-Host "Press Enter to exit"
}