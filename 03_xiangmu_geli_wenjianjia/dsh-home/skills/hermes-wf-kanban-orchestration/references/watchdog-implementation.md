# 协调层看门狗实现：review_watch.py

本项目自研的 Hermes cron monitor，实现「有审核我审、有待派我派、空闲零消耗、卡住自动重唤醒」。

## 脚本位置

```
D:/Ai/Agent/hermes/scripts/hermes-wf/review_watch.py
```

## cron 配置

```
job_id: c296db0ca793
name: "wechat_recovery 协调层看门狗（审+派单）"
schedule: "every 5m"
monitor: "hermes-wf/review_watch.py"
deliver: local
```

## 核心输出格式（逐字节确定性）

```
HB <2分钟桶>
READY <task_id> <assignee>
READY <task_id> <assignee>
...
BUSY <0|1>
```

| 状态 | 输出示例 | 说明 |
|---|---|---|
| 有待审/待派卡 | `HB 14939358\nREADY t_36cbd22c cc-backend-developer\nREADY t_4c4a1991 cc-backend-developer\nBUSY 0` | 每 2 分钟 HB 桶变一次 → 周期性唤醒 agent |
| 无任何待办 | `NONE` | 字节恒定 → 零唤醒（监控静默） |
| 正在跑 worker | `BUSY 1` | 防止并行派单制造 429 |

## 关键设计点

### 1. 心跳桶防死锁

```python
# 有待办时：每 2 分钟必变
print(f"HB {int(now // 120)}")
# 无待办时：输出恒定哨兵
print("NONE")
```

- `int(now // 120)`：桶内字节稳定（不刷屏），跨桶必然变化（不会卡死）
- 同时是重试机制：卡住的工单每 2 分钟重新唤醒一次 agent，不需要额外 stale 计时器
- `BUSY 0|1` 把 worker 起停也算进输出，状态机自己成了唤醒源

### 2. monitor 门控语义

- monitor 输出与上一 tick **逐字节相同** → agent 完全不启动（零 token）
- 变了 → agent 被唤醒，prompt 里注入 diff
- 这正是 `watchdog-cron-patterns` 的「Agent 模式 + monitor 门控」

### 3. 实测验收（必须做）

```bash
# 1. 同桶内两次 md5 一致
python review_watch.py wechat_recovery | md5sum
python review_watch.py wechat_recovery | md5sum

# 2. 看一眼有没有 HB 行
python review_watch.py wechat_recovery

# 3. 等到下一次 tick（5 分钟），确认：
#    - last_run_at 有值
#    - 目标卡真的从 ready → running
#    - claude 进程数变 1
```

只有 "任务存在" 不算建成；必须实测一轮见到卡真动。

## Agent Prompt 必带五条

cron 任务的 prompt 必须自带（否则定时任务会自己编规矩）：

1. 审核由协调层本人做，不派 `cc-code-reviewer`
2. 不采信子员工自述，自己跑命令
3. 发现假 ✅ 直接 `request-changes`
4. 绝不把卡留在 `review`
5. `BUSY=1` 时不派新单（防 429 与双跑）

## 常见坑

| 坑 | 现象 | 修法 |
|---|---|---|
| HB 桶没加 | READY 卡长期不变 → monitor 输出恒定 → agent 永不唤醒 | 必须加 `HB {int(now//120)}` |
| monitor 只看状态不带 HB | 同上 | 同上 |
| NONE 里带换行/空格 | 输出不恒定 → 空转也会唤醒 | 严格 `print("NONE")` 单行 |
| cron 里没写 prompt 五条 | 定时任务自己派 `cc-code-reviewer`、并行派单、留卡在 review | prompt 必带五条 |
| 没实测一轮就宣布建成 | `last_run_at` 为 null，卡没动 | 必须等下一 tick 看到卡 `ready→running`、进程数变 1 |

## 扩展：用临时 SQLite 库自测

```python
import os, subprocess, sys, tempfile
from pathlib import Path

tmp_home = Path(tempfile.mkdtemp())
# 建临时 kanban 目录结构...
env = dict(os.environ, HERMES_KANBAN_HOME=str(tmp_home))
subprocess.run([sys.executable, "review_watch.py", "testboard"], env=env, text=True, capture_output=True)
```

比改真实看板安全：可造 `review`/`ready`/空三种状态各跑一遍。

---

*Distilled from wechat_recovery project (2026-10-22) — first successful watchdog with HB heartbeat preventing monitor deadlock.*