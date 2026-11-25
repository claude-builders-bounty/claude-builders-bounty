# 《审计执行计划》— Windows 主机深度安全审计与合规证据包生成

**文档状态**：待用户确认（确认后方可落地执行）  
**计划日期**：2026-11-10  
**目标宿主**：本机 Windows 10 Pro 10.0.19045（含 WSL / Docker / VM，若存在）  
**执行主体**：Claude Code 多智能体系统（总裁 Agent 调度，PowerShell 原生工具链）  
**工作目录**：`D:\Ai\Agent\gongzuoqu`  
**审计模式**：深度审计（只读采集，无自动修复，无外发数据）

---

## 1. 审计范围与边界

### 1.1 八大审计维度

| 维度 | 简称 | 核心检查点 |
|------|------|-----------|
| D1 | 杀毒/恶意软件 | Defender 状态、威胁检测记录、可疑服务/计划任务/启动项、未签名二进制 |
| D2 | 补丁/漏洞 | 已安装修补程序 (Get-HotFix)、Windows Update 扫描时间、Defender 病毒定义版本 |
| D3 | 配置基线 | 审计策略 (auditpol)、本地安全策略 (secedit 导出)、UAC、RDP、PowerShell 执行策略、防火墙策略 |
| D4 | 网络暴露 | 监听端口/活跃连接 (netstat/Get-NetTCPConnection)、防火墙规则、网络配置、仅本机/本地链路探测 |
| D5 | 权限/账户 | 本地用户/组、Administrators 组成员、账户锁定/密码策略、特权列表 (whoami /priv)、敏感目录 ACL |
| D6 | 日志审计 | 事件日志列表与容量 (wevtutil el/epl)、Security/System/Application/Defender/PowerShell 操作日志导出 (.evtx)、日志启用状态 |
| D7 | 供应链/依赖 | 已安装程序 (注册表卸载项 + Get-Package)、WSL/Docker/Hyper-V 状态、开发依赖清单 (package.json/requirements.txt 等)、驱动签名、WMI 事件消费者 |
| D8 | 数据泄露风险 | BitLocker 加密状态、EFS 加密文件、共享文件夹 (net share)、页面文件/休眠文件、最近文档/临时目录、云同步客户端痕迹 |

### 1.2 深度审计附加项（第 9 阶段）

- 持久化机制排查：运行项注册表 (Run/RunOnce)、服务自启动、计划任务、WMI 事件订阅、启动文件夹
- 离线分析：对所有采集原始数据做文件级哈希 (Get-FileHash) 并归档，用于后续溯源与完整性校验（不外传）
- 内存取证：仅做**可用性评估与记录**（Windows 原生不支持无第三方工具的完整内存镜像；若 Sysinternals 已部署且管理员授权，可记录进程树快照；否则列为已知局限）

### 1.3 禁止事项（硬约束，不可突破）

1. 未经用户逐项确认，不执行任何自动修复、配置变更或补丁安装
2. 不上传/外传主机敏感数据（哈希值本身可作为本地完整性凭据，但不发往外部；不外传用户名、密钥、内网拓扑、日志内容）
3. 不安装未授权的第三方 Agent/服务；仅使用已部署的 Microsoft Safety Scanner、Sysinternals 套件、Defender ATP CLI
4. 不修改系统关键配置（防火墙规则、审计策略、组策略、注册表关键项）
5. 网络动作限制在本机回环 (127.0.0.1/::1) 与本地链路，禁止对外发起主动扫描

---

## 2. 阶段划分与命令清单

全部采集为**只读**；每条命令均附时间戳，输出重定向至证据包对应子目录。

### Phase 0 — 准备与环境预检（预计 2–3 min）

| 步骤 | PowerShell 命令 | 用途 | 证据文件 |
|------|----------------|------|----------|
| 0.1 | `$PSVersionTable; Get-Host` | 记录 PowerShell 版本与主机信息 | `Phase00_Env/psversion.txt` |
| 0.2 | `Get-ComputerInfo \| Select-Object WindowsProductName,WindowsVersion,OsHardwareAbstractionLayer,WindowsSystemDirectory` | 记录宿主版本信息 | `Phase00_Env/computerinfo.txt` |
| 0.3 | `([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)` | 判断是否管理员（影响部分审计项可采集性） | `Phase00_Env/admin_role.txt` |
| 0.4 | `Get-ExecutionPolicy -List` | 记录当前 PowerShell 执行策略 | `Phase00_Env/execution_policy.txt` |
| 0.5 | `New-Item -ItemType Directory -Path ".\Evidence_Package_<ts>"` 及子目录 | 创建证据包目录树 | 目录结构本身 |
| 0.6 | `Start-Transcript -Path ".\Evidence_Package_<ts>\00_Audit_Manifest\audit_transcript.txt"` | 开启全程会话转录，保证可溯源 | `audit_transcript.txt` |

### Phase 1 — D1 杀毒/恶意软件审计（预计 5–8 min）

| 步骤 | PowerShell / 原生命令 | 用途 | 证据文件 |
|------|----------------------|------|----------|
| 1.1 | `Get-MpComputerStatus \| Format-List` | Defender 实时保护、云保护、行为监控、版本状态 | `Phase01_AV/mp_computer_status.txt` |
| 1.2 | `Get-MpPreference` | Defender 偏好设置（排除路径、威胁默认操作等） | `Phase01_AV/mp_preference.txt` |
| 1.3 | `Get-MpThreatDetection` | 近期威胁检测记录 | `Phase01_AV/threat_detection.txt` |
| 1.4 | `Get-Service \| Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -eq 'Running' } \| Select-Object Name,DisplayName,StartType,Status` | 自启动运行中服务清单 | `Phase01_AV/auto_services.txt` |
| 1.5 | `Get-ScheduledTask \| Get-ScheduledTaskInfo \| Select-Object TaskName,State,LastRunTime,LastTaskResult` | 计划任务与最近执行结果 | `Phase01_AV/scheduled_tasks.txt` |
| 1.6 | `Get-CimInstance Win32_StartupCommand \| Select-Object Name,Command,Location,User` | 启动项 (Run/启动文件夹) | `Phase01_AV/startup_commands.txt` |
| 1.7 | `Get-Process \| Select-Object Id,Name,Path,Company,CPU,StartTime \| Sort-Object CPU -Descending` | 进程快照（路径缺失者需重点关注） | `Phase01_AV/process_snapshot.txt` |
| 1.8 | `Get-ChildItem -Path $env:SystemRoot\System32 -Recurse -ErrorAction SilentlyContinue \| Get-AuthenticodeSignature \| Where-Object { $_.Status -notin @('Valid','NotSigned') }` | 系统目录中签名异常二进制 | `Phase01_AV/unsigned_binaries.txt` |
| 1.9 | 若存在：`autoruns64.exe /accepteula -s *`（Sysinternals） | 自启动深度枚举（仅在已部署时调用） | `Phase01_AV/autoruns.txt` |

### Phase 2 — D2 补丁/漏洞审计（预计 3–5 min）

| 步骤 | 命令 | 用途 | 证据文件 |
|------|------|------|----------|
| 2.1 | `Get-HotFix \| Sort-Object InstalledOn` | 已安装修补程序清单 | `Phase02_Patches/hotfix_list.txt` |
| 2.2 | `Get-CimInstance Win32_QuickFixEngineering \| Select-Object HotFixID,InstalledOn,Description,InstalledBy` | WMI 视角的补丁清单（交叉验证） | `Phase02_Patches/qfe_list.txt` |
| 2.3 | `Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\Results\Detect' -ErrorAction SilentlyContinue \| Select-Object LastSuccessTime,LastExecutionTime` | 最近 Windows Update 检测时间 | `Phase02_Patches/wu_last_detect.txt` |
| 2.4 | `Get-MpComputerStatus \| Select-Object AntivirusEngineVersion,AntivirusSignatureLastUpdated,AntispywareSignatureLastUpdated` | Defender 病毒定义更新时效 | `Phase02_Patches/defender_signature.txt` |
| 2.5 | `systeminfo \| Select-String -Pattern 'Hotfix|OS Name|OS Version|System Type'` | 系统汇总信息 | `Phase02_Patches/systeminfo.txt` |

### Phase 3 — D3 配置基线审计（预计 5–8 min）

| 步骤 | 命令 | 用途 | 证据文件 |
|------|------|------|----------|
| 3.1 | `auditpol /get /category:*` | 系统审计策略（账户登录、对象访问、策略变更等） | `Phase03_Baseline/auditpol.txt` |
| 3.2 | `secedit /export /cfg ".\Evidence_Package_<ts>\Phase03_Baseline\local_security_policy.txt"` | 本地安全策略导出（只读导出，不修改） | `local_security_policy.txt` |
| 3.3 | `Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' -Name EnableLUA,ConsentPromptBehaviorAdmin,EnableInstallerDetection` | UAC 配置 | `Phase03_Baseline/uac_registry.txt` |
| 3.4 | `Get-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections` | RDP 启用状态 | `Phase03_Baseline/rdp_status.txt` |
| 3.5 | `netsh advfirewall show allprofiles state` | 各防火墙配置文件启用状态 | `Phase03_Baseline/firewall_state.txt` |
| 3.6 | `netsh advfirewall firewall show rule name=all` | 防火墙规则全量（只读） | `Phase03_Baseline/firewall_rules.txt` |
| 3.7 | `Get-CimInstance Win32_Account \| Select-Object Name,Domain,Disabled,Lockout,PasswordRequired,PasswordChangeable` | 账户基础属性 | `Phase03_Baseline/win32_accounts.txt` |

### Phase 4 — D4 网络暴露审计（预计 3–5 min，仅本机/本地链路）

| 步骤 | 命令 | 用途 | 证据文件 |
|------|------|------|----------|
| 4.1 | `Get-NetTCPConnection -State Listen \| Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,OwningProcess` | TCP 监听端口（本机视角） | `Phase04_Network/tcp_listeners.txt` |
| 4.2 | `Get-NetUDPEndpoint \| Select-Object LocalAddress,LocalPort,OwningProcess` | UDP 端点 | `Phase04_Network/udp_endpoints.txt` |
| 4.3 | `netstat -ano` | 经典网络连接表（交叉验证） | `Phase04_Network/netstat_ano.txt` |
| 4.4 | `Get-NetFirewallProfile \| Select-Object Name,Enabled,DefaultInboundAction,DefaultOutboundAction` | 防火墙配置文件 | `Phase04_Network/firewall_profiles.txt` |
| 4.5 | `Get-NetFirewallRule \| Where-Object { $_.Enabled -eq 'True' } \| Select-Object Name,DisplayName,Profile,Direction,Action,LocalPort,RemoteAddress` | 已启用防火墙规则 | `Phase04_Network/firewall_rules_enabled.txt` |
| 4.6 | `ipconfig /all` | 网络适配器、DNS、网关 | `Phase04_Network/ipconfig_all.txt` |
| 4.7 | `Get-NetRoute \| Select-Object DestinationPrefix,NextHop,InterfaceAlias,RouteMetric` | 路由表 | `Phase04_Network/route_table.txt` |
| 4.8 | `Get-NetConnectionProfile \| Select-Object Name,InterfaceAlias,IPv4Connectivity,NetworkCategory` | 网络连接分类（公有/专有） | `Phase04_Network/connection_profiles.txt` |
| 4.9 | `Test-NetConnection -ComputerName 127.0.0.1 -Port 445`（示例，仅回环） | 回环端口可达性探测（不外发） | `Phase04_Network/loopback_test.txt` |

> 禁止：对任何非本机/非本地链路地址发起主动扫描或爆破。

### Phase 5 — D5 权限/账户审计（预计 3–5 min）

| 步骤 | 命令 | 用途 | 证据文件 |
|------|------|------|----------|
| 5.1 | `whoami /groups; whoami /priv` | 当前用户身份与特权 | `Phase05_Accounts/whoami.txt` |
| 5.2 | `Get-LocalUser \| Select-Object Name,Enabled,PasswordLastSet,LastLogon,Lockout,PasswordExpires` | 本地用户与锁定/密码状态 | `Phase05_Accounts/local_users.txt` |
| 5.3 | `Get-LocalGroupMember -Group 'Administrators' \| Select-Object Name,PrincipalSource` | Administrators 组成员 | `Phase05_Accounts/admin_members.txt` |
| 5.4 | `Get-LocalGroup \| Select-Object Name,Description` | 本地组全量 | `Phase05_Accounts/local_groups.txt` |
| 5.5 | `Get-CimInstance Win32_GroupUser \| Select-Object GroupComponent,PartComponent` | WMI 组-用户映射（交叉验证） | `Phase05_Accounts/group_user_map.txt` |
| 5.6 | `Get-Acl -Path 'C:\Users' -ErrorAction SilentlyContinue \| Select-Object Owner,AccessToString` | 典型用户目录 ACL 快照 | `Phase05_Accounts/users_acl.txt` |
| 5.7 | `Get-Acl -Path 'C:\Windows\System32' -ErrorAction SilentlyContinue \| Select-Object Owner,AccessToString` | 系统目录 ACL 快照 | `Phase05_Accounts/system32_acl.txt` |

### Phase 6 — D6 日志审计（预计 5–10 min，视日志量而定）

| 步骤 | 命令 | 用途 | 证据文件 |
|------|------|------|----------|
| 6.1 | `wevtutil el` | 事件日志全量列表 | `Phase06_Logs/log_list.txt` |
| 6.2 | `Get-WinEvent -ListLog * \| Select-Object LogName,RecordCount,IsEnabled,LogType \| Sort-Object LogName` | 各日志启用状态与记录数 | `Phase06_Logs/log_status.txt` |
| 6.3 | `wevtutil epl Security ".\Evidence_Package_<ts>\Phase06_Logs\Security.evtx"` | 安全日志导出（原始 .evtx） | `Security.evtx` |
| 6.4 | `wevtutil epl System ".\Evidence_Package_<ts>\Phase06_Logs\System.evtx"` | 系统日志导出 | `System.evtx` |
| 6.5 | `wevtutil epl Application ".\Evidence_Package_<ts>\Phase06_Logs\Application.evtx"` | 应用程序日志导出 | `Application.evtx` |
| 6.6 | `wevtutil epl "Microsoft-Windows-Windows Defender/Operational" ".\Evidence_Package_<ts>\Phase06_Logs\Defender_Operational.evtx" -ErrorAction SilentlyContinue` | Defender 操作日志（若存在） | `Defender_Operational.evtx` |
| 6.7 | `wevtutil epl "Windows PowerShell" ".\Evidence_Package_<ts>\Phase06_Logs\PowerShell.evtx" -ErrorAction SilentlyContinue` | PowerShell 操作日志（若启用） | `PowerShell.evtx` |
| 6.8 | `Get-EventLog -LogName Security -Newest 2000 -ErrorAction SilentlyContinue \| Select-Object TimeGenerated,EntryType,Source,EventID,Message \| Format-Table -AutoSize` | 最近安全事件文本摘要 | `Phase06_Logs/security_recent.txt` |

### Phase 7 — D7 供应链/依赖审计（预计 5–10 min）

| 步骤 | 命令 | 用途 | 证据文件 |
|------|------|------|----------|
| 7.1 | `Get-ChildItem -Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall','HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall' \| ForEach-Object { Get-ItemProperty $_.PSPath } \| Select-Object DisplayName,DisplayVersion,Publisher,InstallDate` | 已安装程序清单（注册表卸载项，避开 Win32_Product 导致的重新校验风险） | `Phase07_SupplyChain/installed_programs.txt` |
| 7.2 | `Get-Package -ErrorAction SilentlyContinue \| Select-Object Name,Version,Source,ProviderName` | PackageManagement 视角的包清单 | `Phase07_SupplyChain/packages.txt` |
| 7.3 | 若存在：`wsl --list --verbose` | WSL 发行版与状态 | `Phase07_SupplyChain/wsl_status.txt` |
| 7.4 | 若存在：`docker ps -a; docker images` | Docker 容器与镜像（仅本机查询，不拉取） | `Phase07_SupplyChain/docker_status.txt` |
| 7.5 | 若存在：`Get-VM -ErrorAction SilentlyContinue \| Select-Object Name,State,CPUCount,MemoryAssigned` | Hyper-V 虚拟机状态 | `Phase07_SupplyChain/hyperv_vms.txt` |
| 7.6 | `Get-CimInstance Win32_PnPSignedDriver \| Select-Object DeviceName,DriverVersion,Manufacturer,IsSigned` | 驱动签名状态 | `Phase07_SupplyChain/drivers_signed.txt` |
| 7.7 | `Get-CimInstance -Namespace root\subscription -ClassName __EventConsumer -ErrorAction SilentlyContinue \| Select-Object Name,Creator,Delivered` | WMI 事件消费者（持久化检查点） | `Phase07_SupplyChain/wmi_consumers.txt` |
| 7.8 | 工作目录依赖扫描：`Get-ChildItem -Path . -Recurse -Include package.json,package-lock.json,requirements.txt,*.csproj,*.sln,*.go,*.mod -ErrorAction SilentlyContinue \| Select-Object FullName` | 本项目及常见开发依赖清单（供用户核验） | `Phase07_SupplyChain/local_dependencies.txt` |

### Phase 8 — D8 数据泄露风险审计（预计 3–5 min）

| 步骤 | 命令 | 用途 | 证据文件 |
|------|------|------|----------|
| 8.1 | `Get-BitLockerVolume -ErrorAction SilentlyContinue \| Select-Object MountPoint,VolumeStatus,ProtectionStatus,EncryptionPercentage` | BitLocker 加密状态 | `Phase08_DataLeak/bitlocker.txt` |
| 8.2 | `manage-bde -status C:`（若 BitLocker 模块不可用时的备选） | BitLocker 命令行状态 | `Phase08_DataLeak/manage_bde_status.txt` |
| 8.3 | `cipher /c /s:"$env:USERPROFILE" 2>$null` | EFS 加密文件列表（只读） | `Phase08_DataLeak/efs_encrypted_files.txt` |
| 8.4 | `net share` | 文件共享状态 | `Phase08_DataLeak/net_share.txt` |
| 8.5 | `Get-SmbShare -ErrorAction SilentlyContinue \| Select-Object Name,Path,Description` | SMB 共享详情 | `Phase08_DataLeak/smb_shares.txt` |
| 8.6 | `Get-CimInstance Win32_PageFileSetting \| Select-Object Name,InitialSize,MaximumSize` | 页面文件配置（敏感页面残留风险） | `Phase08_DataLeak/pagefile.txt` |
| 8.7 | `Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management' -Name HiberFileSizePercent -ErrorAction SilentlyContinue` | 休眠文件配置 | `Phase08_DataLeak/hiberfile_cfg.txt` |
| 8.8 | `Get-ChildItem -Path $env:TEMP -Recurse -ErrorAction SilentlyContinue \| Select-Object FullName,Length,LastWriteTime \| Sort-Object LastWriteTime -Descending \| Select-Object -First 100` | 临时目录最近文件快照 | `Phase08_DataLeak/temp_recent.txt` |
| 8.9 | `Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs' -ErrorAction SilentlyContinue` | 最近文档痕迹（注册表） | `Phase08_DataLeak/recent_docs.txt` |
| 8.10 | `Test-Path "$env:LOCALAPPDATA\Microsoft\OneDrive","$env:LOCALAPPDATA\Dropbox" -ErrorAction SilentlyContinue` | 常见云同步客户端存在性 | `Phase08_DataLeak/cloud_sync_presence.txt` |

### Phase 9 — 深度审计附加项：持久化排查与离线分析（预计 5–15 min）

| 步骤 | 命令 | 用途 | 证据文件 |
|------|------|------|----------|
| 9.1 | `Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run','HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce','HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce' -ErrorAction SilentlyContinue` | 运行项注册表（持久化入口） | `Phase09_Deep/run_registry.txt` |
| 9.2 | `Get-ChildItem -Path "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp","$env:APPDATA\Microsoft\Windows\Start Menu\Programs\StartUp" -ErrorAction SilentlyContinue` | 启动文件夹 | `Phase09_Deep/startup_folders.txt` |
| 9.3 | `Get-CimInstance Win32_Service \| Select-Object Name,DisplayName,StartMode,State,PathName,StartName` | 服务二进制路径与启动账号 | `Phase09_Deep/services_detail.txt` |
| 9.4 | `Get-FileHash -Path <证据包内每个原始输出文件> -Algorithm SHA256 \| Export-Csv ...` | 证据包文件 SHA-256 清单（完整性凭据，本地保留不外传） | `00_Audit_Manifest\evidence_manifest.csv` |
| 9.5 | 内存取证可用性评估：记录 `Get-Process` 树与 `procdump`（Sysinternals 若存在）可用性；否则在报告中标注“内存镜像需第三方取证工具，未覆盖” | 内存取证局限性记录 | `Phase09_Deep/memory_forensics_note.txt` |

### Phase 10 — 报告与证据包汇编（预计 3–5 min）

- 生成 `Security_Audit_Report_<ts>.md`（结构化审计报告，见第 4 节）
- 生成 `Remediation_Playbook_<ts>.md`（仅汇报修复建议、回滚步骤与影响面评估，不执行）
- 生成交互式复核清单（每条发现含：发现 ID、通过/失败/需人工复核、证据路径、建议优先级、用户决策栏位）
- 停止转录 (`Stop-Transcript`)，写入 `00_Audit_Manifest/audit_manifest.json`（执行摘要、开始/结束时间、各阶段耗时、阻塞记录）

---

## 3. 预计总耗时与资源

| 项目 | 预估 |
|------|------|
| 总耗时 | **约 35–65 分钟**（受事件日志大小与已安装程序数量影响） |
| CPU/内存 | 低负载；仅只读采集 |
| 磁盘空间 | 证据包预计 200 MB–2 GB（.evtx 日志占大头） |
| 权限需求 | 普通用户可执行大部分命令；管理员可完整采集 ACL、BitLocker、部分注册表与服务路径 |

## 4. 交付物规范（确认后生成）

### 4.1 证据包目录结构

```
Evidence_Package_<YYYYMMDD_HHmmss>/
├── 00_Audit_Manifest/
│   ├── audit_manifest.json        # 执行摘要、时间线、阻塞记录、校验清单
│   ├── audit_transcript.txt       # 全程 PowerShell 会话转录
│   └── evidence_manifest.csv      # 每份证据文件的 SHA-256 哈希（本地完整性凭据，不外传）
├── Phase00_Env/                   # 环境预检输出
├── Phase01_AV/                    # D1 杀毒/恶意软件
├── Phase02_Patches/               # D2 补丁/漏洞
├── Phase03_Baseline/              # D3 配置基线
├── Phase04_Network/               # D4 网络暴露
├── Phase05_Accounts/              # D5 权限/账户
├── Phase06_Logs/                  # D6 日志审计（含 .evtx 原始导出）
├── Phase07_SupplyChain/           # D7 供应链/依赖
├── Phase08_DataLeak/              # D8 数据泄露风险
├── Phase09_Deep/                  # 深度审计（持久化/离线分析）
└── Review_Checklist.md            # 交互式复核清单（用户逐项确认修复）
```

### 4.2 审计报告（Markdown，可转 HTML）

```
Security_Audit_Report_<ts>.md
├── 1. 执行摘要（Executive Summary）
├── 2. 审计范围、方法与工具链
├── 3. 风险等级分布（Critical / High / Medium / Low / Info）
├── 4. 逐项检查清单（通过 / 失败 / 需人工复核）
│   ├── 发现 ID | 维度 | 标题 | 等级 | 证据引用路径 | 采集命令与时间戳 | 修复建议优先级
├── 5. 修复优先级矩阵（与 Remediation_Playbook 对应）
├── 6. 已知局限与未覆盖项
└── 7. 审计签名与确认栏
```

### 4.3 修复剧本（只汇报，不执行）

```
Remediation_Playbook_<ts>.md
├── 每条发现：推荐修复动作 | 回滚步骤 | 影响面评估 | 是否需管理员提权 | 用户决策状态（待决/已批准/已拒绝）
└── 说明：本剧本仅供用户人工决策与执行，审计系统不自动执行任何修复
```

---

## 5. 阻塞与冲突处理机制

遇到权限不足、工具缺失、策略冲突或数据无法采集时，**立即中止当前项**，按以下标准化格式返回，等待用户决策后再重试或跳过：

```
[阻塞项] <发现 ID / 阶段步骤>
现象：<具体无法采集的命令与错误信息>
根因：<权限不足 / 工具未部署 / 策略禁用 / 数据源缺失>
可选方案：<A. 以管理员重试 / B. 改用替代原生命令 / C. 标记为“未覆盖”并写入已知局限 / D. 用户批准后安装已授权工具>
用户决策：待决
```

示例阻塞项：
- `Get-BitLockerVolume` 缺失 → BitLocker 模块未加载（Windows 10 Pro 通常应有，但可能被组策略禁用）→ 可选方案：用 `manage-bde -status` 备选，或标记未覆盖
- `docker` 不存在 → 未安装 Docker → 标记 D7 未覆盖，写入已知局限
- `secedit /export` 目录权限不足 → 改用审计目录子路径，或确认磁盘空间

---

## 6. 已知局限（执行前告知）

1. **内存取证**：Windows 原生不支持无第三方取证工具的完整物理内存镜像；仅做进程/服务快照与可用性评估，内存层列为“未覆盖（需 Sysinternals / 已授权取证工具补充）”。
2. **WSL/Docker/VM 内核层**：仅采集宿主层状态（wsl --list、docker images、Get-VM），不进入容器/虚拟机内部审计。
3. **加密卷**：未解锁的 BitLocker 卷内容不可读，仅记录卷状态。
4. **对外扫描**：严格限制在回环/本地链路，不覆盖局域网其他主机。
5. **第三方杀毒**：若未安装 Windows Defender 或使用第三方杀软，Defender 相关命令将返回空或“未启用”，仅记录状态。

---

## 7. 确认流程

1. 用户审阅本《审计执行计划》
2. 用户确认（或提出修改）：`确认执行` / `修改后执行` / `暂缓`
3. 确认后，按 Phase 0–10 顺序落地执行，每阶段完成后汇报进度与阻塞项
4. 全部完成后交付：`Security_Audit_Report_<ts>.md`、`Evidence_Package_<ts>/`、`Remediation_Playbook_<ts>.md`，并引导用户逐项复核修复决策

---

**请确认以上执行计划，或提出需要调整的阶段/命令/边界。确认后我将开始落地执行。**