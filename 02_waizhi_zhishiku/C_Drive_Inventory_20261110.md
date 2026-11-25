# C 盘清单报告

**采集时间**：2026-11-10  
**主机**：Windows 10 Pro 10.0.19045  
**采集方式**：仅读取，PowerShell 原生命令，未修改任何文件或配置  
**权限状态**：部分目录/操作因权限不足未能读取（已在相应位置标注）

---

## 1. 磁盘总览

| 项目 | 数值 |
|------|------|
| 总容量 | 80.00 GB |
| 已用空间 | 79.86 GB |
| 剩余空间 | 0.14 GB |
| 剩余比例 | 0.2% |
| 碎片率 | 无法获取（权限不足，0x89000024，需管理员运行 `defrag C: /A`） |

> ⚠️ **警告**：C 盘剩余空间仅 0.14 GB（0.2%），处于严重不足状态，可能导致系统更新失败、应用崩溃或虚拟内存页面文件无法扩展，建议立即清理。

---

## 2. 根目录一级文件夹大小排序（前 20）

| 排名 | 文件夹 | 大小 |
|------|--------|------|
| 1 | `C:\Windows` | 29,043.48 MB (~28.36 GB) |
| 2 | `C:\Users` | 28,334.87 MB (~27.67 GB) |
| 3 | `C:\Program Files` | 8,851.79 MB (~8.64 GB) |
| 4 | `C:\Program Files (x86)` | 7,646.43 MB (~7.47 GB) |
| 5 | `C:\Tencent` | 106.79 MB |
| 6 | `C:\fanqie-publisher-cli` | 0.23 MB |
| 7 | `C:\$WINDOWS.~BT` | 0.01 MB |
| 8 | `C:\tmp` | 0 MB |
| 9 | `C:\ESD` | 0 MB |
| 10 | `C:\inetpub` | 0 MB |
| 11 | `C:\PerfLogs` | 0 MB |
| 12 | `C:\Temp` | 0 MB |
| 13 | `C:\LeakHotfix` | 0 MB |

---

## 3. 关键系统目录占用

| 目录 | 大小 | 项目数 | 状态 |
|------|------|--------|------|
| `C:\Windows` | 28.36 GB | 298,237 | OK |
| `C:\Users` | 27.67 GB | 330,460 | OK |
| `C:\Program Files` | 8.64 GB | 29,109 | OK |
| `C:\Program Files (x86)` | 7.47 GB | 18,346 | OK |
| `C:\ProgramData` | 4.64 GB | 17,020 | OK |

---

## 4. 用户配置文件大小细分（Administrator）

| 子文件夹 | 大小 | 状态 |
|----------|------|------|
| `AppData` | 25,848.78 MB (~25.24 GB) | OK |
| `Desktop` | 104.04 MB | OK |
| `Documents` | 0 MB | OK |
| `Downloads` | 279.22 MB | OK |
| `OneDrive` | 1.19 MB | OK |

> AppData 占用绝大部分（约 25 GB），是清理重点区域，建议重点查看 `AppData\Local` 和 `AppData\Roaming` 下的缓存与更新下载文件。

---

## 5. 临时/缓存目录大小

| 目录 | 大小 | 项目数 | 状态 | 清理建议 |
|------|------|--------|------|----------|
| `C:\Windows\Temp` | 0 GB | 0 | OK | 可清理（当前为空） |
| `C:\Windows\Prefetch` | 0 GB | 0 | OK | 建议保留（系统启动优化） |
| `C:\Windows\SoftwareDistribution` | 0.04 GB | 31 | OK | 可清理（Windows 更新缓存，需停止 wuauserv 后操作） |
| `C:\Windows\WinSxS` | 8.45 GB | 115,520 | OK | 可用 `DISM /Online /Cleanup-Image /StartComponentCleanup` 清理旧组件 |

---

## 6. 占用空间最大的 30 个文件

| # | 路径 | 大小 | 最后修改时间 | 备注 |
|---|------|------|-------------|------|
| 1 | `C:\Users\Administrator\AppData\Local\Ollama\updates_v2\ebc82afa4f90fff4c778d67b5487f6653937e2f443d31150c9eed61d1c73f97e\OllamaSetup.exe` | 1,771.61 MB | 2026-11-10 13:44 | Ollama 安装程序，可清理 |
| 2 | `C:\Users\Administrator\.cache\modelscope\models\iic--speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch\snapshots\v2.0.4\model.pt` | 943.91 MB | 2026-10-23 08:26 | ModelScope 模型缓存 |
| 3 | `C:\Program Files\WSL\system.vhd` | 722.92 MB | 2026-06-25 17:46 | WSL 系统磁盘镜像 |
| 4 | `C:\Windows\Installer\62cf6c2.msi` | 655.54 MB | 2025-09-12 00:54 | Windows 安装程序缓存 |
| 5 | `C:\ProgramData\NVIDIA Corporation\Nsight\nsight_visual_studio_edition-windows-x86_64-2022.3.0.22245_31767666.msi` | 525.59 MB | 2022-09-03 07:46 | NVIDIA Nsight 安装包 |
| 6 | `C:\Windows\Installer\449e63.msi` | 525.59 MB | 2022-09-03 07:46 | Windows 安装程序缓存 |
| 7 | `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\cublasLt64_11.dll` | 518.87 MB | 2022-09-07 06:12 | CUDA 库 |
| 8 | `C:\Users\Administrator\AppData\Roaming\LarkShell\sdk_storage\7e88054406dde9bab063f8e1a3cf4324\resources\seed\c9a329e0-5fd7-54ed-ba0d-d84233b193d4` | 501.68 MB | 2026-11-10 01:16 | 飞书/Lark 缓存 |
| 9 | `C:\Users\Administrator\AppData\Roaming\LarkShell\update\update_downloading\f190d7e430151a1c09e1b9d61e8412bb-817dc4888a40de5d7d30258b372270c7-1th.exe` | 500.71 MB | 2026-11-10 01:16 | 飞书/Lark 更新下载文件，可清理 |
| 10 | `C:\Windows\Installer\449e53.msi` | 459.92 MB | 2022-08-25 10:57 | Windows 安装程序缓存 |
| 11 | `C:\Users\Administrator\AppData\Local\Path of Exile 2\Pipelines\data.mdb` | 445.32 MB | 2026-09-13 06:52 | 游戏数据文件 |
| 12 | `C:\Windows\Installer\449e4d.msi` | 374.66 MB | 2022-09-20 02:43 | Windows 安装程序缓存 |
| 13 | `C:\Windows\Installer\1243aa3.msi` | 350.64 MB | 2026-10-01 02:51 | Windows 安装程序缓存 |
| 14 | `C:\Program Files (x86)\Microsoft\EdgeCore\157.0.4341.42\msedge.dll` | 341.18 MB | 2026-11-05 15:30 | Edge 浏览器核心库 |
| 15 | `C:\Program Files (x86)\Microsoft\EdgeWebView\Application\157.0.4341.42\msedge.dll` | 341.18 MB | 2026-11-05 15:30 | Edge WebView2 库 |
| 16 | `C:\Program Files (x86)\Microsoft\Edge\Application\157.0.4341.42\msedge.dll` | 341.18 MB | 2026-11-05 15:30 | Edge 浏览器核心库 |
| 17 | `C:\Program Files (x86)\Microsoft\Copilot\Application\157.0.4341.42\msedge.dll` | 341.18 MB | 2026-11-05 15:30 | Copilot 应用库 |
| 18 | `C:\Program Files (x86)\Microsoft\EdgeCore\Optimized\msedge.dll` | 341.18 MB | 2026-11-05 15:30 | Edge 优化版核心库 |
| 19 | `C:\Users\Administrator\AppData\Local\Programs\Python\Python313\Lib\site-packages\claude_agent_sdk\_bundled\claude.exe` | 328.83 MB | 2026-11-09 19:00 | Claude Agent SDK 可执行文件 |
| 20 | `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\lib\x64\nvrtc_static.lib` | 302.50 MB | 2022-09-22 02:15 | CUDA 库 |
| 21 | `C:\Users\Administrator\AppData\Local\NRC\Saved\ProgramBinaryCache\D3DGraphics_V4318_D7172_S29559_R161.ushaderprecache` | 299.00 MB | 2026-03-27 01:43 | GPU 着色器缓存 |
| 22 | `C:\Users\Administrator\AppData\Local\Programs\Python\Python313\Lib\site-packages\torch\lib\torch_cpu.dll` | 295.17 MB | 2026-11-09 18:55 | PyTorch 库 |
| 23 | `C:\Program Files (x86)\Common Files\VMware\InstallerCache\{6EC7759F-B700-4743-BB65-BD3ED905D545}.msi` | 287.20 MB | 2026-05-17 04:27 | VMware 安装包缓存 |
| 24 | `C:\Windows\Installer\d5dae16.msi` | 287.20 MB | 2026-05-17 04:27 | Windows 安装程序缓存 |
| 25 | `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\cusolver64_11.dll` | 284.62 MB | 2022-08-26 09:30 | CUDA 库 |
| 26 | `C:\Users\Administrator\AppData\Local\@deepseek-aidsh-desktop-updater\installer.exe` | 276.01 MB | 2026-10-29 13:45 | DeepSeek 助手更新程序，可清理 |
| 27 | `C:\Program Files (x86)\Microsoft\Copilot\Application\undocked_copilot\Installer\msedge.7z` | 274.40 MB | 2026-11-05 15:02 | Copilot 安装包，可清理 |
| 28 | `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\cufft64_10.dll` | 266.91 MB | 2022-08-26 07:43 | CUDA 库 |
| 29 | `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\cusparse64_11.dll` | 264.59 MB | 2022-08-26 07:57 | CUDA 库 |
| 30 | `C:\Users\Administrator\.vscode\extensions\anthropic.claude-code-2.1.301-win32-x64\resources\native-binary\claude.exe` | 259.25 MB | 2026-10-16 08:17 | Claude Code 扩展二进制 |

---

## 7. 可清理项建议

| 清理对象 | 预估可释放 | 建议操作 | 风险 |
|----------|-----------|----------|------|
| `C:\Windows\WinSxS` | 约 8.45 GB（部分可清理） | 管理员运行 `DISM /Online /Cleanup-Image /StartComponentCleanup` | 低（系统自带） |
| `C:\Windows\SoftwareDistribution\Download` | 0.04 GB | 停止 Windows Update 服务后清空 Download 子目录 | 低 |
| `C:\Users\Administrator\AppData\Roaming\LarkShell\update\update_downloading\` | ~500 MB | 删除下载中的更新文件 | 低 |
| `C:\Users\Administrator\AppData\Local\Ollama\updates_v2\` | ~1.77 GB | 确认 Ollama 已安装成功后删除安装程序 | 低 |
| `C:\Users\Administrator\.cache\modelscope\` | ~944 MB | 清理不再使用的模型缓存 | 中（可能影响已下载模型） |
| `C:\Windows\Installer\*.msi` | 多个几百 MB 的旧安装包 | 仅删除对应已卸载程序的 .msi（需谨慎） | 中 |
| `C:\Users\Administrator\AppData\Local\@deepseek-aidsh-desktop-updater\installer.exe` | ~276 MB | 删除已完成更新的安装程序 | 低 |
| `C:\Program Files (x86)\Microsoft\Copilot\Application\undocked_copilot\Installer\msedge.7z` | ~274 MB | 删除安装包 | 低 |

**合计可清理预估**：约 10–12 GB（在保证系统稳定的前提下）

---

## 8. 简要分析

1. **空间危机**：C 盘仅剩 0.14 GB（0.2%），属于危险水平。系统页面文件、更新、日志写入均可能失败，建议优先清理。
2. **大目录分布**：Windows (28 GB) 和 Users (27 GB) 并列最大，各占约 1/3 磁盘空间。Program Files 与 Program Files (x86) 各约 7–8 GB。
3. **用户空间集中在 AppData**：Administrator 用户的 AppData 占 25.24 GB，其中 LarkShell、Ollama、ModelScope、PyTorch 等缓存和安装包是主要占用源。
4. **系统组件存储**：WinSxS 占用 8.45 GB，可通过 DISM 清理旧组件释放部分空间。
5. **权限受限项**：防火墙规则查询、磁盘碎片分析均因权限不足未能完成，建议以管理员身份补查。

---

*报告生成工具：PowerShell 原生命令（Get-ChildItem、Get-CimInstance、Get-NetTCPConnection、defrag 等），仅读取不修改。*
