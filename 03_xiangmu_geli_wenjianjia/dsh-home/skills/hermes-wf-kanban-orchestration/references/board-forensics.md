# 看板取证：证明某个阶段到底有没有跑过

回答「X 环节在工作吗 / 是直接跳到完成还是经过了审查 / 这道闸真的拦过东西吗」这类问题时，
**不要看 CLI 帮助、不要看代码里的 if 分支、不要看列名** —— 只认磁盘上的两个证据源：
**看板 DB 的事件流** 和 **worker 日志的判定行**。

## 1. 证据源位置

| 证据 | 路径 |
|---|---|
| 看板 DB（分板） | `<hermes_home>/kanban/boards/<slug>/kanban.db` |
| 看板 DB（全局） | `<hermes_home>/kanban.db` |
| worker 日志 | `<install_dir>/logs/workers/<task_id>.out`（**追加**，不覆盖） |
| 派单状态 | `<install_dir>/logs/dispatch_state.json`（`fail` 字典 = 熔断计数） |
| 派单节拍 | `<install_dir>/logs/tick.log` |

## 2. 真实表结构（按列名写查询，别猜）

```
tasks        id, title, body, assignee, status, priority, created_by, created_at,
             started_at, completed_at, result, consecutive_failures, worker_pid,
             block_kind, block_recurrences, completion_contract, ...
task_events  id, task_id, run_id, kind, payload, created_at
task_runs    ← 运行记录（outcome / summary / ended_at）
task_comments, task_links, task_attachments, kanban_notify_subs
```

**最关键的一条：`task_events` 没有 status 列。** 只有 `kind` + `payload`(JSON)。
所以「某卡是否进过某状态」只能靠 **`kind` 的取值**判断，`payload LIKE '%<词>%'` 作辅证。
状态本身存在 `tasks.status`（只有当前值，没有历史）。

实测出现过的 `kind`（19 种）：

```
created  edited  linked  claimed  spawned  heartbeat  commented
completed  blocked  unblocked  archived  promoted  reclaimed  gave_up
decomposed  dependency_wait  block_loop_detected
skipped_nonspawnable  tip_scratch_workspace
```

## 3. 四个可复制查询

```python
import sqlite3
DB = r"<hermes_home>/kanban/boards/<slug>/kanban.db"
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; cur = c.cursor()

# ① 某阶段到底有没有跑过 —— 先列全部 kind，再看有没有你关心的那个
print([r[0] for r in cur.execute("SELECT DISTINCT kind FROM task_events ORDER BY kind")])

# ② payload 里有没有出现过某个词（第二道确认）
print(cur.execute("SELECT COUNT(*) FROM task_events WHERE payload LIKE '%review%'").fetchone()[0])

# ③ 表里有没有某个字段（状态机支不支持一个阶段，看这里最直接）
print([r[1] for r in cur.execute("PRAGMA table_info(tasks)") ])

# ④ 按卡还原状态链 —— 看是不是「直连完成」
from collections import defaultdict
seq = defaultdict(list)
for r in cur.execute("SELECT task_id, kind FROM task_events ORDER BY rowid"):
    seq[r["task_id"]].append(r["kind"])
keep = {"created","claimed","spawned","completed","blocked","unblocked",
        "reclaimed","gave_up","promoted","archived"}
titles = {r["id"]: r["title"] for r in cur.execute("SELECT id, title FROM tasks")}
for tid, ks in seq.items():
    chain, prev = [], None
    for k in ks:
        if k in keep and k != prev:
            chain.append(k); prev = k
    print(tid, " → ".join(chain), titles.get(tid, "")[:30])

# ⑤ 当前状态分布
for r in cur.execute("SELECT status, COUNT(*) n FROM tasks GROUP BY status ORDER BY n DESC"):
    print(r["status"], r["n"])
```

## 4. 判读规则

- **`kind` 计数为 0 = 该阶段从未运行**。列名/CLI/帮助里出现该阶段都**不算**证据。
- **`created → claimed → completed` 且中间没有别的状态 = 直连完成**，没有经过任何中间关口。
- `skipped_nonspawnable` 是网关对 `cc-*` 卡的预期跳过，**不是异常**。
- 熔断只存计数，看 `dispatch_state.json` 的 `fail`，且会计数残留到已归档卡（无害）。
- `list --json` **不含 parents**，查依赖链必须逐张 `show <id> --json`。

## 5. 第二类证据：闸门到底有没有拦下过东西

代码里有 `if EMPTY → block` 不等于它拦过。数**判定分布**才算验证过：

```bash
L="<install_dir>/logs/workers"
echo "produced : $(grep -h '产出校验: .*produced' "$L"/*.out | wc -l)"
echo "EMPTY    : $(grep -h '产出校验: .*EMPTY'    "$L"/*.out | wc -l)"
echo "skip     : $(grep -h '产出校验: .*verdict=skip' "$L"/*.out | wc -l)"
echo "无快照跳过: $(grep -h '产出校验: 跳过' "$L"/*.out | wc -l)"
echo "判定器异常: $(grep -h '判定器异常退出' "$L"/*.out | wc -l)"
```

- 全部落在「跳过 / 判定器异常」⇒ **这道闸名存实亡**（fail-open）。
- 有 EMPTY 且对应卡确实变成了 `blocked` ⇒ 闸是活的。
- 但**闸活着 ≠ 质量守住了**：产出校验只判「有没有产出」，判不了「产出对不对、验收跑没跑」。

## 6. worker 自述与事实的交叉核对

高信号、每次必看的三个动作：

```bash
# ① worker 自己说「验收没跑」的卡，状态却是 done —— 数量即风险面
grep -l '补跑\|未跑\|未能完成\|未执行\|证据缺失' "$L"/*.out
grep -l 'review' "$L"/*.out          # ② worker 主动请求审查的卡
# ③ 同一份日志里有没有真跑过命令（自述与实际矛盾）
grep -n 'python -c\|git status\|ast.parse' "$L"/*.out
```

判读：

- worker 说「本会话无 shell」**不可信** —— 角色定义带 `tools: Bash`、启动行带 `--allowedTools Bash`，
  且同一份日志里可能就有它真跑过的命令。**以日志里的命令痕迹为准。**
- worker 说「建议标记 review」而卡变成了 `done` ⇒ **包装脚本吞掉了审查请求**，不是 worker 没提。

## 7. 输出成证据表

给用户的结论必须是「结论 + 可复现证据」两栏并列，而不是叙述：

| # | 证据 | 结果 |
|---|---|---|
| 1 | `SELECT DISTINCT kind` 共 N 种 | 无 `<目标阶段>` 相关 kind |
| 2 | `payload LIKE '%<目标>%'` | 0 条 |
| 3 | `PRAGMA table_info(tasks)` | 无相关字段 |
| 4 | N 张终态卡的状态链 | 全部 `claimed → completed` |
| 5 | 当前状态分布 | `<目标阶段>` 恒为 0 |

每一条都要能被用户自己重跑复现 —— 不要出现「我检查过了」「应该是」这类无法复核的表述。

## 8. 第三类证据：执行器侧的会话转录（比 worker 自述可靠）

worker 的**完整会话**不在仓库、也不在 `logs/workers/`，而在 Claude Code 的配置目录里：

```
$CLAUDE_CONFIG_DIR/projects/<cwd 的 slug 化>/<uuid>.jsonl
例：.../projects/D--Ai-Agent-xiangmu-xianyu-agent-workflow-src-roles-marketing-planner/68206a66-....jsonl
```

- 目录名 = **worker 的 cwd 按 slug 化**（`D:\Ai\...\src\roles\marketing_planner` →
  `D--Ai-...-src-roles-marketing-planner`）。所以**从目录名就能看出每个角色实际在哪个目录干活** ——
  这是核对 `WF_AGENT_DIRS` 有没有真正生效的直接证据，不用去猜。
- 子代理另有 `<uuid>/subagents/agent-*.jsonl` 与同名 `.meta.json`。
- 用途：worker 自称「本会话无 shell / 没跑验收 / 已提交」时，转录里记着它**真实的工具调用序列**。
  争议时以转录为准，不以自述为准。
- 判「假 done」时三样对齐才叫完成：`task_runs` 的 outcome 序列 + 完成事件 `summary` 的长度 +
  转录里实际出现过的工具调用。只看前两样会把「先崩一次、再跑一次就算完成」漏过去。

