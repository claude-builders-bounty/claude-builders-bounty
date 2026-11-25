# Windows 主机深度安全审计报告

**报告编号**：SA-20261110-001  
**报告时间**：2026-11-10 (生成于审计执行完成后)  
**目标宿主**：DESKTOP-ER260RG — Microsoft Windows 10 Pro 10.0.19045 Build 19045, x64-based PC  
**执行主体**：Claude Code 多智能体系统（PowerShell 原生只读采集，非提权管理员令牌）  
**审计依据**：《审计执行计划》AUDIT_EXECUTION_PLAN_20261110.md，Phase 0–10  
**证据包**：`Evidence_Package_20261110_170027/`（含 64 份原始采集文件与 SHA-256 完整性清单）  
**审计模式**：只读采集，无自动修复，无外发数据，网络动作严格限制在回环/本地链路

---

## 1. 执行摘要 (Executive Summary)

本次审计对本机 Windows 10 Pro 主机开展了八大审计维度（D1 杀毒/恶意软件、D2 补丁/漏洞、D3 配置基线、D4 网络暴露、D5 权限/账户、D6 日志审计、D7 供应链/依赖、D8 数据泄露风险）以及第 9 阶段深度附加项（持久化排查与离线分析）的只读安全审计。

**核心发现**：
- **High（高危）2 条**：远程桌面服务 (TermService) 以“自动启动”运行且 3389 端口在 `0.0.0.0/::` 全接口监听；SMB (445)、RPC (135)、NetBIOS (139) 同样在全接口监听，远程接入与横向移动攻击面显著。
- **Medium（中危）4 条**：防火墙三个配置文件默认入站/出站动作为 `NotConfigured` 且具体规则因权限不足不可核验；本地 Administrator 账户已启用并最近登录；存在大量第三方自启动项（含百度网盘、钉钉、Coze、TapTap 等），持久化面扩大；Defender WMI 接口不可用（疑被第三方杀毒火绒占用），防毒状态未知。
- **Info/Low（提示/低危）6 条**：Security 事件日志不可访问（审计盲区）；10 个修补程序已安装但 Windows Update 检测注册表为空；WSL 与 VMware 存在；BitLocker 模块不可用；临时目录/最近文档痕迹存在。
- **阻塞项 12 条**：因普通用户权限不足、工具未部署或数据源缺失，部分采集项未能完成，已标记并列入本报告第 6 节。

**综合评价**：主机暴露在局域网可达的远程服务（RDP/SMB/RPC），防护策略（防火墙默认动作、Defender 状态）因权限限制无法完整核验，审计日志（Security 通道）不可读，形成“暴露面大、防护态势未知、审计盲区”的组合风险。建议用户优先处理 High 条目，并以管理员身份重新采集被阻塞项后再做最终定夺。

---

## 2. 审计范围、方法与工具链

### 2.1 审计范围

| 维度 | 简称 | 核心检查点 |
|------|------|-----------|
| D1 | 杀毒/恶意软件 | Defender 状态、威胁检测记录、自启动服务/计划任务/启动项、未签名二进制 |
| D2 | 补丁/漏洞 | 已安装修补程序 (Get-HotFix)、Windows Update 扫描时间、Defender 病毒定义版本 |
| D3 | 配置基线 | 审计策略 (auditpol)、本地安全策略 (secedit)、UAC、RDP、防火墙策略、账户属性 |
| D4 | 网络暴露 | 监听端口/活跃连接 (netstat/Get-NetTCPConnection)、防火墙规则、网络配置、回环探测 |
| D5 | 权限/账户 | 本地用户/组、Administrators 组成员、账户锁定/密码策略、特权列表、敏感目录 ACL |
| D6 | 日志审计 | 事件日志列表与容量 (wevtutil)、Security/System/Application/Defender/PowerShell 日志导出 |
| D7 | 供应链/依赖 | 已安装程序 (注册表卸载项)、WSL/Docker/Hyper-V 状态、驱动签名、WMI 事件消费者、本项目依赖 |
| D8 | 数据泄露风险 | BitLocker 状态、EFS 加密文件、文件共享 (net share)、页面文件/休眠文件、临时目录/最近文档、云同步客户端 |

### 2.2 方法与约束

- 采集模式：只读，不执行任何自动修复、配置变更或补丁安装（硬约束）。
- 数据边界：不上传/外传主机敏感数据；文件哈希仅作为本地完整性凭据。
- 网络边界：仅本机回环 (127.0.0.1/::1) 与本地链路，禁止对外主动扫描。
- 权限模式：普通用户身份执行（`IsAdmin: False`，UAC 受限令牌），需管理员权限的采集项遇阻后标记为阻塞项。

### 2.3 工具链

PowerShell 原生 cmdlet：`Get-MpComputerStatus`、`Get-MpPreference`、`Get-HotFix`、`Get-CimInstance`、`auditpol`、`secedit`、`netsh advfirewall`、`Get-NetTCPConnection`、`Get-LocalUser`/`Get-LocalGroup`、`Get-Acl`、`wevtutil`、`Get-WinEvent`、`Get-BitLockerVolume`、`cipher`、`net share`、`Get-FileHash`、`Start-Transcript` 等。

---

## 3. 风险等级分布

| 等级 | 数量 | 分布说明 |
|------|------|----------|
| Critical | 0 | 无 |
| High | 2 | 远程服务 (RDP/SMB/RPC) 面向所有网络接口暴露 |
| Medium | 4 | 防火墙默认动作未配置/不可核验；Administrator 账户启用；第三方自启动项过多；Defender 状态未知 |
| Low | 1 | 当前以 UAC 受限令牌运行（正常行为，提示） |
| Info | 6 | 状态记录与已知局限（日志盲区、补丁状态、WSL/VMware、BitLocker 不可用等） |
| 阻塞项 | 12 | 因权限/工具/数据源未能采集，列入第 6 节 |

---

## 4. 逐项检查清单

| 发现 ID | 维度 | 标题 | 等级 | 证据引用路径 | 采集命令与时间戳 | 修复建议优先级 |
|---------|------|------|------|-------------|-----------------|---------------|
| F-01 | D4 / D1 | RDP 服务 (TermService, 3389) 在 `0.0.0.0/::` 全接口监听，处于自动启动运行状态 | High | `Phase04_Network\tcp_listeners.txt`、`Phase01_AV\auto_services.txt` | `Get-NetTCPConnection -State Listen`；`Get-Service ...` | 立即 |
| F-02 | D4 | SMB (445)、RPC (135)、NetBIOS (139) 在 `0.0.0.0/::` 全接口监听 | High | `Phase04_Network\tcp_listeners.txt`、`Phase04_Network\netstat_ano.txt` | `Get-NetTCPConnection -State Listen`；`netstat -ano` | 立即 |
| F-03 | D3 / D4 | 防火墙 Domain/Private/Public 三配置文件 DefaultInbound/OutboundAction 为 `NotConfigured`；`Get-NetFirewallRule` 被拒绝 (Access is denied)，具体规则不可核验 | Medium | `Phase03_Baseline\firewall_state.txt`、`Phase04_Network\firewall_profiles.txt` | `netsh advfirewall show allprofiles state`；`Get-NetFirewallRule` | 近期 |
| F-04 | D5 | 本地账户 `Administrator` 已启用，最近登录时间 2026-11-10 12:24:31；Administrators 组仅包含该账户 | Medium | `Phase05_Accounts\local_users.txt`、`Phase05_Accounts\admin_members.txt` | `Get-LocalUser`；`Get-LocalGroupMember -Group 'Administrators'` | 近期 |
| F-05 | D1 / D7 / D9 | 注册表 Run 项及启动文件夹存在大量第三方自启动（百度网盘、钉钉、Coze、TapTap、OneDrive、火绒等），持久化面扩大 | Medium | `Phase01_AV\startup_commands.txt`、`Phase09_Deep\run_registry.txt`、`Phase09_Deep\startup_folders.txt` | `Get-ItemProperty ...\Run`；`Get-CimInstance Win32_StartupCommand` | 近期 |
| F-06 | D1 / D2 | `Get-MpComputerStatus` 返回 RPC 错误 (0x800106ba)，Defender 状态/病毒定义版本未知；系统已安装第三方杀毒“火绒安全软件 6.0.12.3” | Medium | `Phase01_AV\mp_computer_status.txt`、`Phase02_Patches\defender_signature.txt`、`Phase07_SupplyChain\installed_programs.txt` | `Get-MpComputerStatus`；`Get-MpPreference` | 近期 |
| F-07 | D6 | Security 事件日志及多个系统通道日志不可访问 (unauthorized / Access is denied)；`wevtutil epl Security` 导出失败 | Low | `Phase06_Logs\log_status.txt`、`Phase06_Logs\Security.evtx` (未生成) | `wevtutil epl Security ...`；`Get-EventLog -LogName Security` | 待管理员复核 |
| F-08 | D2 | 系统已安装 10 个 Hotfix，但 Windows Update 检测注册表项为空，无法确认最近检测时间 | Info | `Phase02_Patches\systeminfo.txt`、`Phase02_Patches\wu_last_detect.txt` | `systeminfo`；`Get-ItemProperty ...\WindowsUpdate\...\Detect` | 建议核验 |
| F-09 | D7 | WSL 服务 (WSLService) 处于运行状态；Docker 未安装 (`docker` 命令不存在)；Hyper-V cmdlet (`Get-VM`) 不可用 | Info | `Phase01_AV\auto_services.txt`、`Phase07_SupplyChain\wsl_status.txt`、`Phase07_SupplyChain\docker_status.txt` | `wsl --list --verbose`；`docker ps -a`；`Get-VM` | 无需立即处理 |
| F-10 | D8 | BitLocker 模块不可用 (`Get-BitLockerVolume` 缺失，`manage-bde -status` 退出码 3)，加密卷状态未知 | Info | `Phase08_DataLeak\bitlocker.txt`、`Phase08_DataLeak\manage_bde_status.txt` | `Get-BitLockerVolume`；`manage-bde -status C:` | 建议核验 |
| F-11 | D8 | 共享文件夹仅为行政共享 (ADMIN$/C$/D$/IPC$)；临时目录及最近文档注册表痕迹存在 | Info | `Phase08_DataLeak\net_share.txt`、`Phase08_DataLeak\smb_shares.txt`、`Phase08_DataLeak\temp_recent.txt`、`Phase08_DataLeak\recent_docs.txt` | `net share`；`Get-SmbShare`；`Get-ChildItem $env:TEMP` | 无需立即处理 |
| F-12 | D5 | 当前用户属于 Administrators 组但以 UAC 受限令牌运行 (`IsAdmin: False`)，属正常行为 | Info | `Phase00_Env\admin_role.txt`；`Phase05_Accounts\whoami.txt` | `([Security.Principal.WindowsPrincipal]...).IsInRole(Administrator)` | 无需处理 |

### 阻塞项登记表 (B-系列)

| 阻塞 ID | 阶段/步骤 | 现象 | 根因 | 可选方案 | 用户决策 |
|---------|-----------|------|------|----------|----------|
| B-01 | Phase 1.1 | `Get-MpComputerStatus` 抛出 CimException HRESULT 0x800106ba | RPC 服务不可用 / Defender WMI 被占用 (疑火绒) | A. 改用 `Get-MpPreference`（已部分成功）；C. 标记 Defender 状态未知 | 待决 |
| B-02 | Phase 1.8 | System32 签名异常二进制扫描后台任务失败 (exit 1) | 扫描超时/权限受限 | C. 标记未覆盖 | 待决 |
| B-03 | Phase 3.1 | `auditpol /get /category:*` 返回 0x00000522 (所需特权未持有) | 普通用户缺少审计策略读取特权 | A. 以管理员重试 | 待决 |
| B-04 | Phase 3.2 | `secedit /export` 返回 228 (权限不足) | 需本地管理员 | A. 以管理员重试 | 待决 |
| B-05 | Phase 4.5 | `Get-NetFirewallRule` 抛出 Access is denied | 普通用户无权读取防火墙规则 | A. 以管理员重试 | 待决 |
| B-06 | Phase 5.1 | `whoami /groups` 被 WSL 路径 `/usr/bin/whoami` 拦截，不支持 Windows 参数 | PATH 优先级问题 | B. 改用 `[Security.Principal.WindowsIdentity]` 原生方式（已补采集） | 已处理 |
| B-07 | Phase 2.3 | Windows Update 检测注册表项为空 | 数据源缺失 / 未记录检测时间 | C. 标记为 Info 状态记录 | 已记录 |
| B-08 | Phase 6.3 / 6.6 / 6.7 | `wevtutil epl Security` / Defender/PowerShell 日志导出失败 (Access denied / 87 参数错误) | 普通用户无权读取 Security 日志；evtx 导出参数限制 | A. 以管理员重试；C. 标记审计盲区 | 待决 |
| B-09 | Phase 6.8 | `Get-EventLog -LogName Security` 抛出 SecurityException (注册表访问被拒) | 权限不足 | A. 以管理员重试 | 待决 |
| B-10 | Phase 7.4 / 7.5 | `docker`、`Get-VM` 命令/模块不存在 | Docker 未安装；Hyper-V 管理工具未安装 | C. 标记 D7 部分未覆盖（宿主层 WSL 已采集） | 已记录 |
| B-11 | Phase 8.1 / 8.2 | `Get-BitLockerVolume` 模块缺失；`manage-bde -status` 退出码 3 | BitLocker 管理模块未加载 / 未启用 | C. 标记加密状态未知 | 待决 |
| B-12 | Phase 8.6 / 8.7 | 页面文件/休眠文件配置读取为空或失败 | 数据源为空或权限 | C. 标记为状态记录 | 已记录 |

---

## 5. 修复优先级矩阵（与 Remediation_Playbook 对应）

| 优先级 | 发现 ID | 建议动作摘要 | 是否需管理员 |
|--------|---------|-------------|-------------|
| P0 (立即) | F-01 | 禁用/重配置 RDP (TermService) 或限制其绑定接口；仅在必要时启用，并通过防火墙限制来源 | 是 |
| P0 (立即) | F-02 | 禁用不需要的 SMB/RPC/NetBIOS 外部监听，或通过防火墙限制至受信网段 | 是 |
| P1 (近期) | F-03 | 以管理员身份读取并加固防火墙默认动作（入站默认拦截）与具体规则 | 是 |
| P1 (近期) | F-04 | 禁用未使用的本地 Administrator 账户，或强制其强密码与 MFA/智能卡登录 | 是 |
| P1 (近期) | F-05 | 审核并禁用不需要的第三方自启动项（Run 注册表、启动文件夹、计划任务） | 否/是 |
| P1 (近期) | F-06 | 确认火绒与 Defender 关系，统一防毒策略，恢复 Defender 可用性或明确替代方案 | 是 |
| P2 (待管理员复核) | F-07 / B-08 / B-09 | 以管理员身份导出 Security 及关键日志，启用审计策略 | 是 |
| P3 (建议核验) | F-08 / F-10 / F-11 | 确认 Windows Update 检测状态；确认 BitLocker 加密状态；清理敏感临时文件 | 是/否 |

---

## 6. 已知局限与未覆盖项

1. **内存取证**：Windows 原生不支持无第三方取证工具的完整物理内存镜像；仅采集进程/服务快照，内存层列为“未覆盖”。
2. **权限限制**：以普通用户身份执行，Security 事件日志、auditpol、secedit、防火墙规则、BitLocker、WMI 安全通道等多项采集受阻，需以管理员身份重试后方可完整定夺。
3. **WSL/Docker/VM 内核层**：仅采集宿主层状态（WSLService 运行中、Docker 未安装、Hyper-V cmdlet 不可用），未进入容器/虚拟机内部审计。
4. **第三方杀毒**：已安装火绒安全软件，Defender WMI 接口不可用，Defender 实际防护状态无法通过原生接口确认。
5. **对外扫描**：严格限制在回环/本地链路，未覆盖局域网其他主机。
6. **未签名二进制扫描**：System32 递归签名扫描因超时/失败未完成，列为未覆盖。

---

## 7. 审计签名与确认栏

| 项目 | 内容 |
|------|------|
| 审计执行人 | Claude Code 多智能体系统（PowerShell 原生工具链） |
| 执行开始 | 2026-11-10 17:00:27 |
| 执行结束 | 报告生成时 (2026-11-10) |
| 证据包 | `Evidence_Package_20261110_170027/`，64 份文件，SHA-256 见 `00_Audit_Manifest\evidence_manifest.csv` |
| 完整性凭据 | 见证据包 `00_Audit_Manifest\evidence_manifest.csv`（本地保留，不外发） |
| 用户确认（可否合并/接受风险） | □ 接受当前风险状态，按剧本逐项决策 □ 要求以管理员重新采集阻塞项后再决策 |
| 审计签名 | ____________________ 日期：____________ |

---

**后续**：配套修复剧本见 `Remediation_Playbook_20261110_170027.md`（仅汇报建议、回滚步骤与影响面，不自动执行）。交互式复核清单见证据包根目录 `Review_Checklist.md`。
