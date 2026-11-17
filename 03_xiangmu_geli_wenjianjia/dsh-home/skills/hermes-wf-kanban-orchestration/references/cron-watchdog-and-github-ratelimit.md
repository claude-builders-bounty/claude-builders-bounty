# Cron Job Watchdog 坑 & GitHub API 限流处理

本文记录本轮发现的两类会导致「看起来像中毒/一直自动操作」的结构性问题及其解决模式。

---

## 1. Cron Job Watchdog 反复派单导致系统异常

### 现象
用户报告：
- "几秒钟拉一次 ccswitch"
- "鼠标被抢焦点"
- "怎么现在一直有东西自动操作"

### 根因
`hermes cron` 里有 **`window_tool 协调层看门狗（审+派单）`** (job_id `558ac3922cdf`)，**每 5 分钟跑一次**，当前 `enabled: true`。

它的逻辑：
- 每 5 分钟扫描 `window_tool` 看板
- 发现 `status=ready` 且 `assignee=cc-*` 的卡 → **强制派单** (`FORCE_DISPATCH=1 ./dispatch_claude.sh`)
- **当前 `t_539a4db1` 是 `running` 但被 block 了**（GitHub 429），看门狗可能误判为 ready 或重试逻辑有问题，**反复派单 → worker 启动 → 立即失败 (exit=1) → 循环**

你在进程里看到的 `hermes.exe kanban --board window_tool show t_539a4db1` 就是它派出的 worker。

**并行元凶**：`window_tool` 自身在后台跑着 (PID 14088)：
```
"C:\Users\Administrator\AppData\Local\Programs\Python\Python313\pythonw.exe" "D:\Ai\Agent\projects\window_tool\main.py" --minimized
```
它的热键 `Ctrl+Shift+W/H/S/T` + 托盘菜单可能与系统/其他软件冲突，导致「抢鼠标」。

### 立即解决方案
1. **暂停看门狗**：改 `cron/jobs.json` 的 `enabled: true -> false`（停止反复派单、停止 ccswitch 拉取）
2. **暂停/退出 window_tool**：托盘右键 → 退出，或改热键（`%APPDATA%\WindowTool\config.json`）
3. **把 `t_539a4db1` 手动改回 `todo` 或 `ready`**，等 GitHub 恢复后再手动派单，别让自动看门狗瞎搞

### 通用规则
**任何项目的看板如果有「自动看门狗」cron job，且该卡正卡在外部依赖（GitHub rate limit、API quota 等），必须先暂停看门狗，再手动控制派单节奏。** 否则会制造：
- worker 反复启动 → 即失败
- 看门狗再派 → 指数级失败日志
- 429 叠加（NVIDIA + GitHub 双重限流）
- 系统表现为「一直有东西自动操作」

> 看门狗配置见 `cron/jobs.json`，格式参考 `references/watchdog-implementation.md`。

---

## 2. GitHub API 限流（git clone/fetch/ls-remote）

### 现象
- `git ls-remote https://github.com/...` 返回 `fatal: unable to access '...': Empty reply from server`
- `git clone`/`fetch` 超时或 403/429

### 区别
NVIDIA 429 是推理通道限流，GitHub 限流是 **源码获取层**，不影响已在本地的编译/构建。

### 处理规则
1. **探测恢复**：定期 `git ls-remote <repo> HEAD`；返回 commit hash = 恢复。
2. **等恢复后再 unblock + FORCE_DISPATCH**：卡被 block 且 worker 日志显示 GitHub 连接失败，**不要在限流期间反复重派**；会白耗重试次数并连续失败。
3. **unblock 动作**：`hermes kanban unblock <tid> --board <board>` → `FORCE_DISPATCH=1 ./dispatch_claude.sh <tid> <agent> "prompt"`
4. **已 clone 的仓库不受影响**：`git fetch --tags`、`git checkout <tag>` 纯本地操作，无需网络。

### 实战模板（后台探测 + 自动重派）
```bash
# 每 2-3 分钟探测一次
until git ls-remote https://github.com/ggml-org/llama.cpp.git HEAD 2>&1 | grep -q '^[a-f0-9]\{40\}'; do
  sleep 120
done
# 恢复后
hermes kanban unblock t_539a4db1 --board window_tool
FORCE_DISPATCH=1 ./dispatch_claude.sh t_539a4db1 cc-backend-developer "继续执行 P10b: clone + checkout tag"
```

---

## 3. 看板批量清理：SQLite 直改（CLI 不可用时）

### 场景
`hermes kanban archive`/`delete` CLI 不可用（模块未安装、环境异常），需批量归档 done 任务、删除冗余任务链。

### 步骤
1. 定位 DB：`D:/Ai/Agent/hermes/kanban/boards/<board>/kanban.db`
2. 查看所有任务：`SELECT id, title, status, assignee FROM tasks;`
3. 批量归档 done 任务
4. 删除冗余/错误任务：`DELETE FROM tasks WHERE id='t_xxx';`
5. 验证：再次 `SELECT` 确认状态变更。

### 实战模板（本轮 window_tool 看板清理）
```python
import sqlite3
DB = r"D:/Ai/Agent/hermes/kanban/boards/window_tool/kanban.db"
conn = sqlite3.connect(DB)

# 1. 归档 11 个 done 任务
done_ids = [
    't_e1037a5a', 't_c99bd019', 't_4d7188ad', 't_439c3786',
    't_57fbf9bc', 't_abf7ed5c', 't_33546dbe', 't_ef9c6f85',
    't_c3d7bd6a', 't_b79d75e5', 't_7b2d92d7'
]
for tid in done_ids:
    conn.execute("UPDATE tasks SET status='archived' WHERE id=?", (tid,))
    print(f"Archived: {tid}")

# 2. 删除冗余旧 P10 任务（分配给不存在的 agent）
conn.execute("DELETE FROM tasks WHERE id=?", ('t_b65be317',))
print("Deleted: t_b65be317")

conn.commit()
conn.close()
print("Done!")
```

**注意**：直接改 DB 后 dispatcher 可能需要几秒感知；用 `hermes kanban list --board <board>` 读回确认。