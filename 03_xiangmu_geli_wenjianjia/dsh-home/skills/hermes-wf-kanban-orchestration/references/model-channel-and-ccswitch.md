# 模型链路与 cc-switch 代理配置

本文记录 cc-switch 代理的模型改写机制、验证方法、以及 NIM 模型测试的正确姿势。

---

## cc-switch 代理改写机制（2026-10-18 实测）

本机 settings.json 无 model 字段（只有 BASE_URL=http://127.0.0.1:15721 + AUTH_TOKEN=PROXY_MANAGED），模型决定权在 cc-switch 代理。代理会把客户端请求的**任何**模型改写成当前 provider 的 `ANTHROPIC_MODEL`（日志铁证：req=nemotron → used=deepseek 43 次；req=claude-sonnet-5 → used=deepseek 1135 次）。所以「客户端 --model 指定了却被换掉」= provider 主档位不是你想要的那个。另有 5 个档位（MODEL/SONNET/OPUS/HAIKU/FABLE），只改主档位不会覆盖降级档位。改 cc-switch.db 后**必须重启进程**才生效（实测：不重启 req=n3u→used=deepseek；重启后立即按 n3u 发）。派单侧已收口为 `WF_CLAUDE_MODEL="auto"`（dispatch_claude.sh 调 ccswitch_model.py 现场读，日志有「模型来源」行），自检脚本 `scripts/hermes-wf-xianyu/verify_model_channel.py`（`--restart` 自动重启）。重启会断代理，在跑 worker 全废，挑空档做。

## WF_CLAUDE_MODEL 配置策略

**首选：`WF_CLAUDE_MODEL="auto"`（2026-10-18 落地）。** 设为 `auto` 或留空时，`dispatch_claude.sh` 每次派单现场调 `ccswitch_model.py` 读 cc-switch 当前 provider 的主档位 `ANTHROPIC_MODEL`（自动剥掉 `[1M]` 后缀）再传给 `--model`。这样用户在任何时候改 cc-switch，下一次派单自动跟随，**派单层不再持有第二份模型配置**。日志里会有一行 `模型来源：cc-switch 当前主档位 → <model>` 作为证据。

**不要写死模型名。** 写死 = 在派单层再覆盖一次 cc-switch，出现「两处真相打架」：用户以为改了 cc-switch 就生效，实际被 `--model` 顶着。历史上 `WF_CLAUDE_MODEL` 写死过 `deepseek-ai/deepseek-v4.1-flash`，导致用户把 cc-switch 切成 n3u 后完全不生效。

**留空的旧风险仍在**：`ccswitch_model.py` 读失败时会退化成不传 `--model` → Claude Code 用内置默认 `claude-opus-5` → 别名映射对 opus 不生效 → 上游 404。所以 `auto` 路径必须验证 helper 能拿到值（`python ccswitch_model.py` 有输出），读失败时日志会打 `⚠️ 读 ccswitch 模型失败`。

**改完 cc-switch 一定要确认真的生效**，一条命令：

```bash
python D:/Ai/Agent/hermes/scripts/hermes-wf-xianyu/verify_model_channel.py
# 未生效时自动重启 cc-switch：
python .../verify_model_channel.py --restart --wait 120
```

它比对「cc-switch 配置的模型」与「代理最近一次真实请求的 `used`」，并顺带检查五个档位是否一致、`WF_CLAUDE_MODEL` 是否还在覆盖。

要做「按阶段/角色分模型」（重活给大模型、轻活给小模型），加一个 `config.env` 键 `WF_AGENT_MODELS="角色=真实模型名,角色=真实模型名"`，再在 `dispatch_claude.sh` 里按 `AGENT_NAME` 查表。**关键是查不到时必须回落到 cc-switch 的当前模型**，不能让 `--model` 落空。改完用 `bash -n` + 用真实 `config.env` 跑一遍全角色解析（包括一个未登记角色验证回落）才算法验证过——不要只看脚本能跑。

## ANTHROPIC_BASE_URL 与 cc-switch 代理

`ANTHROPIC_BASE_URL` 指向 `http://127.0.0.1:15721`（cc-switch 内嵌代理），而 **NVIDIA 只支持 OpenAI 格式（`POST /v1/messages` → 404），必须靠这个代理做 Anthropic↔OpenAI 转换**。所以：

- **cc-switch 一停，Claude Code 就完全不可用**（症状：调用挂死到 `REAL_EXIT=124`，输出全空；`netstat | grep 15721` 什么都没有）。
- cc-switch 没有 CLI，**执行 `cc-switch.exe` 就是启动它的 GUI + 代理**；它启动时会自动 attach 当前渠道并**重写 `settings.json`**。
- **它每次 attach 都会把我的手工改动覆盖回别名**（`ANTHROPIC_DEFAULT_SONNET_MODEL` 写回 `claude-sonnet-5[1M]`，真实模型名放在同名的 `_MODEL_NAME` 键里）。所以**不要手改 `settings.json` 的模型名**——那是 cc-switch 的辖地，改了也会被冲掉；要改就改 cc-switch 的 provider 配置（`cc-switch.db` 的 `providers.settings_config`），并在 app 停止时改（在跑时改会被回写覆盖）。
- **`WF_CLAUDE_MODEL` 不是最终真相 —— 代理会改写它。** cc-switch 会把客户端请求的**任何**模型改写成当前 provider 的主档位 `ANTHROPIC_MODEL`。所以「`config.env` 填了 X、`proxy_request_logs` 里 `used` 是 Y」= provider 主档位不是 X，**不是** `--model` 没传。
  五个档位要一起改：`ANTHROPIC_MODEL` 之外还有 `ANTHROPIC_DEFAULT_SONNET/OPUS/HAIKU/FABLE_MODEL` —— 只改主档位时，Claude Code 的子任务/降级调用仍跑旧模型，表现为「有时 X 有时 Y」，很难查。
  改完 `cc-switch.db` 也要重启 app 或改走界面（运行中的 GUI 不重读 DB）；**在 worker 跑着时不要重启**，重启会断代理、在跑的卡全废。判定脚本与证据取法见 `configure-ccswitch-claude-code` 的「我指定了模型，实际却跑另一个模型」。

## 测 NIM 上的模型：必须用真实模型名，绝不用 Claude Code 的别名

NVIDIA NIM 上**没有 `claude-*` 模型**（那是 Anthropic 的模型名）。用 `claude --model opus|sonnet|haiku` 去探 NIM，参数会被解析成别名（如 `claude-opus-5[1M]`），上游必然不认识 —— 报「selected model 可能不存在或无权访问」或 404。**这种测试无效，不能据此判定某个真实模型不可用。**

正确做法：先用 `GET /v1/models` 查出 NIM 目录里的**真实模型名**（如 `deepseek-ai/deepseek-v4.1-flash`、`nvidia/nemotron-3-ultra-550b-a55b`），再用 `claude --model <真实模型名>` 直测；或直接绕开 Claude Code 调 `POST /v1/chat/completions`（OpenAI 格式 + `stream: true`）。

**豁免**：只有当别名在 cc-switch 的映射表里**命中**时（`ANTHROPIC_DEFAULT_<T>_MODEL` 的别名 ↔ 同名 `_MODEL_NAME` 的真实模型），别名才等价于真实模型，`proxy_request_logs.model` 列会显示真实模型名。查那一列就能确认映射到底有没有生效。

## 派单前先验证执行器的模型链路

**派单管道全绿，不代表 worker 能出活。** 执行器（Claude Code）能不能拿到模型回复，是和派单脚本**完全独立的失败域**：`claude --version` 有版本、`agent-health.sh` 全绿、`dispatch_claude.sh` 退出 0 —— worker 仍可能因为模型链路断了而**一个字都产不出来**，并以 exit 0（或「零产出」block）收场。批次卡住时，先确认模型链路，再怀疑派单脚本。

派第一批卡**之前**跑一次最小端到端：

```bash
OUT="D:/<scratch>/probe.txt"     # 原生正斜杠路径；别用 $TMPDIR，git-bash 的 /tmp 原生工具读不到
rm -f "$OUT"
timeout 180 env CLAUDE_CONFIG_DIR="$WF_CLAUDE_CONFIG_DIR" "$WF_CLAUDE" \
  -p "reply with exactly: PONG" --max-turns 1 > "$OUT" 2>&1
echo "REAL_EXIT=$?"              # 124 = 超时被杀 = 模型链路断了
```

**判据是文件里有 `PONG`**，不是退出码 —— 管道会掩盖真实退出码。模型链路本身怎么查见 `configure-ccswitch-claude-code` 的排障章（cc-switch app 是否常驻、代理是否在听、`proxy_request_logs` 里有没有 `status_code=200`）。

### 实测基线：NVIDIA 链路「能通，但很慢」——别把慢当断

本机唯一可用渠道是 NVIDIA（`integrate.api.nvidia.com`），它**官方限流，单次简单调用实测耗时约 5 分钟**（`claude --model sonnet -p "reply with exactly: PONG"` → `PONG`，`REAL_EXIT=0`，**307 秒**）。

所以**预检的超时必须放到 600 秒以上**。用 90/150/200 秒的 `timeout` 去探，会把「正常但慢」误判成「链路断了」——症状是 `REAL_EXIT=124` 且代理日志里**连这条请求的记录都没有**（请求还在重试中，没落盘）。**先看代理日志有没有新行，再下「不通」的结论。**

同时在 `proxy_request_logs` 里对基线定性：

| 查到的 model | HTTP | 含义 |
|---|---|---|
| `deepseek-ai/deepseek-v4.1-flash` | `200` | **正常**。这是别名（如 `claude-sonnet-5`）经代理映射后的**上游真实模型名** |
| `claude-*`（别名原样） | `404` / `410` | 代理**没做映射**，别名被原样转发 → 上游不认识 |
| 任意模型名 | `410` 且报文提到**另一个模型**已 EOL | 代理仍在路由到**旧模型**，provider 配置没真正生效 |
| `429` / `503` | — | NVIDIA 官方限流，**属正常**，重试即可 |

`model` 列是**上游真实模型**，`request_model` 列是**客户端发来的名字**——两者不同 = 映射生效了，这是判断映射是否工作的唯一依据。