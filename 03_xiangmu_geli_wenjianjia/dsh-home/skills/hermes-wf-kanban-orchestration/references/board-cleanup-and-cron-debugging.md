# 看板板面清理 + Hermes Cron 看门狗排查 + GitHub 429 处理

## 看板板面清理（归档/去重/依赖链保护）

**场景**：项目阶段结束，P0-P9 全 done，存在冗余旧链路（分配给不存在的 agent）、已完成任务占板面。

**步骤**：
1. `kanban_list --board <board>` 列出所有任务，识别：
   - 全部 `done` 的旧阶段任务 → **archived**
   - 分配给不存在 agent 的冗余任务 → **DELETE**（SQLite 直接删）
   - 正规依赖链路（parent→child）→ **保留**，等上游恢复自动推进
2. **归档 done 任务**（批量，保留历史记录）：
   ```sql
   UPDATE tasks SET status='archived' WHERE id IN ('id1','id2',...);
   ```
3. **删除冗余任务**（彻底移除，不留痕）：
   ```sql
   DELETE FROM tasks WHERE id='redundant_id';
   ```
4. **验证依赖链完整**：`SELECT * FROM task_links WHERE child_id IN (剩余任务);` 确认 parent 关系未破坏。

**铁律**：
- 绝不 `DELETE` 有 `children` 依赖它的任务（会孤儿化子卡）
- `archived` 优于 `DELETE`——保留审计轨迹，仅移除板面显示
- 清理前先 `kanban_list` 截图/记录，防误删

## GitHub API 限流（429）处理标准流程

**症状**：`git clone/fetch` 返回 `Empty reply from server` / `429 Too Many Requests`，worker 反复启动即失败 `exit=1`，卡片被置 `blocked`。

**标准流程（严禁在限流期重派）**：
1. **探测恢复**：`git ls-remote https://github.com/... HEAD` —— 返回 commit hash 即恢复
2. **等待恢复后**：`kanban_unblock <task_id> --board <board>` 解除 block
3. **强制重派**：`FORCE_DISPATCH=1 ./dispatch_claude.sh <task_id> <assignee> "..."`
4. **链路自动推进**：child 任务依赖 parent `done` 自动 `ready` → 派单

**反模式（必犯错）**：
- ❌ 在 429 期间反复 `dispatch` / `unblock` → 耗尽重试、污染 failure_streak
- ❌ 手动 `git clone` 绕过看板 → 破坏派单契约、产出校验失效
- ❌ 改派其他 agent → 环境不一致、编译参数错配

## Hermes Cron 看门狗异常排查

**症状**：「几秒钟拉一次 ccswitch」「有东西自动操作」「抢鼠标」——实为 Hermes 内置 cron job 在跑。

**排查步骤**：
1. **读取 jobs.json**：`read_file D:/Ai/Agent/hermes/cron/jobs.json`
2. **定位高频 job**：找 `schedule.kind=interval, minutes≤5, enabled=true` 的 job
3. **确认逻辑**：读其 `prompt`/`script` —— 若含「派单」「扫描看板」「FORCE_DISPATCH」即为看门狗
4. **暂停/禁用**：在 jobs.json 里改 `enabled: true → false`，或 `hermes cron pause <job_id>`
5. **清理已派 worker**：`tasklist | findstr hermes` 找到派单产生的 `hermes.exe kanban show` 进程，结束之

**本次实例**：`window_tool 协调层看门狗` (id `558ac3922cdf`) —— every 5m，扫描 `window_tool` 看板，发现 `ready` 卡强制派单。当前 `t_539a4db1` 因 GitHub 429 被 block，看门狗误判/重试 → 反复派单失败。

**修复**：暂停该 job，等 GitHub 恢复后手动派单，再恢复 job。

## window_tool 热键冲突缓解

**症状**：鼠标被抢、热键误触发、托盘菜单弹出干扰。

**原因**：`window_tool` (PID 14088) 以 `pythonw.exe main.py --minimized` 常驻后台，注册全局热键 `Ctrl+Shift+W/H/S/T`。

**缓解**：
- 托盘右键 → **暂停热键** / **退出**
- 或改热键：编辑 `%APPDATA%\WindowTool\config.json` 的 `hotkeys` 字段
- 或卸载：删除注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` 中 WindowTool 项