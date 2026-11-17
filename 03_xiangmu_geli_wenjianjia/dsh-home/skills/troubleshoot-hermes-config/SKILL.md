---
name: troubleshoot-hermes-config
description: "Use when Hermes model routing or auxiliary config breaks."
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, config, troubleshooting, gateway, approvals, auxiliary]
    related_skills: [hermes-agent, verify-hermes-setup, manage-systemd-services-wsl]
---

# Troubleshoot Hermes Config

Fix recurring Hermes configuration issues: invalid `approvals.mode`, missing auxiliary model providers, outdated gateway service definition, MCP auth errors. Run when `hermes doctor` shows warnings or gateway logs show config errors.

## When to Use

- `hermes doctor` or gateway logs show: `Unknown approvals.mode`, `auxiliary.* provider not configured`, `gateway service definition is outdated`
- MCP server returns 401 (token expired)
- Need to restart gateway from outside gateway process
- Config drift after Hermes updates

## Prerequisites

- Hermes CLI working (`hermes --version`)
- Access to `~/.hermes/config.yaml` and `~/.hermes/.env`
- Gateway running as systemd user service
- Feishu/other messaging platform configured (if applicable)

## How to Run

```bash
# Quick diagnosis
hermes doctor

# Fix approvals.mode
hermes config set approvals.mode smart

# Fix auxiliary providers
hermes config set auxiliary.compression.provider nvidia
hermes config set auxiliary.vision.provider local_vision

# Restart gateway (MUST run from separate shell, not inside gateway)
systemctl --user restart hermes-gateway

# Fix MCP 401: regenerate token in ModelScope, update .env
# hermes mcp test bing-cn
```

## Quick Reference

| Issue | Fix Command |
|-------|-------------|
| `approvals.mode: ask` invalid | `hermes config set approvals.mode smart` |
| Missing compression provider | `hermes config set auxiliary.compression.provider nvidia` |
| Missing vision provider | `hermes config set auxiliary.vision.provider local_vision` |
| Gateway definition outdated | `systemctl --user restart hermes-gateway` (external shell) |
| MCP 401 (bing-cn) | Update `HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY` in `.env` |
| NVIDIA API overloaded | Wait + retry (cloud issue, not config) |
| `Refusing to write to Hermes config file` | 改用 `hermes config set <dot.path> <value>`，不要直接编辑 `config.yaml` |
| `Auxiliary approval: ... timed out` / `all fallbacks exhausted` | `hermes config set auxiliary.approval.provider/model` 换成活的模型 |
| 每轮都慢 / 有 404 声音 | 查 `moa.*`：reference 模型是否下线、aggregator 的 ollama 权重是否真在本地 |
| `Scope Recall truth writer lease is held by another process` | **正常**，单写者设计，其它进程降级只读召回 |
| `另一个 Hermes 安装实例正在使用此配置` / `Another Hermes installation is using this profile` | **仅提示**，桌面端后端 + CLI 共用一个 `HERMES_HOME`；不必修 |

## Procedure

### 1. Diagnose with `hermes doctor`

```bash
hermes doctor
# Check for: "Unknown approvals.mode", "auxiliary.* provider", "gateway definition outdated"
```

### 2. Fix `approvals.mode`

```bash
# Check current
hermes config get approvals.mode
# If "ask" or invalid → fix:
hermes config set approvals.mode smart
# Valid values: smart, manual, off
```

**Success criterion:** `hermes config get approvals.mode` returns `smart`.

### 3. Fix Auxiliary Model Providers

```bash
# Check current
hermes config get auxiliary.compression.provider
hermes config get auxiliary.vision.provider

# Set if missing/auto
hermes config set auxiliary.compression.provider nvidia
hermes config set auxiliary.vision.provider local_vision
# local_vision uses Ollama qwen2.5-vl:7b (configured in model.aliases.vision)
```

**Success criterion:** Both return configured providers (not `auto` or empty).

### 4. Restart Gateway (Critical: Outside Gateway Process)

```bash
# CANNOT run inside Feishu/Telegram/gateway session — SIGTERM propagates
# Run from separate terminal / WSL instance / SSH:
systemctl --user restart hermes-gateway

# Or use hermes CLI (also must be external):
hermes gateway restart
```

**Success criterion:** `systemctl --user status hermes-gateway` shows `active (running)` with new PID.

### 5. Fix MCP Server 401 (ModelScope bing-cn)

```bash
# 1. Get new token from ModelScope: https://modelscope.cn/my/myaccesstoken
# 2. Update .env
sed -i 's/HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=.*/HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=ms-NEWTOKEN/' ~/.hermes/.env
# 3. Restart gateway to reload .env
systemctl --user restart hermes-gateway
# 4. Test
hermes mcp test bing-cn
```

**Success criterion:** `hermes mcp test bing-cn` returns `Connected` + tool list.

### 6. Verify All Fixes

```bash
hermes doctor
# Should show: All checks passed! 🎉
# Gateway logs (journalctl -u hermes-gateway -f) should show no config warnings
```

## 改 `config.yaml` 只能走 `hermes config set`

`config.yaml` 受保护：`patch` / `write_file` 会被拒绝（`Refusing to write to Hermes config file`）。
用点号路径改值，改前先备份：

```bash
cp "$HERMES_HOME/config.yaml" "$HERMES_HOME/config.yaml.bak-$(date +%Y%m%d-%H%M%S)"
hermes config set auxiliary.approval.provider zai
hermes config set moa.enabled false
hermes config get auxiliary.approval.provider     # 回读校验，别只看 set 的回显
hermes config check                               # 完整性
```

`⚠ 'x.y' is not a recognized config key — it was saved anyway` **不等于没生效**：
只要该键本来就在 `config.yaml` 里（只是没进 schema），值会正常写入 —— 回读确认即可，
不要因此改用直接编辑文件。

## 退役/更换模型：四处全量扫查，否则「静默降级」

同一份模型名会散落在**互不相干的位置**。只改主模型或只改代理配置，旧模型会残留在辅助链路里，
而且**不报错** —— 表现只是变慢、某个功能不工作、审批失败。退役一个模型时四处都要扫，缺一处就是没换干净：

| 位置 | 键 | 漏掉的后果 |
|---|---|---|
| Hermes 主配置 | `model.*`、`auxiliary.*.provider/model` | 主会话换了，辅助链路仍在打旧模型 |
| Hermes 高级块 | `moa.reference_models`、`moa.aggregator`、`moa.presets.*` | 每轮并调一个 404 模型 |
| 执行器/代理侧 | cc-switch `providers.settings_config`、`settings.json` 的 `ANTHROPIC_DEFAULT_*_MODEL_NAME` | 派单仍打到旧模型 |
| 工作流 config.env | `WF_AGENT_MODELS` / `WF_CLAUDE_MODEL` | 派单仍指定旧模型 |

扫查就一条：`grep -n "<模型名>" "$HERMES_HOME/config.yaml"` —— 命中几行处理几行。
`model_thresholds` 里的同名条目只影响上下文阈值，**可以留着**，别当故障报。

### `auxiliary.approval` 必须指向活着的模型

它负责**判断一条命令危不危险**。它挂了不是「审批变宽松」，而是审批**直接失败**：

```
Auxiliary approval: request ... timed out after 30.0s
Auxiliary approval: main provider nvidia is unavailable and no fallback_chain configured
Auxiliary approval: all fallbacks exhausted. Raising the primary error.
```

后果在非交互场景（`-q` / cron / 派单 worker）最重：无人可审批 ⇒ 被判危险的命令**一律拒绝**。
所以 `auxiliary.approval` 要指一个**已验证可用且快**的模型（例如已在 compression/title/describer
上跑稳的那个），不要指大而慢或已下线的模型；配 `fallback_chain` 可避免单点。

### MoA：关掉比配错强

`moa.enabled: true` + `fanout: user_turn` + `degraded_reference_policy: loud` 意味着**每一轮**
都并调 reference 模型再用 aggregator 合成。两个必查项：

- `reference_models[].model` 是否真实可达 —— 下线的模型只会 404，**不会把自己禁用**；
- `aggregator` 若是 `provider: ollama`，**先确认本地真有这个权重**：
  `curl -s http://127.0.0.1:11434/api/tags`。参考模型在云端不等于本地 Ollama 也拉了同名模型，
  配错时 aggregator 必然失败。

拿不准就 `hermes config set moa.enabled false`：MoA 是「更聪明」，不是「能干活」；
链路有问题时它只会让每轮更慢。

## 别追的告警：Scope Recall 写租约

```
WARNING scope-recall ... process_lifecycle:
Scope Recall truth writer lease is held by another process;
continuing in read-only recall mode (owner={"role": "provider"})
```

**这是设计如此，不是实例冲突。** 记忆库是单写者（两个进程同时开写连接会损坏库），
主 Hermes 的 provider 进程持写租约，其它进程（每个派单 worker、每次 cron、每次 CLI）
自动降级为只读召回。三步确认它无害，别急着「修」：

1. 持有者：`cat "$HERMES_HOME/scope-recall/.truth-writer.lease.info"` → `{"role": "provider"}`
2. 写入仍在跑：`ls -la "$HERMES_HOME/scope-recall/memory.sqlite3"*`，mtime 是最近的
3. 频次对得上进程启动：每次有新进程起就往 `logs/errors.log` 写一条

**唯一真实影响**：这些子进程能查记忆、不能写新记忆。报告时要讲清「告警属实但无害」和
「无影响」的区别，不要把它说成冲突，也不要为了消除日志去改单写者设计。

## 别追的告警之二：「另一个 Hermes 安装实例正在使用此配置」

```
另一个 Hermes 安装实例正在使用此配置。两个实例共享此配置的设置和数据，
因此更改可能发生冲突。你可以继续使用，也可以在更改前关闭另一个实例。
```

源文件 `hermes_cli/shared_profile_warning.py`，**文件第一行就是结论**：
`"Advisory only: simultaneous installs share profile data, not ownership."`

触发条件（源码原样）：
```python
if any(e["install"] != install_id(project_root)          # 不是同一个安装
       and e["hermes_home"] == home_key                    # 但用同一个 home
       for e in ledger_entries(all_installs=True, verified_only=True)):
    return "另一个 Hermes 安装实例..."
```

关键：`install_id` **不是唯一安装编号，而是路径哈希** ——
`sha256(Path(project_root).resolve().lower())[:12]`。所以**同一个 Hermes、从不同路径起进程，
就会得到两个 install id**，这不是「重复安装」。

### 定位：把哈希反查回路径

```bash
# 1. 机器级登记表：谁在跑、用哪个 home
cat "$HERMES_HOME/spawn-ledger.json"
# 2. 每个 pid 是否真活着（死条目不算冲突）
powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process -Filter 'ProcessId=<pid>' | Select-Object Name,ExecutablePath,CreationDate"
# 3. 反查：对候选 project_root 算 sha256(路径.lower())[:12]，跟登记表里的 install 比
```

典型的两条命中就是 **桌面端自带 python 后端**（project_root 形如 `…/hermes-agent`）和
**CLI/gateway 后端**（project_root 形如 `…/installs/<id>/environments/<id>/workspace`）。
两者共用一个 `HERMES_HOME` → 必然弹这句。**并存是官方支持的用法，确认「继续使用」即可。**

### 不要误判成故障的两件事

- `installs/` 下有多个安装目录 **不等于** 它们在跑 —— 不在 `spawn-ledger.json` 里的就是不活跃的旧目录，
  与这条警告无关。先看登记表，再看得目录。
- 「更改可能发生冲突」的真实风险只是**并发写同一个 SQLite**，而那个已经有机制了：
  Scope Recall 单写者租约（另一个进程自动降级只读）+ kanban 原子 claim。

汇报时把「这是提示、不是错误、不影响运行」说在前面，再给证据（两个 pid 分别是什么），
不要一上来就说「发现冲突」。

## Pitfalls

- **Gateway restart from inside gateway** → Blocked with error: "cannot restart... from inside the gateway process". Always use separate shell.
- **`.env` changes need gateway restart** — Gateway reads `.env` at startup only.
- **`approvals.mode` values** — Only `smart`, `manual`, `off` are valid. `ask` was removed.
- **Auxiliary providers** — `auto` falls back to OpenRouter/Google; explicit is more reliable.
- **MCP token expiry** — ModelScope tokens expire; rotate periodically.
- **NVIDIA API overload** — Not a config issue; shows as `openai.APIError: Service temporarily overloaded`. Auto-retries (max 3).

## Verification

```bash
# 1. Config clean
hermes config get approvals.mode auxiliary.compression.provider auxiliary.vision.provider
# Expected: smart, nvidia, local_vision

# 2. Doctor passes
hermes doctor | grep -q "All checks passed"

# 3. Gateway healthy
systemctl --user is-active hermes-gateway
# Expected: active

# 4. MCP test (if using bing-cn)
hermes mcp test bing-cn | grep -q "Connected"
```

---

*Skill distilled from session 20260904_014632_e3f797b9 (Feishu) analyzing 5 config issues in single troubleshooting session.*