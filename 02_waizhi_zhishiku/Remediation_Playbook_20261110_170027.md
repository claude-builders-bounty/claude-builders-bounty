# Windows 主机深度安全审计 — 修复剧本

**剧本编号**：RP-20261110-001  
**对应报告**：`Security_Audit_Report_20261110_170027.md`  
**证据包**：`Evidence_Package_20261110_170027/`  
**生成时间**：2026-11-10  
**执行模式**：**仅汇报建议，不执行** —— 本剧本供用户人工审阅与决策，审计系统不自动执行任何修复动作。每条修复均含推荐动作、回滚步骤、影响面评估、提权需求与用户决策状态（均初始为“待决”，由用户批准/拒绝后方可执行）。

---

## 使用说明

1. 用户逐条阅读，对每条发现设定决策状态：`待决` → `已批准` / `已拒绝`。
2. 对标记为“已批准”的条目，用户自行决定执行时机并自行操作（建议先在非生产环境或快照后验证）。
3. 所有需管理员提权的动作（标记“是”），必须以“以管理员身份运行”的 PowerShell/CMD 执行。
4. 执行前建议先建立系统还原点或备份关键注册表项。

---

## P0 — 立即处理（高危）

### P0-1 · F-01：RDP 服务 (TermService) 面向全接口暴露 (3389)

**证据**：`Evidence_Package_20261110_170027\Phase04_Network\tcp_listeners.txt`（3389 在 0.0.0.0 和 :: 监听，OwningProcess 1628=TermService）、`Phase01_AV\auto_services.txt`（TermService Automatic/Running）、`Phase03_Baseline\rdp_status.txt`。

**推荐修复动作**：
- 若业务不需要远程桌面：以管理员身份执行 `Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -Value 1`，并停止/禁用 TermService 服务；或通过 `netsh advfirewall firewall add rule` 限制 3389 仅允许受信 IP 段入站。
- 若需要保留 RDP：仅绑定至内网/VPN 接口，启用网络级身份验证 (NLA)，并限制来源 IP。

**回滚步骤**：
- 将 `fDenyTSConnections` 改回 0；重新启动 TermService (`Start-Service TermService`)；删除临时防火墙规则。

**影响面评估**：
- 禁用 RDP 将禁止通过远程桌面协议登录本机；若本机仅靠 RDP 远程管理，可能导致远程管理中断（请改用本地控制台或其他管理通道）。

**是否需管理员提权**：是  
**用户决策状态**：待决

---

### P0-2 · F-02：SMB (445)、RPC (135)、NetBIOS (139) 面向全接口暴露

**证据**：`Phase04_Network\tcp_listeners.txt`（445/135 在 0.0.0.0 和 :: 监听，OwningProcess 4=系统/1408=RPCSS）、`Phase04_Network\netstat_ano.txt`；`Phase08_DataLeak\net_share.txt`（仅行政共享 ADMIN$/C$/D$/IPC$）。

**推荐修复动作**：
- 若本机不向局域网提供文件共享：以管理员身份通过 `netsh advfirewall firewall add rule` 在所有配置文件下阻止入站 445、135、139；或在服务层面停止 `LanmanServer`（Server）服务（仅当不需要本机被访问时）。
- 若需要局域网共享：将共享限制在受信任内网段，并禁用不必要的默认共享（C$/D$/ADMIN$ 为系统默认，建议保留但通过防火墙控制访问）。

**回滚步骤**：
- 删除添加的阻止规则；若停止了 LanmanServer，以管理员执行 `Start-Service LanmanServer` 并设启动类型为 Automatic。

**影响面评估**：
- 阻止 445/135/139 将阻断本机的文件/打印共享与远程 RPC 调用；局域网内其他主机将无法访问本机共享资源，部分依赖本机 SMB 的旧式应用可能受影响。

**是否需管理员提权**：是  
**用户决策状态**：待决

---

## P1 — 近期处理（中危）

### P1-1 · F-03：防火墙默认动作未配置且具体规则不可核验

**证据**：`Phase03_Baseline\firewall_state.txt`（三个配置文件 DefaultInboundAction/OutboundAction 均为 NotConfigured）；`Phase04_Network\firewall_rules_enabled.txt`（获取失败，Access is denied）。

**推荐修复动作**：
- 以管理员身份执行 `Get-NetFirewallProfile | Set-NetFirewallProfile -DefaultInboundAction Block -DefaultOutboundAction Block`（或按业务需求设为 Block），再添加显式允许规则。
- 以管理员身份导出完整防火墙规则清单供核验：`Get-NetFirewallRule | Where-Object {$_.Enabled -eq 'True'} | Select-Object Name,Direction,Action,LocalPort,RemoteAddress`。

**回滚步骤**：
- 将 DefaultInbound/OutboundAction 还原为 NotConfigured；移除新增的显式规则。

**影响面评估**：
- 默认入站拦截可能阻断合法的入站服务（如本机作为文件/打印服务器时），需在开启前梳理所需端口并添加允许规则。

**是否需管理员提权**：是  
**用户决策状态**：待决

---

### P1-2 · F-04：本地 Administrator 账户已启用并最近登录

**证据**：`Phase05_Accounts\local_users.txt`（Administrator，Enabled=True，LastLogon 2026-11-10 12:24:31）；`Phase05_Accounts\admin_members.txt`（Administrators 组仅含 Administrator）。

**推荐修复动作**：
- 若不需要本地 Administrator 日常使用：以管理员身份禁用该账户 `Disable-LocalUser -Name Administrator`，并创建一个标准用户账户用于日常运行（提权时再用 UAC）。
- 若必须保留：强制强密码策略、账户锁定策略，并考虑启用智能卡/Windows Hello 登录；避免以 Administrator 账户日常联网使用。

**回滚步骤**：
- `Enable-LocalUser -Name Administrator`；恢复原密码策略。

**影响面评估**：
- 禁用 Administrator 后，以该账户的服务/任务可能受影响；建议预先保留另一个具备管理员权限的账用于紧急恢复，防止锁死。

**是否需管理员提权**：是  
**用户决策状态**：待决

---

### P1-3 · F-05：大量第三方自启动项，持久化面扩大

**证据**：`Phase01_AV\startup_commands.txt`、`Phase09_Deep\run_registry.txt`（HKLM/HKCU Run 含 百度网盘、钉钉、Coze、TapTap、OneDrive、火绒等）、`Phase09_Deep\startup_folders.txt`。

**推荐修复动作**：
- 逐条审核 Run 注册表项与启动文件夹，禁用不需要的第三方自启动：`Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name <项名>`（或 HKLM 对应路径，需管理员）。
- 审核计划任务 (`Get-ScheduledTask`) 中的非必要第三方任务并禁用。
- 优先关注来源不明、路径缺失或位于用户可写目录的条目。

**回滚步骤**：
- 重新添加被删除的注册表值/快捷方式；重新启用计划任务。

**影响面评估**：
- 禁用后相关应用不会随系统自动启动，用户需手动启动；对企业管理/同步类客户端（如 OneDrive、钉钉）可能影响协同办公，建议按业务需要保留。

**是否需管理员提权**：HKCU 项否，HKLM 项是  
**用户决策状态**：待决

---

### P1-4 · F-06：Defender WMI 接口不可用，防毒状态未知；系统已安装火绒安全软件

**证据**：`Phase01_AV\mp_computer_status.txt`（RPC 0x800106ba 失败）；`Phase02_Patches\defender_signature.txt`（获取失败）；`Phase07_SupplyChain\installed_programs.txt`（火绒安全软件 6.0.12.3）。

**推荐修复动作**：
- 确认火绒与 Windows Defender 的关系：若以火绒为主防，建议在 Defender 中关闭实时保护以避免冲突（或反之，统一为单一防毒产品），避免两款产品同时实时扫描导致性能与稳定性问题。
- 若决定以 Defender 为主：卸载或关闭火绒实时防护，并以管理员身份验证 `Get-MpComputerStatus` 可正常返回，开启云保护与实时保护，更新病毒定义。
- 无论哪种，确保主机始终运行一款处于启用状态、定义最新的防毒产品。

**回滚步骤**：
- 重新启用被关闭的防毒产品；恢复原排除路径与默认威胁处理动作。

**影响面评估**：
- 切换主防产品期间可能存在短暂无防护窗口；建议在切换时断开网络或在低风险时段操作。

**是否需管理员提权**：是  
**用户决策状态**：待决

---

## P2 — 待管理员复核（日志与审计盲区）

### P2-1 · F-07 / B-08 / B-09：Security 事件日志不可读，审计盲区

**证据**：`Phase06_Logs\log_status.txt`（大量 unauthorized）；`Phase06_Logs\Security.evtx`（导出失败，未生成）；`Phase06_Logs\security_recent.txt`（获取失败）。

**推荐修复动作**：
- 以管理员身份重新导出关键日志：`wevtutil epl Security <路径>\Security.evtx`、`wevtutil epl System <路径>\System.evtx`、`wevtutil epl Application <路径>\Application.evtx`。
- 以管理员身份检查并启用审计策略：`auditpol /get /category:*`，按需开启账户登录、对象访问、策略变更类审计。
- 确认 PowerShell 操作日志与 Defender 操作日志是否启用（已尝试导出但因参数/权限失败）。

**回滚步骤**：
- 审计策略变更可通过 `auditpol /restore` 或手动关闭对应类别恢复。

**影响面评估**：
- 开启详细审计会增加事件日志卷与轻微磁盘 IO，需确保日志容量足够并配置覆盖策略。

**是否需管理员提权**：是  
**用户决策状态**：待决

---

## P3 — 建议核验（信息类）

### P3-1 · F-08：Windows Update 检测注册表为空，10 个 Hotfix 已安装

**推荐动作**：手动触发 Windows Update 检查，确认系统处于最新补丁状态；记录最近检测时间以便后续审计。  
**提权**：是（部分更新需管理员）  
**决策状态**：待决

### P3-2 · F-10：BitLocker 模块不可用，卷加密状态未知

**推荐动作**：确认系统盘是否已启用 BitLocker 加密；若未加密且存有敏感数据，建议开启 BitLocker 或使用 EFS 加密敏感文件。  
**提权**：是  
**决策状态**：待决

### P3-3 · F-09：WSL 运行中，Docker 未安装，Hyper-V 管理工具缺失

**推荐动作**：若不使用 WSL，可考虑禁用 WSLService 以缩小攻击面；虚拟化层仅审计宿主，未进入内部，如有虚拟机需单独审计。  
**提权**：是  
**决策状态**：待决

### P3-4 · F-11：共享为行政共享，临时目录/最近文档痕迹存在

**推荐动作**：定期清理 `%TEMP%` 与最近文档痕迹；对敏感工作目录考虑 EFS 加密。  
**提权**：否  
**决策状态**：待决

---

## 用户决策汇总表

| 条目 | 发现 ID | 决策 (待决/已批准/已拒绝) | 用户签名 | 日期 |
|------|---------|--------------------------|----------|------|
| P0-1 | F-01 | 待决 | | |
| P0-2 | F-02 | 待决 | | |
| P1-1 | F-03 | 待决 | | |
| P1-2 | F-04 | 待决 | | |
| P1-3 | F-05 | 待决 | | |
| P1-4 | F-06 | 待决 | | |
| P2-1 | F-07/B-08/B-09 | 待决 | | |
| P3-1 | F-08 | 待决 | | |
| P3-2 | F-10 | 待决 | | |
| P3-3 | F-09 | 待决 | | |
| P3-4 | F-11 | 待决 | | |

---

## 免责声明

本剧本仅基于只读审计采集的证据生成，不执行任何修复；所有修复动作由用户自行决策与执行，执行后果由用户承担。建议在执行任何需提权动作前创建系统还原点。
