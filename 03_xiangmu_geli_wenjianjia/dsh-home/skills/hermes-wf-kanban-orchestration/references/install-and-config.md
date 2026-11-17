# Install, config, and troubleshooting — Hermes-wf kanban workflow

Depth for `hermes-wf-kanban-orchestration`. Key table, symptom→cause→action table, card
template, command cheatsheet.

## 1. `config.env` key table

Lives at `<hermes_home>/scripts/hermes-wf-<board>/config.env`. **It survives a reinstall**
(that is the whole reason to put machine-specific pins here rather than in the scripts).

Il manual's Appendix B is authoritative for the base keys; the ones that actually bite:

| Key | Meaning | Notes |
|---|---|---|
| `WF_BOARD` | kanban board slug | one board per project |
| `WF_REPO` | target repo, **forward-slash native path** (`D:/x/y`) | git-bash `/d/x` breaks native tools |
| `WF_AGENT_PREFIX` | `cc-` | anti-grab: only `<prefix>*` assignees are dispatched, so the built-in gateway dispatcher never touches these cards |
| `WF_AGENT_DIRS` | `agent=subdir,...` | disjoint cwd per worker. Must name agents that exist. Give each role a disjoint **output/resource** path too, not only a code dir |
| `WF_MAX_CONCURRENT` | parallel workers | 3 is a sane default |
| `WF_MAX_PER_AGENT` | cards per agent | keep `1` |
| `WF_CLAUDE_ARGS` | `--allowedTools ...` | **comma-separated**; space-separated is silently ignored → fake done |
| `WF_MAX_OUTPUT_TOKENS` | `32000` | dropping it truncates long reports and crashes the worker |
| `WF_VERIFY_KEYWORDS` | 验收,巡检,复核,盘点,闭环,演练,审计,只读,排查,对照实验 | matched against the card **title** only |
| `WF_BASH` / `WF_PYTHON` / `WF_HERMES` | tool pins | empty = auto-detect. Leave empty unless detection is wrong |
| `WF_CLAUDE` | absolute path to the `claude` executable | **needed when the sentinel runs under cron** — see §3 |
| `WF_CLAUDE_DIR` | dir to prepend to `PATH` as a fallback | only used when `WF_CLAUDE` is empty |
| `WF_CLAUDE_CONFIG_DIR` | value to `export CLAUDE_CONFIG_DIR` before dispatch | **needed under cron** — see §3 |
| `WF_STALE_RUNNING_SECONDS` | `1800` (30min) | worker 日志超时无更新即判定僵死，触发 `reclaim_stale()` |
| `WF_TEST_GATE` | `1` | 1=强制测试全绿，0=关闭（仅限明确知道测试环境不可用时） |
| `WF_BLOCKED_MAX_RECOVER` | `80` | 受阻卡自动恢复上限（过夜前必改，默认 3 太浅） |
| `WF_AGENT_TIMEOUT_SEC` | `1800` | 单卡最长运行秒数，过夜前建议从 7200 降到 1800 |
| `WF_FAIL_FUSE` | `5` | 失败熔断阈值：达到即长退避 |
| `WF_ABS_MAX_FAIL` | `15` | 绝对失败上限：达到即归档退出循环 |
| `WF_LONG_BACKOFF_SECONDS` | `1800` | 长退避秒数 |
| `WF_ACCEPT_MAX_REJECT` | `8` | 验收打回上限，达到即 block + 告警 |

### Never round-trip a masked value into a config file

Hermes masks credential-shaped substrings (long digit runs, tokens, keys) in *all* tool
output. A read → edit → write cycle therefore persists the **mask** into the file and
silently breaks the key.

- Match patches on an anchor that **excludes** the masked value, or
- blank the key and let auto-detection fill it (`WF_PYTHON=""` re-proves each candidate by
executing `python -c "import sys"`, which is stricter than a `command -v` check).
- After any `config.env` edit, re-read the neighbouring keys and confirm nothing else moved.

## 2. Repo prep — order matters

1. `git init` + set a user identity.
2. Create the whole directory layout (each role's code dir + output dir + resource dir), each
   with a `.gitkeep`.
3. **`git add -A && git commit` the scaffold before the first dispatch.** This is not
   housekeeping — it is what makes the produce-check work at all (§4).
4. `.gitignore` must contain `.worktrees/` **and** every credential path (`config/.env`,
   `.env`). `.worktrees/` is not ignored by default and one `git add -A` would commit an
   entire repo copy.

Confirm before committing: `git add -A --dry-run` and check no credential path appears.

## 3. Symptom → cause → action

| Symptom | Cause | Action |
|---|---|---|
| `claude: command not found`; dispatch log shows `exit=127`; card instantly `blocked` | The sentinel runs from **cron**, which does not inherit the user's env — the user's `PATH` never reaches it | Pin the binary: `WF_CLAUDE=<absolute path>` and have the dispatch script resolve `CLAUDE_BIN` from it instead of calling a bare `claude` |
| `--agent '<name>' not found`, and the printed "Available agents" equals the **fallback** dir's files + Claude Code's built-ins (`claude`, `Explore`, `Plan`, `general-purpose`, …) | Same cause, second variable: `CLAUDE_CONFIG_DIR` didn't reach cron, so Claude Code fell back to `~/.claude/agents` and your own agents are invisible | `WF_CLAUDE_CONFIG_DIR=<dir with your agents>` + `export CLAUDE_CONFIG_DIR` in the dispatch script. Prove it with `env -u CLAUDE_CONFIG_DIR claude --agent <name> …` — reproduces the error instantly |
| `verdict=EMPTY 零产出（HEAD 未变且工作区无变化）` but the files **are** on disk | Fingerprint is `md5(sorted(git status --porcelain))`, and porcelain collapses a wholly-untracked dir to one `?? dir/` line → nested writes change nothing | Commit the scaffold (§2). Afterwards nested writes show as ` M ` and the guard works. Independently verify the files before accepting the block |
| Worker exits 0 and did nothing | `--allowedTools` was space-separated | Comma-separate `WF_CLAUDE_ARGS` |
| Worker reports it has no `Bash`/shell, so it never commits | Model misreporting its toolset — the same invocation run by the coordinator has Bash | Put an explicit "you have Bash, run git/ls/python" line in every role's 完成须知; verify by asking, don't trust the self-report |
| Card stuck in `triage`, CLI refuses every move | `triage` is a one-way CLI door (see §5) | `archive` + recreate from the saved body file |
| `logs/tick.log` has a timestamp gap | the host slept | not a bug; check log continuity before debugging |

## 4. Produce-check fingerprint — both blind spots

The checker (`card_produce_check.py`) computes
`md5("\n".join(sorted(git(["status","--porcelain"]).splitlines())))` plus `git rev-parse HEAD`.

1. **Untracked-directory collapse** — described in §3. Fix by committing the scaffold.
2. **Two implementations disagree** — a bash-side `git status | md5sum` sees CRLF where the
   Python side sees LF, so the fingerprints never match and the guard always reports
   "produced". Keep exactly one implementation.

When the guard blocks a card, **verify the files yourself** (`ls -R` the card's file domain,
diff against the source) before believing it: a false block costs a worker's whole output and
pushes the card into `triage`.

## 5. `triage` is a one-way door

A card auto-escalates to `triage` after repeated block→unblock loops (commonly a produce-check
false block). From there:

- `promote` — refuses (`only applies to 'todo' or 'blocked'`)
- `unblock` — refuses (`not blocked/scheduled`)
- `schedule` — refuses
- `complete` — refuses (`unknown id or terminal state`)
- `specify` — the designed exit, but it makes an **LLM call** and fails outright when that call
  is denied (`LLM error: PermissionDeniedError`), which it may be

Recovery: `hermes kanban --board <b> archive <id>` and **recreate from the same body file**.
This is why card bodies should be written to a file first (`create --body-file <path>`) —
recreation then costs one command. Record the old id in the new card's body so the trail is
kept.

## 8. Kanban DB 损坏恢复（实测）

**症状**：`integrity_check` 报 `btreeInitPage() returns error code 11`，主库被截断、WAL 未合并。

**错误路径**：
- `mode=ro` 只读打开 → 读不到 WAL（comments 只读到 21 而非真实行数）
- `pragma journal_mode=DELETE` checkpoint 失败
- `SELECT count(*)` 返回坏页头垃圾值（实测 538 vs 真实 21）

**正确路径**：
1. 先复制 `kanban.db`、`kanban.db-wal`、`kanban.db-shm` 三件套到工作目录
2. 正常打开（非只读）让 SQLite 重放 WAL
3. 逐 `rowid` 探测真实行数（`SELECT * FROM table WHERE rowid=?` 循环，直到无结果）
4. 按 `rowid` 逐行重建新库（`INSERT INTO new_table SELECT * FROM old_table WHERE rowid=?`）
5. 新库跑 `PRAGMA integrity_check` → `ok`
6. 原库 + WAL + SHM 归档到 `_corrupt_archive/`

**关键点**：坏页头的 `count(*)` **不可信**，逐 `rowid` 读取才是真实数据量。先复制三件套再正常打开以重放 WAL。

**可复用实现**：`scripts/recover_kanban_db.py`（按 rowid 逐行重建）。

## 7. Card template

Keep the body in a file. Sections, in order:

```markdown
## 现象
<what is wrong / what is missing, observable>

## 根因
<the mechanism; for a migration card state that the source is read-only and why copy-not-move>

## 要求
<numbered, one deliverable; name every source path and every target path explicitly>

## 文件域（只准动这些）
- `src/roles/<role>/`

## 禁区
- the source tree, spelled out, marked read-only
- every other role's directory

## 验收（必须自测并附证据）
1. <a command that really runs, with the expected output>
2. <the untouched-source check>
3. <a syntax/parse check over the delivered files>
4. 未测项如实标注，不许写「应该没问题」
```

Title rules: one deliverable; **avoid `WF_VERIFY_KEYWORDS`** (验收/巡检/复核/盘点/闭环/演练/
审计/只读/排查/对照实验) — a title containing them is treated as verify-type and its
zero-output is waved through. Fix cards use 修/修复/新增/实现 instead.

## 7. Command cheatsheet

```bash
# boards / sentinel
hermes kanban boards list
hermes cron list --all
hermes cron remove <job-id>

# cards — ALWAYS pass --board (a global "current board" pointer drifts)
hermes kanban --board <b> create "<title>" --body-file <path> --assignee <agent> --priority <n> --json
hermes kanban --board <b> list
hermes kanban --board <b> show <id>
hermes kanban --board <b> comment <id> "<markdown>"
hermes kanban --board <b> unblock <id>
hermes kanban --board <b> archive <id>

# `block` takes the reason POSITIONALLY, not as --reason
hermes kanban --board <b> block <id> "<reason>"

# the sentinel
python <dir>/kanban_auto_dispatch.py --dry-run
python <dir>/kanban_auto_dispatch.py --once

# roster health (reports the effective config dir, agent count, name/filename consistency)
bash "$CLAUDE_CONFIG_DIR/scripts/agent-health.sh"
```

Verify a completion yourself, never from the worker's report:
`git log --all --oneline --grep="<card-id>"`, `git show --name-only <sha>`,
then re-run the card's key acceptance command with your own script.

## 8. 新增专用 Agent 落地清单（Agent Onboarding Checklist）

> 以 `cc-gui-tester` 为例，每次新增专用 agent 都要走完这套流程，缺一不可。

| 步骤 | 文件/位置 | 动作 | 验收 |
|---|---|---|---|
| 1. 定义 agent | `CLAUDE_CONFIG_DIR/agents/cc-<name>.md` | 写 SKILL.md 格式 frontmatter + 使命/工具/硬规则/交互优先级/验收标准/环境信息/权限确认 | `cat` 确认内容、前置解析无误 |
| 2. 同步备份区 | `CLAUDE_CONFIG_DIR/.hermes_backup/agents/cc-<name>.md` | `cp` 同步 | `diff` 两文件一致 |
| 3. Dispatch 注入工具 | `scripts/hermes-wf/dispatch_claude.sh` | 在 `case "$AGENT_NAME"` 里加分支，补 `--allowedTools $DEFAULT_TOOLS,<special_tool>` | `bash -n` 语法 OK、实测 dispatch 日志含 special tool |
| 4. 目录映射 | `scripts/hermes-wf/config.env` | `WF_AGENT_DIRS` 追加 `cc-<name>=<subdir>` | `agent_preflight.py` 报 "目录映射覆盖 全部 agent 已映射" |
| 5. 环境文档同步 | `scripts/hermes-wf/AGENT_ENV.md` | 表格追加 `cc-<name> | <special_tool>` | `agent_preflight.py` 报 "tools 权限 全部含 Read/Grep/Glob/Bash/Write/Edit" |
| 6. 预检数量 | `scripts/hermes-wf/agent_preflight.py` | 修改预期 agent 总数（如 30→31） | `python agent_preflight.py` 全绿 PASS |
| 7. 全量自检 | `scripts/hermes-wf/agent_preflight.py` | 跑完整自检 | `PASS 17 | WARN 0 | FAIL 0` |

**关键点**：
- **必须有 Write/Edit 权限**（fallback 只读会导致零产出）
- **special tool 必须在 dispatch 脚本里显式注入**（如 `computer_use`），空格分隔会被忽略导致假 done
- **WF_AGENT_DIRS 必须用逗号分隔**、**`cc-<name>=<subdir>` 格式**
- **预检脚本是最终裁判**——它检查前置解析、工具权限、落盘规则、备份一致性、目录映射、配置项、哨兵 cron，一条不漏
