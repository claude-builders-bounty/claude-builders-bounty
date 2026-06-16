# changelog.ps1 — Generate structured CHANGELOG.md from git history (PowerShell)
# Usage: .\changelog.ps1 [-Repo PATH] [-Output FILE] [-Since TAG]

param(
    [string]$Repo = (Get-Location).Path,
    [string]$Output = "CHANGELOG.md",
    [string]$Since = ""
)

python (Join-Path $PSScriptRoot "changelog.py") --repo "$Repo" --output "$Output" $(if ($Since) { "--since $Since" })
