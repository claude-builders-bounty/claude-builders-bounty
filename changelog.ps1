# CHANGELOG Generator (PowerShell)
# Automatically generates a structured CHANGELOG.md from git history

Write-Host "Generating CHANGELOG from git history..." -ForegroundColor Green

# Get last tag
$lastTag = git describe --tags --abbrev=0 2>$null
if ($lastTag) {
    Write-Host "Last tag: $lastTag" -ForegroundColor Cyan
    $version = "v$lastTag"
    $ref = "$lastTag..HEAD"
} else {
    Write-Host "No tags found, using all commits" -ForegroundColor Yellow
    $version = "Unreleased"
    $ref = "HEAD"
}

# Get commits
$commits = git log $ref --pretty=format:%s 2>$null
if ($commits) {
    $commitList = $commits -split "`n"
    $commitCount = $commitList.Count
} else {
    $commitList = @()
    $commitCount = 0
}
Write-Host "Found $commitCount commits" -ForegroundColor Cyan

# Categorize commits
$added = @()
$fixed = @()
$changed = @()
$removed = @()

foreach ($commit in $commitList) {
    if ([string]::IsNullOrWhiteSpace($commit)) { continue }
    
    $commitLower = $commit.ToLower()
    
    if ($commitLower -match "(add|added|add:|feat:|feature|new|create|implement)") {
        $added += $commit
    } elseif ($commitLower -match "(fix|fixed|fix:|bug|bugfix|resolve|correct|patch)") {
        $fixed += $commit
    } elseif ($commitLower -match "(remove|removed|remove:|delete|deleted|deprecate|deprecation)") {
        $removed += $commit
    } else {
        $changed += $commit
    }
}

# Build changelog
$date = Get-Date -Format "yyyy-MM-dd"
$changelog = "# Changelog`n`n"
$changelog += "## [$version] - $date`n`n"

if ($added.Count -gt 0) {
    $changelog += "### Added`n`n"
    foreach ($commit in $added) {
        $changelog += "- $commit`n"
    }
    $changelog += "`n"
}

if ($fixed.Count -gt 0) {
    $changelog += "### Fixed`n`n"
    foreach ($commit in $fixed) {
        $changelog += "- $commit`n"
    }
    $changelog += "`n"
}

if ($changed.Count -gt 0) {
    $changelog += "### Changed`n`n"
    foreach ($commit in $changed) {
        $changelog += "- $commit`n"
    }
    $changelog += "`n"
}

if ($removed.Count -gt 0) {
    $changelog += "### Removed`n`n"
    foreach ($commit in $removed) {
        $changelog += "- $commit`n"
    }
    $changelog += "`n"
}

if ($added.Count -eq 0 -and $fixed.Count -eq 0 -and $changed.Count -eq 0 -and $removed.Count -eq 0) {
    $changelog += "No changes since last release.`n"
}

# Write to file
$changelog | Out-File -FilePath "CHANGELOG.md" -Encoding UTF8

Write-Host "CHANGELOG.md generated successfully!" -ForegroundColor Green
Write-Host "Version: $version" -ForegroundColor Cyan
Write-Host "Commits processed: $commitCount" -ForegroundColor Cyan