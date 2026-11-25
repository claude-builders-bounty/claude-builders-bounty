# Review Gate & Stuck Task Fixer — 2026-10-23 实战沉淀

## 问题背景

本轮 `wechat_recovery` 项目实测发现：

1. **原版 `dispatch_claude.sh` 无审查闸门** —— 产出校验通过后直接 `complete`，0 张卡走 `review`
2. **`kanban_auto_dispatch.py` 不处理 `review` 状态** —— `skipped_nonspawnable {'assignee': 'cc-code-reviewer'}` 静默跳过
3. **派单父进程意外死亡导致审查闸门不执行** —— P4 worker 提交代码后父进程未捕获退出码，守卫⑦ `request-review` 分支未跑，卡卡在 `running`

## 修复清单（已落地）

### 1. `dispatch_claude.sh` 守卫⑦：审查闸门

```bash
# 产出校验通过后
kb_parent() { sqlite3 "$KANBAN_DB" "SELECT parent_id FROM task_links WHERE child_id='$TASK_ID' LIMIT 1;"; }
PARENT=$(kb_parent)
if [ -n "$PARENT" ]; then
  hermes kanban --board "$BOARD" request-review "$TASK_ID" --reviewer "$WF_REVIEWER" --summary "产出校验通过，提交 review"
else
  hermes kanban --board "$BOARD" complete "$TASK_ID" --summary "..."
fi
```

- `config.env` 新增：`WF_REQUIRE_REVIEW=1` / `WF_REVIEWER=cc-code-reviewer`
- 审查报告固定位置：`docs/REVIEW_{tid}.md`
- 首行固定：`# 审查结论：APPROVE` 或 `# 审查结论：REQUEST_CHANGES`
- 协调层亲审时：跑完实测 → 写报告 → `grep -q 'REQUEST_CHANGES'` 判定 → `request-changes` 打回

### 2. `kanban_auto_dispatch.py`：支持 `review` 状态派单

```python
# tick() 候选池
if t.get("status") not in ("ready", "running", "review"):
    continue

# 新增 review_prompt()
def review_prompt(task):
    return f"""【审查卡 {task['id']}】...
    必须产出 docs/REVIEW_{{tid}}.md，首行固定结论。
    不采信实现方自述，必须自己跑命令贴输出。
    发现『文档写 ✅ 但实际 False』直接判 REQUEST_CHANGES。"""
```

### 3. `stuck_task_fixer.py`：僵尸卡兜底（新增）

```python
# cron 每 5 分钟
for card in get_running_cards():
    if not is_claude_alive(card['worker_pid']) and git_head_changed(card['id']):
        request_review(card['id'], reason="worker 进程已退出但有新提交，触发兜底审查")
```

- 集成到看门狗 `review_watch.py`（`REVIEW/READY/BUSY/NONE + HB` 心跳）
- cron `c296db0ca793` 每 5 分钟执行
- 端到端验证：19:05 自动派单 P0 → 完成 → 协调层自动审 → APPROVE

## 关键经验（Pitfalls）

### ⛔ 审查闸门不在看板状态机里，必须自己在派单器里接线

看板原版只有 `ready/running/done/blocked`，没有 `review`——这是设计如此。手册 §6.3：**「它只负责派。验收不在它里面——完成后由协调者负责。」** 所以：

- **不走 `kanban request-review` = 无审查**，哪怕看板列名里有 `review`
- 必须在 `dispatch_claude.sh` 产出校验后显式调用 `request-review`
- 自动派单器必须识别 `review` 状态并派单给 reviewer 角色

### ⛔ 派单父进程死亡 = 审查闸门失效，需独立兜底

- worker 正常退出但父进程已死 → 守卫⑦ 代码分支根本不执行
- 表现：卡停在 `running`，git 有新提交，看板事件只有 `claimed` 无 `completed`
- **兜底脚本独立于派单器**，读 DB 直判：`running` + 无进程 + HEAD 变 → 触发 `request-review`
- 不要试图在派单器里加心跳/信号量修父进程死亡——太脆弱，独立兜底更稳

### ⛔ `kanban edit --body` 写不了多行，改卡正文必须走 SQLite

- `--body "多行"` → 只写最后一行；`---` 开头直接 rc=2
- 改正文：`sqlite3 kanban.db "UPDATE tasks SET body=? WHERE id=?"` → `kanban show` 读回验证
- 这影响：给 9 张卡追加「多机通用」要求、回填审查约束、消毒卡面反向指令

### ⛔ 协调层亲审必须真跑实测，不采信 worker 自述

- P1 worker 声称 `.dat` 解密 verified=True，实测 10/10 全 False
- P0 文档写「CER 4.2% 本地实测 50 条」，无样本无脚本
- P2 143 个加密 `.bin` 被当已恢复写入输出目录
- **审查报告必须贴真实命令输出**，没有输出 = 没验收

### ⛔ 零硬编码红线：业务代码禁用本机路径

- 仅允许在 `tests/fixtures/` 和 `docs/` 示例中出现 `wodwend` / `wxid_96ij4nce` / `4.1.0.34`
- 发现一处 → 全量 grep 扫描全仓库，不许只改报错那一处
- `path_helper.py` 第 3 次返工修复：`COMMON_DATA_DIRS` 只拼盘符+固定相对路径，`wodwend` 层从未成为候选根

### ⛔ 失败不落盘，诚实报告

- P2 最终版：`11 copied_plain + 163 failed = 174`，V2 泄漏 0
- 失败 reason 可诊断（`probe_dat` 返回 `verified=False` + 原因）
- 这比「假成功」对下游安全得多

## 相关文件

| 文件 | 作用 |
|---|---|
| `scripts/hermes-wf/dispatch_claude.sh` | 守卫⑦ + `kb_parent()` |
| `scripts/hermes-wf/kanban_auto_dispatch.py` | `review` 状态派单 + `review_prompt()` |
| `scripts/hermes-wf/stuck_task_fixer.py` | 僵尸 running 卡兜底审查 |
| `scripts/hermes-wf/review_watch.py` | 看门狗（确定性输出 + HB 心跳） |
| `scripts/hermes-wf/config.env` | `WF_REQUIRE_REVIEW=1` / `WF_REVIEWER=cc-code-reviewer` |
| `scripts/hermes-wf-xianyu/verify_model_channel.py` | 模型通道自检（含 `--restart`） |
| `docs/REVIEW_*.md` | 审查报告模板（首行固定结论） |

## 验收判据

1. 派单 → 产出 → `request-review` 自动触发（日志含 `request-review t_xxx`）
2. `kanban_auto_dispatch.py --once --dry-run` 能看到 `review` 卡被派给 `cc-code-reviewer`
3. 杀掉 dispatch 父进程、保留 worker 跑完 → `stuck_task_fixer.py` 能检测到并触发 `request-review`
4. 审查报告 `docs/REVIEW_{tid}.md` 首行 `grep -E 'APPROVE|REQUEST_CHANGES'` 命中
5. 协调层亲审实测：真实命令输出贴进报告，无输出 = 未验收
6. `grep -r 'wodwend|wxid_96ij4nce|4\.1\.0\.34' --include=*.py` 业务代码 0 命中
7. 失败文件不落盘、失败统计可核对