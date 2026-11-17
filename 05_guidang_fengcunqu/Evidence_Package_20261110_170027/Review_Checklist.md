# Windows 主机深度安全审计 — 交互式复核清单

**证据包**：`Evidence_Package_20261110_170027/`  
**对应报告**：`Security_Audit_Report_20261110_170027.md`  
**对应剧本**：`Remediation_Playbook_20261110_170027.md`  
**使用说明**：对每条发现，在“用户决策”列填写 `待决 / 已批准 / 已拒绝 / 需人工复核`；对阻塞项填写 `待重试 / 已标记未覆盖 / 待用户决策`。本清单不自动执行任何修复。

---

## A. 发现项复核 (F-系列)

| 发现 ID | 维度 | 标题 | 等级 | 证据路径 | 建议优先级 | 用户决策 |
|---------|------|------|------|----------|-----------|----------|
| F-01 | D4 / D1 | RDP 服务 (TermService, 3389) 在 `0.0.0.0/::` 全接口监听，自动启动运行 | High | `Phase04_Network\tcp_listeners.txt`、`Phase01_AV\auto_services.txt` | 立即 | |
| F-02 | D4 | SMB (445)、RPC (135)、NetBIOS (139) 在 `0.0.0.0/::` 全接口监听 | High | `Phase04_Network\tcp_listeners.txt`、`Phase04_Network\netstat_ano.txt` | 立即 | |
| F-03 | D3 / D4 | 防火墙三配置文件 DefaultInbound/OutboundAction 为 NotConfigured；具体规则不可核验 (Access is denied) | Medium | `Phase03_Baseline\firewall_state.txt`、`Phase04_Network\firewall_profiles.txt` | 近期 | |
| F-04 | D5 | 本地 Administrator 已启用，最近登录 2026-11-10；Administrators 组仅含该账户 | Medium | `Phase05_Accounts\local_users.txt`、`Phase05_Accounts\admin_members.txt` | 近期 | |
| F-05 | D1 / D7 / D9 | 注册表 Run 项与启动文件夹存在大量第三方自启动（百度网盘、钉钉、Coze、TapTap、OneDrive、火绒等） | Medium | `Phase01_AV\startup_commands.txt`、`Phase09_Deep\run_registry.txt`、`Phase09_Deep\startup_folders.txt` | 近期 | |
| F-06 | D1 / D2 / D7 | Get-MpComputerStatus 失败 (0x800106ba)；Defender 状态未知；已安装火绒安全软件 6.0.12.3 | Medium | `Phase01_AV\mp_computer_status.txt`、`Phase07_SupplyChain\installed_programs.txt` | 近期 | |
| F-07 | D6 | Security 事件日志不可读 (unauthorized / Access is denied)；审计盲区 | Low | `Phase06_Logs\log_status.txt` (`Security.evtx` 未生成) | 待管理员复核 | |
| F-08 | D2 | 系统已安装 10 个 Hotfix，但 Windows Update 检测注册表项为空 | Info | `Phase02_Patches\systeminfo.txt`、`Phase02_Patches\wu_last_detect.txt` | 建议核验 | |
| F-09 | D7 | WSLService 运行中；Docker 未安装；Hyper-V 管理工具不可用 | Info | `Phase01_AV\auto_services.txt`、`Phase07_SupplyChain\wsl_status.txt`、`Phase07_SupplyChain\docker_status.txt` | 无需立即处理 | |
| F-10 | D8 | BitLocker 模块不可用，卷加密状态未知 | Info | `Phase08_DataLeak\bitlocker.txt`、`Phase08_DataLeak\manage_bde_status.txt` | 建议核验 | |
| F-11 | D8 | 共享仅为行政共享 (ADMIN$/C$/D$/IPC$)；临时目录/最近文档痕迹存在 | Info | `Phase08_DataLeak\net_share.txt`、`Phase08_DataLeak\temp_recent.txt` | 无需立即处理 | |
| F-12 | D5 | 当前为 UAC 受限令牌 (IsAdmin: False)，正常行为 | Info | `Phase00_Env\admin_role.txt`、`Phase05_Accounts\whoami.txt` | 无需处理 | |

---

## B. 阻塞项复核 (B-系列)

| 阻塞 ID | 阶段/步骤 | 现象 | 根因 | 可选方案 | 用户决策 |
|---------|-----------|------|------|----------|----------|
| B-01 | Phase 1.1 | Get-MpComputerStatus RPC 0x800106ba | Defender WMI 不可用/被占用 | A 改用 Get-MpPreference / C 标记状态未知 | |
| B-02 | Phase 1.8 | System32 签名异常二进制扫描失败 (exit 1) | 超时/权限 | C 标记未覆盖 | |
| B-03 | Phase 3.1 | auditpol 0x00000522 (特权不足) | 普通用户 | A 以管理员重试 | |
| B-04 | Phase 3.2 | secedit /export 228 (权限不足) | 需本地管理员 | A 以管理员重试 | |
| B-05 | Phase 4.5 | Get-NetFirewallRule Access is denied | 普通用户 | A 以管理员重试 | |
| B-06 | Phase 5.1 | whoami /groups 被 WSL 路径拦截 | PATH 优先级 | B 已用 PowerShell 原生方式补采集 | 已处理 |
| B-07 | Phase 2.3 | Windows Update 检测注册表为空 | 数据源缺失 | C 标记为 Info | 已记录 |
| B-08 | Phase 6.3/6.6/6.7 | wevtutil epl Security/Defender/PowerShell 导出失败 | 权限/参数 | A 以管理员重试 / C 标记盲区 | |
| B-09 | Phase 6.8 | Get-EventLog Security SecurityException | 权限不足 | A 以管理员重试 | |
| B-10 | Phase 7.4/7.5 | docker / Get-VM 不存在 | Docker 未装 / Hyper-V 工具缺失 | C 标记 D7 部分未覆盖 | 已记录 |
| B-11 | Phase 8.1/8.2 | Get-BitLockerVolume 缺失；manage-bde 退出码 3 | 模块未加载 | C 标记加密状态未知 | |
| B-12 | Phase 8.6/8.7 | 页面文件/休眠文件配置读取为空 | 数据源为空 | C 状态记录 | 已记录 |

---

## C. 证据包完整性

- 证据文件总数：64 份（不含 evidence_manifest.csv 本身）
- SHA-256 完整性清单：`00_Audit_Manifest\evidence_manifest.csv`
- 全程会话转录：`00_Audit_Manifest\audit_transcript.txt`

---

**审计完成确认**：  
用户签名：____________________  日期：____________  
“以上发现已逐项复核，决策状态已填写，准备按 Remediation_Playbook 逐项执行或排期。”
