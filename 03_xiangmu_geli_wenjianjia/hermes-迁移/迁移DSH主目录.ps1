# 把 DeepSeek Harness 主目录（~/.dsh）搬到 D 盘
# 用法：完全退出 DeepSeek Harness（含托盘）后，在本文件所在目录运行：
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\迁移DSH主目录.ps1
# 想放到别处就加参数，例如： -NewHome 'D:\dsh-home'

param(
  [string]$NewHome = 'D:\Ai\dsh-home'
)

$ErrorActionPreference = 'Stop'

$old = Join-Path $env:USERPROFILE '.dsh'
$running = @(Get-Process -Name 'DeepSeek Harness' -ErrorAction SilentlyContinue)
if ($running.Count -gt 0) {
  Write-Host "检测到 DeepSeek Harness 还在运行（$($running.Count) 个进程），请先完全退出再运行本脚本。" -ForegroundColor Red
  exit 1
}
if (-not (Test-Path $old)) { Write-Host "找不到 $old" -ForegroundColor Red; exit 1 }
if (Test-Path $NewHome) { Write-Host "$NewHome 已存在，先确认是不是已经迁移过。" -ForegroundColor Red; exit 1 }

New-Item -ItemType Directory -Force (Split-Path $NewHome) | Out-Null

Write-Host "1/3 复制 $old -> $NewHome"
robocopy $old $NewHome /E /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { Write-Host "robocopy 失败（$LASTEXITCODE）" -ForegroundColor Red; exit 1 }

Write-Host "2/3 校验文件数量"
$srcCount = @(Get-ChildItem $old -Recurse -File -Force | Where-Object { $true }).Count
$dstCount = @(Get-ChildItem $NewHome -Recurse -File -Force | Where-Object { $true }).Count
Write-Host "    源 $srcCount 个文件，目标 $dstCount 个文件"
if ($dstCount -lt $srcCount) { Write-Host "目标文件数少于源，已中止，未删除任何东西。" -ForegroundColor Red; exit 1 }

Write-Host "3/3 设置用户环境变量 DSH_HOME=$NewHome"
[Environment]::SetEnvironmentVariable('DSH_HOME', $NewHome, 'User')

# 校验通过才删除旧目录
Remove-Item $old -Recurse -Force

Write-Host ""
Write-Host "完成。现在重新打开 DeepSeek Harness。" -ForegroundColor Green
Write-Host "验证方法：打开应用后随便发一句话，让我执行 `$env:DSH_HOME`，应显示 $NewHome。"
Write-Host ""
Write-Host "如果要回滚："
Write-Host "  [Environment]::SetEnvironmentVariable('DSH_HOME',`$null,'User')"
Write-Host "  然后退出应用，把 $NewHome 移回 $old"
