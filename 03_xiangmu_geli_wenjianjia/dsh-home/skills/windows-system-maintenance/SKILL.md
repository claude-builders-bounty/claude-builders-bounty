---
name: windows-system-maintenance
description: "Windows/WSL 系统维护与磁盘清理：安全识别可清理路径、执行清理、迁移缓存配置，不破坏系统与软件运行。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, wsl]
tags: [windows, wsl, disk-cleanup, system-maintenance, cache-migration, safety]
---

# Windows/WSL 系统维护与磁盘清理

针对 Windows（含 WSL 挂载的 `/mnt/c`）的磁盘空间回收与缓存迁移。核心原则：**只清理可安全删除的缓存/临时文件，绝不碰系统核心、程序运行库、UWP 数据、用户配置**。迁移大户缓存有两条路，按顺序选：① 软件内置的缓存/存储路径设置（最安全）；② 软件没有该设置时，对**用户级 App Data 目录**用**目录 junction** 迁移（见第 8 节完整工作流）。junction 对系统目录与下方红线目录仍然**禁止**。

## 触发条件
- C 盘剩余空间 < 20% 或用户主动要求清理
- 需要迁移大型缓存目录到其他盘符
- 排查不明空间占用来源

## 硬性安全红线（违反即造成软件/系统损坏）
| 目录/组件 | 后果 | 处理方式 |
|-----------|------|----------|
| `C:\ProgramData\CCP` | 腾讯全家桶游戏全挂 | **只读，绝不删、不动、不链接** |
| `C:\ProgramData\Microsoft` | 系统组件缺失 | **只读** |
| `C:\Users\<user>\AppData\Local\Packages` | UWP 应用全炸，开始菜单变空 | **只读** |
| `C:\Windows\WinSxS` / `DriverStore` | 系统更新/驱动回滚/修复失效 | 仅允许 `Dism /Online /Cleanup-Image /StartComponentCleanup /ResetBase` |
| `C:\Users\<user>\AppData\Roaming\Microsoft\Windows` | 用户配置损坏，无法登录桌面 | **只读** |
| 对红线/系统目录做 `mklink /J` | 权限错误、更新失败、应用崩溃 | **禁止**；junction 只用于用户级 App Data（见第 8 节规程），红线目录只读 |

## 标准清理流程（按顺序执行，每步可独立运行）

### 1. 系统级临时文件深度清理
```cmd
cleanmgr /sageset:99
cleanmgr /sagerun:99
```
- 清理：临时文件、缩略图缓存、回收站、Windows 更新清理、旧版本备份
- 需管理员权限

### 2. 用户临时目录 `%TEMP%`
```cmd
del /q /f /s %TEMP%\* 2>nul
for /d %d in (%TEMP%\*) do rd /s /q %d 2>nul
```
- 强制删除可删文件，跳过被占用项

### 3. 开发工具链缓存
| 工具 | 清理命令 | 永久迁移环境变量 |
|------|----------|------------------|
| uv | `uv cache clean` | `UV_CACHE_DIR=D:\uv_cache` |
| pip | `pip cache purge` | `PIP_CACHE_DIR=D:\pip_cache` |
| npm | `npm cache clean --force` | `npm config set cache D:\npm_cache` |
| cargo | `cargo clean` | `CARGO_HOME=D:\.cargo` |
| go | `go clean -cache -modcache` | `GOMODCACHE=D:\go\pkg\mod` |

### 4. AI/模型运行时缓存
| 组件 | 典型路径 | 处理 |
|------|----------|------|
| Ollama | `C:\Users\<user>\AppData\Local\Ollama` | 确认模型已在别处（`OLLAMA_MODELS` 指向 D 盘）后**整目录删** |
| HuggingFace | `C:\Users\<user>\.cache\huggingface` | 设置 `HF_HOME=D:\hf_cache` 后删 |
| ModelScope | `C:\Users\<user>\.cache\modelscope` | 设置 `MODELSCOPE_CACHE=D:\ms_cache` 后删 |

### 5. 显卡驱动缓存
| 组件 | 路径 | 大小 | 处理 |
|------|------|------|------|
| NVIDIA DXCache | `C:\Users\<user>\AppData\Local\NVIDIA\DXCache` | 1–3G | **整目录删**，重装驱动自动重建 |
| NVIDIA GLCache | `C:\Users\<user>\AppData\Local\NVIDIA\GLCache` | 几十M | 同删 |
| AMD/Intel 同理 | 对应厂商目录 | 同理 | 同理 |

### 6. WinSxS 组件存储（仅此一法）
```cmd
Dism /Online /Cleanup-Image /StartComponentCleanup /ResetBase
```
- 仅此官方支持的深度清理，**不可手动删文件**
- 通常能回收 100M–1G

### 7. 必须用户在软件内手动改路径的大户（脚本无法代劳）
| 软件 | 设置位置 | 建议目标 |
|------|----------|----------|
| 豆包/抖音/字节系 | 设置 → 缓存路径 | `D:\DoubaoCache` |
| 飞书/Lark | 设置 → 缓存路径 | `D:\LarkCache` |
| 微信/微信文件 | 设置 → 文件管理 → 迁移 | `D:\WeChatFiles` |
| 迅雷 | 设置 → 下载目录/缓存目录 | `D:\ThunderDownload` / `D:\ThunderCache` |
| WPS/金山 | 选项 → 备份路径/临时文件 | `D:\WPSWorkspace` |
| 酷狗/网易云/QQ音乐 | 设置 → 缓存/下载目录 | `D:\MusicCache` |
| Chrome/Edge | 设置 → 下载内容 → 更改位置 | `D:\Downloads` |
| Firefox | 设置 → 常规 → 浏览器缓存 → 选择文件夹 | `D:\FirefoxCache` |
| Ryujinx | 设置 → General → Game Directory / Firmware / Save | `D:\Ryujinx` |
| JetBrains IDE | File → Invalidate Caches → 勾选所有 → Invalidate and Restart | 配合 `idea.config.path` 迁移配置目录 |

### 7.1 可安全删除的缓存目录（无需软件内设置，直接删）
以下目录实测可直接删除，**不影响软件运行**，下次启动自动重建：
| 目录 | 典型大小 | 说明 |
|------|----------|------|
| `%LOCALAPPDATA%\Doubao` | 3–7 GB | 豆包 AI 对话缓存、模型下载残留 |
| `%APPDATA%\LarkShell` | 2–5 GB | 飞书缓存、日志、临时文件 |
| `%APPDATA%\duowan` | 1–4 GB | 多玩/YY 游戏助手缓存 |
| `%LOCALAPPDATA%\Thunder Network` | 0.5–2 GB | 迅雷下载缓存 |
| `%APPDATA%\Kingsoft` | 0.5–2 GB | WPS 备份/临时文件 |
| `%APPDATA%\Tencent` | 1–3 GB | QQ/微信缓存（建议客户端内清理，直删可能丢聊天记录） |

> 删除前建议先关闭对应软件进程，避免文件被锁。删除后软件正常启动即可自动重建必要目录。

## 8. 把用户级数据目录搬到其他盘（junction 工作流）

**适用**：纯用户级 App Data（`AppData\Local\<App>`、`AppData\Roaming\<App>`、`C:\Users\<user>\.<app>`），且应用**已完全退出**（进程不存在）。
**禁止**：上方红线表全部目录、`Program Files`、`AppData\Local\Packages`（UWP 沙箱）。

原理：真实文件放 D 盘，C 盘原位置留一个目录联接（junction）。应用仍看到原路径，绝大多数程序完全无感。

```powershell
# 1) 确认应用已退出（进程不存在），否则文件被锁会漏搬
Get-Process | Where-Object { $_.ProcessName -match '<appname>' }

# 2) 搬（跨盘=复制后删源）。rc<8 才算成功
robocopy "<C:\原路径>" "<D:\新路径>" /E /MOVE /R:1 /W:1
if ($LASTEXITCODE -ge 8) { throw "robocopy 失败：源保持不动，不要继续" }

# 3) 删掉源空壳（robocopy /MOVE 会留下空目录）
Remove-Item -LiteralPath "<C:\原路径>" -Recurse -Force

# 4) 建 junction —— PowerShell 里没有 mklink！
New-Item -ItemType Junction -Path "<C:\原路径>" -Target "<D:\新路径>" | Out-Null
```

### 本工作流的致命陷阱
| 陷阱 | 机制 | 正确做法 |
|------|------|----------|
| **`mklink` 在 PowerShell 里不存在** | `mklink` 是 cmd.exe 内建命令、不是可执行文件 → PowerShell 报 `CommandNotFoundException`。此时文件已搬到 D 盘、junction 未建，**应用目录处于断链状态** | 用 `New-Item -ItemType Junction`；或在 PS 里显式 `& cmd /c "mklink /J ..."` |
| **`rmdir /s` 删 junction 会连带删掉目标真实文件** | `/s` 递归删除链接**指向的内容** | 删链接**只**用 `rmdir "<link>"`（不加 `/s`）；先确认 `Attributes -band ReparsePoint` 再删 |
| **搬到一半失败就删源** | 复制未完成时删源 = 数据丢失 | 先判 robocopy 退出码 `<8` **且**目标侧关键文件已存在，再删源；否则中止并保留源 |
| **用回收站代替删除** | 回收站在同一分区，删进回收站 = 空间没变 | 搬运式清理：移到**另一个盘**的暂存目录，既立刻释放空间又完全可逆 |
| **整目录 `Remove-Item` 撞上被锁文件** | 静默跳过部分项，事后看不出丢了什么 | 迁移后**核对目标侧体积≈原体积**，差异大就去查被锁文件 |

### 迁移后必做验证（四项全过才算成功）
1. 目标盘实际体积 ≈ 原体积
2. 通过 C 盘 junction 路径能访问到应用主程序（如 `...\Application\<app>.exe`）
3. **写入穿透测试**：往 C 盘路径写文件 → 确认能在 D 盘看到
4. 启动应用一次，确认正常

回滚：`& cmd /c "rmdir \"<C:\原路径>\""`（不加 `/s`）后把文件搬回。

---

## 9. 实用脚本与工具

### 9.1 一键清理常见 AppData 缓存脚本
**位置**：`scripts/clean_appdata_dirs.ps1`（本技能目录下）

```powershell
# 用法：powershell -ExecutionPolicy Bypass -File clean_appdata_dirs.ps1
# 先关闭对应软件（豆包、飞书、多玩、迅雷、WPS），再运行
# 自动计算释放量，逐项报告，汇总总计
```

清理目标（见脚本内 `$targets` 数组）：
- `%TEMP%` — 用户临时文件
- `%LOCALAPPDATA%\Doubao` — 豆包 AI 缓存
- `%APPDATA%\LarkShell` — 飞书缓存/日志
- `%APPDATA%\duowan` — 多玩/YY 缓存
- `%LOCALAPPDATA%\Thunder Network` — 迅雷下载缓存
- `%APPDATA%\Kingsoft` — WPS 备份/临时文件

> 实测一次性释放 16 GB+（2026-10-27：Temp 8.5G + Doubao 6.7G + LarkShell 4.5G + duowan 3.1G + 其他）。

### 9.2 PowerShell 目录体积扫描模板（避免中文编码/foreach 语法坑）
```powershell
# 正确写法：用 $f 而非 foreach ( in )
$folders = Get-ChildItem $targetDir -Directory
$results = @()
foreach ($f in $folders) {
    $size = (Get-ChildItem $f.FullName -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    $results += [PSCustomObject]@{Name=$f.Name; SizeMB=[math]::Round($size,2)}
}
$results | Sort-Object SizeMB -Descending | Select-Object -First 20 | Format-Table -AutoSize
```
> PowerShell 中文环境下 `foreach ( in )` 会报 `MissingVariableNameAfterForeach`，必须显式写迭代变量名。

### 9.3 CUDA Toolkit 安装与清理注意事项
- **安装路径固定**：CUDA Toolkit 必须安装到 `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\`（Visual Studio 硬编码查找路径），**无法通过参数改装 D 盘**。
- **安装后可用 Junction 迁移**：
  ```cmd
  move "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA" "D:\Ai\CUDA"
  mklink /J "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA" "D:\Ai\CUDA"
  ```
  真实文件在 D 盘，C 盘留联接点，VS/CMake/nvcc 无感知。
- **静默安装**：`setup.exe /s /noreboot`（安装包约 3 GB，需 C 盘预留 3-4 GB 临时空间）。
- **提取的安装文件**：运行安装包后会在 `%LOCALAPPDATA%\Temp\CUDA\` 解压完整安装文件，可直接运行其中的 `setup.exe /s /noreboot`，避免重复下载。
- **环境变量 CUDA_PATH**：安装后需设置 `CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8`（User 级即可，Machine 级需管理员）。
- **GTX 1060 (Pascal) 必须用 CUDA 11.8**：禁止 12.x，sm_61 架构 11.8 兼容性最优。
- **`.bat`/`.cmd` 必须纯 ASCII**：cmd.exe 按 GBK 解析文件，UTF-8 中文注释会乱码并破坏行语法（表现为 `'xxx' 不是内部或外部命令`、`unexpected EOF`）。中文说明写进 `.md`/`.ps1`，`.bat` 只用英文注释。
- **`whoami` 在 MSYS/git-bash 下命中 bash 自带的 `whoami`**，不认 `/groups`。要 Windows 版就写绝对路径 `C:\Windows\System32\whoami.exe`。
- **`reg query` 输出是 GBK**：Python `subprocess` 取它必须 `encoding="gbk", errors="replace"`，否则 reader 线程抛 `UnicodeDecodeError`。
- **`\\wsl.localhost\...` 这类 UNC 路径经 bash 内联传 PowerShell 会失效**（bash 吃反斜杠 / MSYS 路径转换）。把 PowerShell 写进 `.ps1` 文件再执行。
- **在 bash 里给 `wsl ... bash -c "..."` 传变量**：双引号内的 `$VAR` 会被**外层** shell 先展开成空值，命令静默跑错。用单引号包裹或直接写字面路径。
- **算目录体积**用 `[System.IO.Directory]::EnumerateFiles($p,'*','AllDirectories') | Measure-Object -Sum`，比 `Get-ChildItem -Recurse` 快得多。几十 GB 的目录树放后台跑——前台工具调用会超时。
- **提权步骤**（写 `Program Files`、注册计划任务、静默安装）在非提权会话里做不到：写自提权 `.bat`（`net session` 判断 + `Start-Process -Verb RunAs` 重启自身）交用户点一次 UAC。UAC 弹窗无人应答时命令会**挂起直到超时**，别把提权步骤夹在长脚本中间。

## 执行原则（用户偏好嵌入）
1. **能直接执行就直接执行，不生成脚本** —— 用户明确要求「别给脚本，直接帮我做」
   - 例外：需要提权的步骤（UAC）无法在会话内完成 → 写自提权 `.bat` 交付，用户点一次
2. **清理优先用「搬运」而非删除** —— 移到另一盘暂存目录，可逆且真正释放空间（回收站不释放）；附 `manifest.json` 记录每项原路径
3. **中文沟通** —— 所有提示、确认、报告全中文
4. **每步确认风险** —— 删除前展示路径与大小，等待用户 `y/N`；**未经明确批准绝不删任何东西**
5. **不碰雷区** —— 红线目录只读，不链接、不移动、不重命名
6. **结果可验证** —— 清理前后空间对比，汇报释放量；迁移后跑第 8 节的四项验证
7. **交付清单不含猜测** —— 报告里每一项都写出「大小 + 是什么 + 风险等级 + 依据」，不确定就标「需确认」而不是编一个解释
8. **只出报告，不自动清理** —— 用户明确要求「别自己清理，只出报告给我看」；磁盘分析、缓存扫描、大户识别全部输出结构化报告，**等用户逐项确认后再执行对应清理命令**

## 常用诊断命令（WSL 侧可直接跑）
```bash
# 查看 C 盘整体占用
df -h /mnt/c

# 扫描一级目录大小（需管理员/权限足够）
du -h /mnt/c --max-depth=1 2>/dev/null | sort -hr | head -20

# 扫描用户目录大物件
du -h /mnt/c/Users/<user>/AppData/Local --max-depth=1 2>/dev/null | sort -hr | head -20
du -h /mnt/c/Users/<user>/AppData/Roaming --max-depth=1 2>/dev/null | sort -hr | head -20

# ProgramData 大物件
du -h /mnt/c/ProgramData --max-depth=1 2>/dev/null | sort -hr | head -15

# WinSxS 占用
du -sh /mnt/c/Windows/WinSxS 2>/dev/null

# 确认某目录是否仍在被占用（Windows 侧）
# cmd.exe /c "handle.exe <path>"  # 需 Sysinternals handle.exe
```

## 典型清理收益参考
| 项目 | 典型释放量 |
|------|------------|
| 系统临时文件 + `%TEMP%` | 0.5–2G |
| uv/pip/npm/cargo 等工具链缓存 | 1–5G |
| Ollama/HF/ModelScope 模型缓存 | 2–20G（视模型数量） |
| NVIDIA DXCache | 1–3G |
| WinSxS (DISM) | 0.1–1G |
| **软件内改路径后的未来增量** | **持续节省 6–10G+** |

## 关联技能
- `verify-hermes-setup` — 含环境健康检查
- `manage-python-venv-wsl` — Python 环境隔离，减少系统盘占用
- `install-chromadb-wsl` — 向量库部署选址建议
- `wsl2-windows-interop-automation` — CUA driver 部署与诊断（见 `references/diagnose-process-hijacking.md`)

## 更新日志
- 1.0.0 (2026-08-25): 初版，基于实战会话提炼，含完整红线清单、分步清理流程、用户偏好嵌入