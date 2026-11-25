# 用系统 Python + 管线 venv 的 site-packages 跑闲鱼扫描（venv 本身已坏，勿用）
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Keywords)
$ErrorActionPreference = 'Stop'
$py = 'C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe'
$sp = 'D:\Ai\Agent\xiangmu\xianyu_pipeline\venv\Lib\site-packages'
$root = 'D:\Ai\Agent\xiangmu\xianyu_pipeline'
$env:PYTHONPATH = "$sp;$root"
$env:PYTHONIOENCODING = 'utf-8'
& $py (Join-Path $PSScriptRoot 'scan.py') @Keywords
exit $LASTEXITCODE
