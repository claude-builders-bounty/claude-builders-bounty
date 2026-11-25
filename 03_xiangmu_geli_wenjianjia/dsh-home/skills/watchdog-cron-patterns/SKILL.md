---
name: watchdog-cron-patterns
description: "Silent-success cron watchdog scripts using no_agent: true."
category: devops
tags: [cron, watchdog, monitoring, no_agent, silent-success]
version: 0.1.0
metadata:
  hermes:
    tags: [cron, watchdog, monitoring, no_agent, silent-success]
    related_skills: [hermes-wf-kanban-orchestration, kanban-stale-task-watchdog, unattended-agent-execution, feishu-im-alert]
---

# Watchdog Cron Patterns

Reusable patterns for cron jobs that run scripts directly (`no_agent: true`) with **silent success / noisy failure** delivery semantics.

## Core Principle

| `no_agent: true` Behavior | Trigger |
|---------------------------|---------|
| stdout **non-empty** | Delivery sent to `deliver` target |
| stdout **empty** | **Silent** — no delivery at all |
| stderr | Never triggers delivery |

## Silent-Success / Noisy-Failure Template

```python
#!/usr/bin/env python3
"""Watchdog script: silent on success, alerts on failure."""
import sys

def run_checks():
    """Return list of failure strings, or empty list if all OK."""
    failures = []
    # ... run your checks ...
    return failures

def build_alert(failures):
    """Format alert for delivery (stdout)."""
    return "WATCHDOG ALERT\n\n" + "\n\n".join(failures)

def main():
    failures = run_checks()
    
    if failures:
        # FAILURE: output to stdout triggers delivery
        print(build_alert(failures))
    else:
        # SUCCESS: stderr only -> silent
        sys.stderr.write("[OK] All checks passed\n")

if __name__ == "__main__":
    main()
```

## Common Mistakes

| Mistake | Result |
|---------|--------|
| `print("OK")` on success | Spams delivery every run |
| `print()` any debug on success | Spams delivery |
| Using `print()` for all logs | No silent mode possible |

## Fix Pattern

```python
# All normal logs -> stderr
sys.stderr.write("Checking Ollama... OK\n")
sys.stderr.write("Disk usage: 42%\n")

# Only alert text -> stdout
if failures:
    print(alert_text)
```

## Cron Job Config

```yaml
# hermes cronjob create \
#   --name my-watchdog \
#   --schedule "*/5 * * * *" \
#   --script "watchdog.py" \
#   --no-agent true \
#   --deliver "feishu"
```

- `no_agent: true` — script IS the job, no LLM involved
- `deliver: "feishu"` — where alerts go
- `script: "watchdog.py"` — relative to `~/.hermes/scripts/`

## Agent 模式 + monitor 门控（要推理的巡检，但空转不能烧 token）

`no_agent: true` 是脚本直出。当任务本身需要推理（审查看板、派单、判定工单能不能过）时，用 **`monitor` 脚本门控 agent 运行**：每 tick 先跑 monitor 脚本，输出与上一 tick **逐字节相同** → agent 完全不启动（零 token）；变了 → agent 被唤醒，prompt 里注入 diff。

**致命坑：门控量本身不会自变时，会死锁。**
monitor 输出只由被监控状态决定时，只要那个状态不自己变（例如「有 N 张卡在 ready」— 卡自己不会走），输出就恒定 → agent 永远不被唤醒 → **明明有活干却停摆**。表现为：`last_changed_at` 停在第一次取基线的时间，`last_run_at` 永远 null。

修法：**有待办时输出里带一个心跳桶；无待办时输出恒定哨兵值。**

```python
if not pending:
    print("NONE")                    # 字节恒定 → 零唤醒
    return
print(f"HB {int(now // 120)}")      # 每 2 分钟变一次 → 周期性唤醒
for line in pending:
    print(line)
print(f"BUSY {1 if worker_running() else 0}")
```

- 用 `int(now // 120)` 而不是 `time.time()`：桶内字节稳定（不刷屏），跨桶必然变化（不会卡死），同时满足「输出必须确定性」。
- 心跳桶同时是重试机制：卡住的工单每 2 分钟重新唤醒一次 agent，不需要额外的 stale 计时器。
- 把 worker 起停也算进输出（`BUSY 0|1`），状态机自己就成了唤醒源，不必额外轮询。

**自检（必须做，否则「任务存在」冒充「任务能用」）：**

```bash
python watch.py <board> | md5sum    # 连跑两次：同桶内一致
python watch.py <board>             # 看一眼有没有 HB 行
```

再等到下一次 tick，确认 `last_run_at` 有值、目标真的动了（卡 `ready`→`running`、进程数变 1）。只看 cron list 里有一条 `enabled: true` 就宣布建成是假验收。

用临时 SQLite 库造 `review`/`ready`/空三种状态各跑一遍，比改真实看板安全：

```python
env = dict(os.environ, HERMES_KANBAN_HOME=str(tmp_home))
subprocess.run([sys.executable, "watch.py", "testboard"], env=env, text=True, capture_output=True)
```

## Applied Examples

| Script | Job ID | Purpose |
|--------|--------|---------|
| `proactive_patrol.py` | `ead55c70d699` | 7-system health check (Ollama, ChromaDB, Gateway, WSL net, disk, GPU, systemd) |

## 巡检设计铁律（比静默语义更容易搞错）

**① 能确定性自愈的，巡检必须自己修；报警文案里不许写「需人工 X」。**
写「需 human 执行 reclaim / 需人工重启」等于把动作挂起等人工 —— 而巡检正是为无人值守而建的。
用户睡觉时报警只是一条没人看的消息，流水线实际停摆。形态：`if heal: 执行修复`，
默认自愈、`--no-heal` 保留只诊断；自愈了照样报（降成 WARN 并写「已自愈 N 项」），不要静默。

**② 判活/判死的字段必须是「不会被复用的」。**
长生命周期实体（任务、会话、连接）常有一个「开始时间」字段，它在**重新认领时不刷新** ——
拿它算「已运行 N 小时」会把刚起 10 分钟的东西报成 11 小时，巡检于是去回收**正在干活**的实例，
比不巡检更糟。同理，租约/过期字段在「自己写库、不走续租 API」的组件里会永久停在过去。
可信信号是**会随活干而变的产物**：日志文件 mtime、上游请求日志新行、心跳行。

**③ 周期太稀的巡检 ≈ 没有巡检。**
3 小时的档在 8 小时夜间只跑 2~3 次；中间堆的垃圾文件、连败后归档的任务全落在空窗里。
判据是「巡检脚本本身的耗时」而不是直觉：如果一次 <10 秒，30 分钟甚至 5 分钟都不是成本问题。

**④ 必须有一条「有没有出活」的结果指标，不能只有「机制在不在」。**
服务都在听、进程都活着、队列都非空 —— 仍然可能一整天零产出。要有「最近 N 小时完成任务数 == 0 且队列非空 → FAIL」这种业务向判据，否则用户问的「它干嘛去了」永远答不上来。

**⑤ 巡检脚本自己有误报时，先修判据再加规则。**
一条永远误报的检查会被训练成「扫一眼就忽略」，真故障就这样被漏掉。新规则要么双向实测
（健康 → 静默、注入故障 → 报警），要么不进巡检。

## Verification Checklist

- [ ] `python3 script.py >/dev/null` produces NO output on success
- [ ] `python3 script.py 2>/dev/null` produces alert text on injected failure
- [ ] 至少一项可自愈故障已实测「注入 → 无人工干预自己恢复」，并核对了恢复后的真实状态
- [ ] 没有任何一条告警文案以「需人工 X」结尾（能自愈的都已自愈）
- [ ] Cron `last_delivery_error` is null after silent runs
- [ ] Feishu only receives messages when something is actually wrong

---

*Distilled from fixing proactive-patrol spam (job_id: ead55c70d699, 2026-09-24).*