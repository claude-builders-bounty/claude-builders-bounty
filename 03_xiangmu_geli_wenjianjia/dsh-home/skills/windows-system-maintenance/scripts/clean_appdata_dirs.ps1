# Clean AppData directories that commonly accumulate large caches
# Usage: powershell -ExecutionPolicy Bypass -File clean_appdata_dirs.ps1
# Run with target directories closed (apps exited) for best results

$targets = @(
    @{ Path = "$env:TEMP"; Name = "Temp"; Desc = "User temporary files" },
    @{ Path = "$env:LOCALAPPDATA\Doubao"; Name = "Doubao"; Desc = "豆包 AI 对话缓存" },
    @{ Path = "$env:APPDATA\LarkShell"; Name = "LarkShell"; Desc = "飞书缓存、日志" },
    @{ Path = "$env:APPDATA\duowan"; Name = "duowan"; Desc = "多玩/YY 游戏助手缓存" },
    @{ Path = "$env:LOCALAPPDATA\Thunder Network"; Name = "Thunder Network"; Desc = "迅雷下载缓存" },
    @{ Path = "$env:APPDATA\Kingsoft"; Name = "Kingsoft"; Desc = "WPS 备份/临时文件" }
)

Write-Host "=== Cleaning AppData directories ===" -ForegroundColor Cyan
$totalFreed = 0

foreach ($t in $targets) {
    if (Test-Path $t.Path) {
        $before = (Get-ChildItem $t.Path -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "  [$($t.Name)] $($t.Path) - $([math]::Round($before,2)) MB - $($t.Desc)" -ForegroundColor Yellow
        try {
            Remove-Item $t.Path -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  [$($t.Name)] Cleaned" -ForegroundColor Green
            $totalFreed += $before
        } catch {
            Write-Host "  [$($t.Name)] Error: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  [$($t.Name)] Not found (already clean)" -ForegroundColor Gray
    }
}

Write-Host "" 
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Total freed: $([math]::Round($totalFreed,2)) MB" -ForegroundColor Green
Write-Host "Run 'df -h /mnt/c' in WSL to verify C: drive space." -ForegroundColor Cyan
