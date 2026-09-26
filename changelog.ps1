<#
.SYNOPSIS
    Generate a structured CHANGELOG.md from git history (PowerShell port of changelog.sh).
.DESCRIPTION
    Fetches commits since the last git tag, categorizes them into
    Added / Fixed / Changed / Removed, and writes a Keep-a-Changelog style CHANGELOG.md.
.PARAMETER ProjectDir
    Path to the git repository (default: current directory).
.PARAMETER Output
    Output file path (default: CHANGELOG.md in the project dir).
.EXAMPLE
    .\changelog.ps1                     # render CHANGELOG.md in current repo
    .\changelog.ps1 -ProjectDir C:\repo -Output changelog.md
#>
param(
    [string]$ProjectDir = ".",
    [string]$Output = "CHANGELOG.md"
)

$ErrorActionPreference = "Stop"

Push-Location $ProjectDir
try {
    git rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -ne 0) { throw "'$ProjectDir' is not a git repository." }

    # Last tag, or fall back to full history.
    $lastTag = (git describe --tags --abbrev=0 2>$null | Select-Object -First 1)
    $baseSpec = if ($lastTag) { "$lastTag..HEAD" } else { "HEAD" }
    $rangeDesc = if ($lastTag) { "since $lastTag" } else { "full history (no tags found)" }
    Write-Host "Changelog range: $rangeDesc"

    # <hash>|<subject> per line
    $raw = git log --pretty=format:'%h|%s' $baseSpec 2>$null
    if (-not $raw) {
        Set-Content -Path $Output -Value "# Changelog`n`n_(no commits in the selected range)_"
        Write-Host "Wrote $Output (no commits)."
        exit 0
    }

    $added = [System.Collections.Generic.List[string]]::new()
    $fixed = [System.Collections.Generic.List[string]]::new()
    $changed = [System.Collections.Generic.List[string]]::new()
    $removed = [System.Collections.Generic.List[string]]::new()

    function Get-CleanSubject([string]$subject) {
        # Strip conventional prefix and optional scope: feat(scope): msg -> msg
        if ($subject -match '^\w+(\([^)]*\))?!?:\s?(.*)$') { return $Matches[2] }
        return $subject
    }

    function Get-Category([string]$subject) {
        $lower = $subject.ToLowerInvariant()
        if ($lower -match '^(feat|feature|add|new|introduce)[(:]') { return 'Added' }
        if ($lower -match '^(fix|bugfix|bug|hotfix|patch)[(:]') { return 'Fixed' }
        if ($lower -match '^(remove|delete|drop|deprecate|breaking|refactor!)[(:]') { return 'Removed' }
        if ($lower -match '!:\s') { return 'Removed' }
        return 'Changed'
    }

    $outLines = New-Object System.Collections.Generic.List[string]
    foreach ($line in $raw) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        $parts = $line -split '\|', 2
        if ($parts.Count -lt 2) { continue }
        $hash = $parts[0].Trim()
        $subject = $parts[1].Trim()
        $clean = Get-CleanSubject $subject
        $cat = Get-Category $subject
        $item = "* $clean ([$hash](https://github.com/user/repo/commit/$hash))"
        switch ($cat) {
            'Added'   { $added.Add($item) }
            'Fixed'   { $fixed.Add($item) }
            'Removed' { $removed.Add($item) }
            default   { $changed.Add($item) }
        }
    }

    $today = Get-Date -Format 'yyyy-MM-dd'
    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine('# Changelog')
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('All notable changes to this project are documented in this file,')
    [void]$sb.AppendLine('generated automatically from git history.')
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine("## [Unreleased] - $today")
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine("_Range: ${rangeDesc}_")
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('### Added')
    if ($added.Count -eq 0) { [void]$sb.AppendLine('- No additions in this range.') } else { foreach ($i in $added) { [void]$sb.AppendLine($i) } }
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('### Fixed')
    if ($fixed.Count -eq 0) { [void]$sb.AppendLine('- No fixes in this range.') } else { foreach ($i in $fixed) { [void]$sb.AppendLine($i) } }
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('### Changed')
    if ($changed.Count -eq 0) { [void]$sb.AppendLine('- No changes in this range.') } else { foreach ($i in $changed) { [void]$sb.AppendLine($i) } }
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('### Removed')
    if ($removed.Count -eq 0) { [void]$sb.AppendLine('- Nothing removed in this range.') } else { foreach ($i in $removed) { [void]$sb.AppendLine($i) } }

    Set-Content -Path $Output -Value $sb.ToString() -Encoding UTF8
    Write-Host "Wrote $Output ($($added.Count) added, $($fixed.Count) fixed, $($changed.Count) changed, $($removed.Count) removed)."
}
finally {
    Pop-Location
}