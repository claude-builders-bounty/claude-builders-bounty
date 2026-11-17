---
name: configure-ccswitch-claude-code
description: Use when wiring third-party APIs into Claude Code.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [claude-code, cc-switch, api-relay, windows, provider-config]
    related_skills: [hermes-agent, edit-config-files-wsl, verify-hermes-setup]
---

# 用 CC Switch 给 Claude Code 配置第三方 API 提供商

## When to Use
用户拿到免费/中转站 API key（Anthropic 协议），要接进 Claude Code；或发现「CC Switch 切了 provider 但 Claude Code 不生效」。

## 架构真相（先搞清，否则白配）

```
cc-switch.db (providers 表)
   └─ settings_config 字段 = 一份完整 settings.json 内容
         ↓ CC Switch 切换时原样写出
<claudeConfigDir>\settings.json     ← CC Switch 的写入目标
         ↑ 但 Claude Code 默认只读 ↓
~/.claude/settings.json             ← Claude Code 的真实读取位置
```

**关键结论**：
1. `settings.json` 与 `providers.settings_config` 是 **1:1 全等**。验证：`json.load(settings.json) == json.load(provider.settings_config)` 必须为 True。
2. 切换 provider = ①把 settings_config 写进 settings.json ②该行 `is_current=1`、其余置 0。没有别的把戏。
3. **CC Switch Portable 把 `claudeConfigDir` 写在 `~/.cc-switch/settings.json`**；它把配置写到那个目录，而 Claude Code 默认读 `~/.claude/`。两者不匹配时，用户所有的切换都静默失效。桥接靠环境变量 `CLAUDE_CONFIG_DIR`。
4. **`cc-switch.exe` 没有命令行参数** —— 直接执行它就是启动 GUI（连 `--help` 都会把界面启起来）。**它必须常驻**：本地代理只在 app 运行时监听 `127.0.0.1:15721`（开关是 `proxy_config.proxy_enabled`），**app 一关代理就死，Claude Code 随即静默挂死**（无报错、无输出、被 timeout 杀掉）。诊断「Claude Code 卡住」先确认这个进程在不在。
5. **上游是 OpenAI 格式时，代理不是可选项**。provider 的 `meta.apiFormat` 标 `openai_chat`（如 NVIDIA `integrate.api.nvidia.com`：只有 `/v1/chat/completions`，`POST /v1/messages` 直接返 `404 page not found`）时，Claude Code 说的 Anthropic 协议**必须由代理转换**。此时 `settings.json` 的 `ANTHROPIC_BASE_URL` 会被写成 `http://127.0.0.1:15721`（**不是**上游地址），`ANTHROPIC_AUTH_TOKEN` 也换成代理自己的值 —— 所以看到 BASE_URL 指向本地不要以为是配错了。
6. **模型名是两层的**：`ANTHROPIC_DEFAULT_<别名>_MODEL` 是 **Claude Code 看到并请求的名字**，`ANTHROPIC_DEFAULT_<别名>_MODEL_NAME` 是**代理替换后真正发给上游的模型**。`[1M]` 这类后缀在转发前被剥掉。要换上游模型就改 `_MODEL_NAME`；`ANTHROPIC_MODEL` **没有**对应的 `_NAME` 键，它按原样转发（同样剥后缀），所以它写什么上游就收到什么。

## 步骤

### 1. 侦察
```bash
cat ~/.cc-switch/settings.json                    # 含 claudeConfigDir
find ~/.cc-switch/backups -name '*.source' -exec cat {} \;   # 内容是它管的 settings.json 路径
dir /a /b %USERPROFILE%\.claude                   # 默认位置有没有 settings.json
reg query "HKCU\Environment" | grep -i CLAUDE     # 有没有 CLAUDE_CONFIG_DIR
```

### 2. 确认 station 的协议与 Base URL
- **必须查站点官方文档**，不要照抄 OpenAI 风格路径。
- Anthropic 兼容站的 `ANTHROPIC_BASE_URL` **一律不带 `/v1`**（Claude Code 自己拼 `/v1/messages`）。
- 境内站常有**备用域名**（主域超时 → 试备用域）。

### 3. 实测端点（不要跳过）
```bash
K=$(grep -oE 'sk-[A-Za-z0-9_-]+' keyfile | head -1)   # 绝不 echo 出来
BODY='{"model":"<model>","max_tokens":16,"messages":[{"role":"user","content":"hi"}]}'
curl -sS -m 25 -w '\n[%{http_code}]\n' -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $K" -H 'anthropic-version: 2023-06-01' \
  -H 'User-Agent: claude-cli/2.1.300 (external, cli)' \
  -d "$BODY" https://<base>/v1/messages
```
**错误码翻译**：
| 返回 | 含义 | 动作 |
|:--|:--|:--|
| `unauthorized client detected` | 站点按客户端指纹拦截 | 加 `User-Agent: claude-cli/<ver> (external, cli)` |
| `model_not_found` / `无可用渠道` | **key 是好的**，模型名/分组不对 | 换模型名，或让用户去后台看分组 |
| `401` 提示 token 无效 | key 真的无效/过期 | 找用户换 key |
| `403` + Cloudflare HTML | WAF 拦截（常间歇性）| 加真实浏览器 UA 重试；仍不行找用户 |
| `402 Insufficient Balance` | 账号欠费 | 站点侧问题，非配置问题 |
| 连接超时 `000` | 网络不通 | 试备用域名 / 让用户开代理 |

### 4. 写 provider（先备份 DB）
```python
import sqlite3, json, time, uuid
DB  = r"...\cc-switch.db"
now = int(time.time()*1000)

def cfg(base, key, model):
    env = {"ANTHROPIC_BASE_URL": base, "ANTHROPIC_AUTH_TOKEN": key,
           "ANTHROPIC_MODEL": model,
           "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
           "ANTHROPIC_DEFAULT_SONNET_MODEL": model,
           "ANTHROPIC_DEFAULT_OPUS_MODEL": model,
           "CLAUDE_CODE_AUTO_MODE_SERVER": "0"}
    return json.dumps({"env": env}, ensure_ascii=False)

META = json.dumps({"commonConfigEnabled": True, "endpointAutoSelect": True,
                   "apiFormat": "anthropic"})
c = sqlite3.connect(DB); pid = str(uuid.uuid4())
c.execute("""insert into providers (id,app_type,name,settings_config,website_url,category,
  created_at,sort_index,notes,icon,icon_color,meta,is_current,in_failover_queue,cost_multiplier,
  limit_daily_usd,limit_monthly_usd,provider_type)
  values (?,?,?,?,?,?,?,?,?,?,?,?,0,0,'1.0',NULL,NULL,NULL)""",
  (pid, "claude", "<站点名>", cfg(base, key, model), base, None, now, None, "<备注>", None, None, META))
c.execute("insert into provider_endpoints (provider_id,app_type,url,added_at) values (?,?,?,?)",
          (pid, "claude", base, now))
c.commit()
```
- `app_type='claude'`；PK 是 `(id, app_type)`（用 uuid4）。
- **HAIKU/SONNET/OPUS 三个全设成同一个模型名**，否则子 agent / haiku 调用会打到不存在的模型。
- `cost_multiplier='1.0'`, `is_current=0`, `in_failover_queue=0`，其余可 NULL（`icon`/`category` 可空）。
- **不要擅自改用户现有的 current provider**（除非像余额 402 那种已废的情况，且要明说）。

### 5. 补 `CLAUDE_CONFIG_DIR`（最容易漏的一步）
```bash
setx CLAUDE_CONFIG_DIR "<claudeConfigDir>"
reg query "HKCU\Environment" /v CLAUDE_CONFIG_DIR   # 复核
```

### 6. 端到端验证（唯一算数的验证）
```bash
CC="<claudeConfigDir>/node_modules/@anthropic-ai/claude-code/bin/claude.exe"
# 不传任何 ANTHROPIC_* 变量，验证它确实在读 CC Switch 的文件
CLAUDE_CONFIG_DIR="<claudeConfigDir>" "$CC" -p "只回复两个字：成功"
```
看两点：① 有无 `Not logged in · Please run /login`（= 没读到配置）② 是否返回模型文本。

## 排障：Claude Code 挂死 / 报模型错

**先分清症状属于哪一层** —— 三种症状指向三个不同的失败域，别在同一个地方瞎试：

| 症状 | 含义 | 查哪里 |
|:--|:--|:--|
| `claude -p ...` **长时间零输出、被 timeout 杀掉** | 端点**不可达**，连错误报文都返不回来 | 对 `ANTHROPIC_BASE_URL` 的 host 做 TCP 443 探测；确认 cc-switch 在跑、代理在听 |
| `There's an issue with the selected model (<名字>)` | **代理已经通了**，只是模型名被拒 | `proxy_request_logs` 的 `status_code`（404/410） |
| 上游 `410 Gone: The model '<X>' has reached its end of life` | **渠道被钉在一个已下线的模型上** | 见下条 |
| 上游 `404 ... Function id '<uuid>' ... is not found` | 该账号下没有这个部署 | 站点后台确认账号**实际授权**的模型（公共目录里有 ≠ 你的账号能用） |

**模型下线会整条渠道报废**：provider 被钉在某个已退役模型时，**无论请求里写什么模型名**，上游都回同一条 410 —— 换 `ANTHROPIC_MODEL` / `_MODEL_NAME` 都不解决问题，必须去站点后台换一个在册模型。判定方法：拿 token 拉一次**实时模型目录**（NVIDIA：`GET https://integrate.api.nvidia.com/v1/models`，HTTP 200 返回全部在册 id 与总数），**钉住的那个 id 不在里面就是它**；`/v1/models` 通只证明 token 有效，不证明目标模型可用。

**诊断数据全在 cc-switch.db 里**，比看 UI 快也准：

| 表 | 看什么 |
|:--|:--|
| `proxy_request_logs` | 每个请求的 `model` / `request_model` / `status_code` / `error_message`（含上游原始报文）。按 `provider_id`+`status_code` 分组，就能看出哪条链路真的通过、从哪一刻起全挂 |
| `provider_health` | `is_healthy` / `last_success_at` / `last_error` —— 直接给出「最后一次成功是什么时候」 |
| `proxy_config` | `proxy_enabled`（代理总开关）/ `listen_port` |
| `providers` | `settings_config`（当前配置）/ `is_current`（谁在生效） |
| `provider_endpoints` | 该 provider 登记的上游 URL |

**「有没有真的成功过」的唯一硬证据是 `status_code=200`**，不是 UI 的绿灯、不是 `claude --version`、也不是 `agent-health.sh` 全绿。

### 关键区分：`cua-driver.exe` ≠ `cc-switch.exe`

用户常混淆，因为都会在进程列表里出现且名字带 switch/driver。

| 进程 | 作用 | 是否抢鼠标/键盘 |
|------|------|-----------------|
| `cc-switch.exe` | Claude Code 本地代理（Anthropic → 第三方 API 转换），监听 127.0.0.1:15721 | **否** — 无输入钩子，只转发 HTTP |
| `cua-driver.exe` | Computer Use Agent 驱动（桌面自动化），注册全局光标覆盖层 `Cua.AgentCursorOverlay.default` | **是** — 拦截/模拟鼠标键盘，导致焦点抢占、光标乱跳 |

**诊断口诀**：
- 鼠标被抢、光标乱跳、窗口莫名切换 → **先查 `cua-driver.exe`**
- Claude Code 卡住、报模型错、429 限流 → **查 `cc-switch.exe` / 代理链路**

**实测（2026-10-29）**：用户报 "ccswitch 几秒拉一次抢鼠标"，实际是 `cua-driver.exe` (PID 11152) 抢鼠标 + `cc-switch.exe` (PID 11740) 由 cron 看门狗每 5min 重启。两者完全不同，杀错进程解决不了问题。

详细诊断步骤见 `windows-system-maintenance` 技能的 `references/diagnose-process-hijacking.md`。

---

### 症状：我指定了模型，实际却跑另一个模型

**机制**：cc-switch 代理会把客户端请求的**任何**模型改写成当前 provider 的主档位 `ANTHROPIC_MODEL`，再按原样转发上游。所以「客户端 `--model` 传了 A，日志里 `used` 是 B」不是客户端没生效，而是**代理层的 provider 主档位赢了**。

**铁证怎么取**（`request_model` = 客户端要的，`model` = 网关实际发的，两者不等即被改写）：
```sql
SELECT request_model, model, status_code, COUNT(*) n
FROM proxy_request_logs GROUP BY 1,2,3 ORDER BY n DESC LIMIT 20;
```
`req=nemotron → used=deepseek` 这类记录就是用户抱怨「不按我指定的走」的全部证据，不要猜。

**五个档位必须一起改**。只改一个会留下静默落差：

| 档位 | 作用 |
|:--|:--|
| `ANTHROPIC_MODEL` | 主档位，代理改写的目标 |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` / `_OPUS_` / `_HAIKU_` / `_FABLE_` | 降级/子任务档位，Claude Code 内部另起的调用走这些 |

用户「在界面里改成了 X」却仍跑 Y，常见原因就是 **X 只落进了四个降级档位，主档位还是 Y**。改完必须把五个键全部打印回读确认，不要只看改动的那一个。

**模型有第二处真相**：自动化派单脚本通常自己还传 `--model`（或 config.env 里存着模型名）。代理改写开着时 provider 档位赢；改写没触发时 `--model` 赢。两边不一致就会出现「有时对有时不对」。统一模型时**两处都要改**，并记录改过哪两处。

**改完 DB 不等于生效**：GUI 进程启动后可能一直用内存里的配置，写 `cc-switch.db` 后它不重读。验证方法：发一次真实请求看 `proxy_request_logs` 最新一条的 `model`。若 worker 正占满通道，合成请求会超时且无日志 —— 此时**不要断言已生效**，如实说明「需重启 cc-switch 或改走界面」，因为重启会断代理、正在跑的 worker 全部失败。

**比速度只看 `first_token_ms`**：`duration_ms` 常为 0（未记录），拿它比会得出「一样快」的错结论。按模型聚合 `first_token_ms` 的平均值与 200 率才是可信对比；样本少时同时看最近几小时逐条，历史成功率高/低可能来自早已修复的时段。

**探针**：`scripts/probe_ccswitch_model.py` 一次打出「五个档位是否一致 + 改写记录 + 各模型首字延迟/成功率」，只读不泄密。用户说「模型不是我选的那个」时先跑它，比手工写 SQL 快也比猜准。

### `EXIT=$?` 在管道之后会骗你

```bash
timeout 180 claude -p "..." 2>&1 | tail -6; echo EXIT=$?   # ✗ 这是 tail 的退出码，永远是 0
```

模型挂死也会显示「成功」。必须落文件、不带管道：

```bash
OUT="D:/<scratch>/probe.txt"     # 原生正斜杠路径；别用 $TMPDIR，git-bash 的 /tmp 原生工具读不到
rm -f "$OUT"
timeout 180 env CLAUDE_CONFIG_DIR="<claudeConfigDir>" "$CC" \
  -p "reply with exactly: PONG" --max-turns 1 > "$OUT" 2>&1
echo "REAL_EXIT=$?"              # 124 = 超时被杀 = 一个字都没出 = 不可用
```

**判据是文件里有没有 `PONG`**，不是退出码，也不是命令有没有回显。

## NVIDIA 上游限流（40 RPM）的规避方案

实测：NVIDIA `integrate.api.nvidia.com` 实测 ~40 RPM 配额，**cc-switch 本地限流不生效/未配置**，并发派单瞬间打满 → 全 `HTTP 429: Too Many Requests`。

**症状**：cc-switch 日志密集 `Provider Nvidia 请求失败: 上游 HTTP 429`；`claude -p` 启动即超时、零输出。

**先分清 429 报的是哪个模型名**：Claude Code 请求的是 `claude-sonnet-5` / `claude-opus-5` 这类**客户端别名**，代理改写成 provider 主档位（如 `nvidia/nemotron-3-ultra-550b-a55b`）后才发上游。所以「429 的是 claude-sonnet-5」和「429 的是 nemotron」讲的是同一件事，不要和用户争。要讲清是哪一层在限流，取 `proxy_request_logs` 的 `request_model`（客户端要的）对 `model`（网关实发）；只看 UI 那一列会误判。

**不要默认推荐 AgentRouter 兜底。** 用户已实测判定它「最烂、完全不可用」，拿它当替代方案会被当场拒绝。要用公益站先问用户哪家在册可用。

**默认处置是先等，不是换配置**：429 通常几十分钟到几小时自行解除 —— 跑探针（落文件、不带管道）直到出字再派单。确需换 provider 时走本技能「步骤 4」写新 provider + 切 `is_current`，并把五个模型档位一起改。

**下面这段 AgentRouter 配置只当格式参考，不代表当前可用**（境内直连、`deepseek-v4-flash`）：

```json
// settings.json 关键改动（cc-switch 会写出去，也可手动改 DB 后重启 cc-switch）
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://ps.air-outer.com",   // AgentRouter 境内备用域名
    "ANTHROPIC_AUTH_TOKEN": "<你的 AgentRouter key>",
    "ANTHROPIC_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_FABLE_MODEL": "deepseek-v4-flash",
    "CLAUDE_CODE_AUTO_MODE_SERVER": "0"
  }
}
```

**验证**：`curl -H "Authorization: Bearer $K" -H 'anthropic-version: 2023-06-01' -d '{"model":"deepseek-v4-flash","max_tokens":8,"messages":[{"role":"user","content":"hi"}]}' https://ps.air-outer.com/v1/messages` 返回 200。

**注意**：
- AgentRouter 按客户端指纹拦截，**必须带 `User-Agent: claude-cli/<ver> (external, cli)`** 否则 `unauthorized client detected`
- 仅 `deepseek-v4-flash` 实测可用；`claude-opus-5`/`claude-opus-4-8` 报「无可用渠道」
- 此为**临时兜底**，NVIDIA 配额恢复后改回`cc-switch.db` 的历代 `.bak*` 就是回退点，
按 mtime **最早的那个 ≈ 安装即刻**（provider 最少、`is_current` 是初始那家）。先列一遍再挑：

```bash
cd "<claudeConfigDir>" && ls -la cc-switch.db.bak*        # 名字里的时间戳就是回退点
```

### 步骤（顺序不能反）

```bash
cd "<claudeConfigDir>"
# ① 先留一份当前库 —— 这一条永远做，否则回不去了
cp cc-switch.db "cc-switch.db.bak-before-restore-$(date +%Y%m%d-%H%M%S)"
# ② 停 app：运行中的 GUI 持有 DB 且会用内存配置回写，不停就白恢复
powershell -NoProfile -Command "(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'cc-switch.exe' }) | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
# ③ 覆盖库 + 清遗留 WAL/SHM
cp cc-switch.db.bak-<最早那个> cc-switch.db && rm -f cc-switch.db-wal cc-switch.db-shm
# ④ 重启 app —— 它会立刻按新库的 is_current 重写 settings.json
powershell -NoProfile -Command "Start-Process -FilePath '<claudeConfigDir>\cc-switch.exe' -WorkingDirectory '<claudeConfigDir>'"
```

### 恢复成功的判据（三条，不要只看文件大小）

1. `providers` 里**那批后加的 provider 没了**、`is_current` 回到初始那家
2. `proxy_request_logs` 行数归零（新库是空的）
3. **`settings.json` 已被重写**，其 `ANTHROPIC_DEFAULT_*_MODEL_NAME` 反映**新 current provider** 的模型 ——
   cc-switch 每次 attach 都重写 settings.json，所以**恢复后读 settings.json 就知道哪家赢了**，不用猜。
   新 current 若是不需要代理的一家，`ANTHROPIC_BASE_URL` 可能整条消失，那是正常的。

⚠️ **provider 数不会恰好等于备份里的数量。** cc-switch 启动时会从**它自带的源**补进若干预设 provider
（特征：`settings_config` 里带 `_cc_source` / `key_env` / `provider_key` 这类键）。多出一两个不是恢复失败，
只要不是 `is_current` 就不影响。报告时按「后加的那批已清除 / 自带的补进了 N 个」分开讲，不要报成「数量对不上」。

### 边界：这条和「绝不碰 Claude Code 环境」不冲突

默认 `cc-switch.db` / `settings.json` 属只读禁区；**但用户明确要求恢复 cc-switch 初始化时，那是用户的决定** ——
做（带备份），做完就把模型配置**交还给用户**，不要再顺手去调 provider / 模型名。

### 🚨 交接完的配置还在变 = 大概率是用户正在界面上改，先别喊异常

配置交回给用户之后，`cc-switch.db` 的 `is_current` 与 provider 列表**会继续变** —— 那是 GUI 在写。
实测：恢复完读了一次，发现某 provider 消失、current 换了一家，正准备报「异常」，用户回了一句「那是我自己删的」。

规则：**连读三次、间隔十几秒，三次一致才叫稳定；出现变化先问「是不是你在界面上动了」**，
再考虑库是不是被写坏。报告用「当前实际状态（含你的操作）」的语气，不要用「检测到异常」。

## 陷阱清单
- **Claude Code 2.x 是原生 `claude.exe`（数百 MB），不是 cli.js**。入口看 `node_modules/@anthropic-ai/claude-code/package.json` 的 `bin` 字段。
- **Windows bash 下 `curl -o <path>` 可能静默失败**（文件根本没建）。调试时代码直接打 stdout，别重定向。
- **cmd/PowerShell 继承的是启动时的环境块**，`setx` 之后立刻 `cmd /c echo %VAR%` 仍是旧值——用 `reg query` 判定是否写成功。
- `~/.claude/` 里没有 `settings.json` 很常见；`hasCompletedOnboarding` 等状态在 `~/.claude.json`（易与 `~/.claude/` 混淆）。
- Claude Code 报 `doesn't recognize the model ... assumes a context window of 200k` 只是提示；要精确修需在 settings.json 设 `autoCompactWindow` 或 `modelSettings`（**不知道真实窗口就别乱设**）。
- 密钥只从文件读进变量，**任何输出都要掩码**，日志/记忆里绝不落明文。**脱敏必须按内容做，不能按列名做**：`providers.settings_config` 这类字段是**装着一整份 config 的 JSON 字符串**，key 藏在值里面 —— 只判断列名里有没有 `key`/`token` 会把 `nvapi-…` 明文打到 stdout。正确做法是对**每个字符串值**跑一遍正则（`sk-[A-Za-z0-9_-]{4,}`、`nvapi-[A-Za-z0-9_-]{4,}`、`api[_-]?key`）再输出。漏一次就够让用户去轮换密钥。
- **读诊断数据前先停 cc-switch，否则拿到的是半成品。** 它在 WAL 模式下持有 `cc-switch.db`，只 `cp` 主文件而不带 `-wal`/`-shm`，复制品虽然头是合法 SQLite、体积也正常（十几 MB），但 `sqlite_master` 里 **0 张表** —— 据此断言「库加密了 / 表不存在」是误判。要读就：① 先 Stop-Process，再 cp（推荐）；或 ② 连 `-wal`、`-shm` 一起复制。
- **`conn.execute('PRAGMA cipher_version')` 不抛异常 ≠ SQLCipher。** 普通 SQLite 执行未知 pragma 同样不报错，只是**不返回任何行**。判据是 `fetchall()` 有没有内容，不是有没有异常。
- **不能从 `settings.json` 反推「模型通道是断的」。** 它由 cc-switch 随时重写，读它的那一刻不代表运行时的值。
  实测：只读 settings.json 看到少了 `ANTHROPIC_BASE_URL` / `AUTH_TOKEN`，据此断言「Claude Code 根本调不到模型」
  并写进部署方案，下一条命令真跑 `claude -p "回复两个字：可用"` 就 `exit=0` 正常出字，方案当场作废。
  **通道通不通只有探针说了算**（落文件、不带管道的写法见「`EXIT=$?` 在管道之后会骗你」）。读配置两个方向都不能定论。
