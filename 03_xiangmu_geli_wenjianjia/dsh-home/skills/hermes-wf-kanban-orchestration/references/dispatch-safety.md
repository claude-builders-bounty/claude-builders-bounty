# 派单防重与 worker 生命周期

派单（`dispatch_claude.sh`）是唯一会让看板与实际执行脱节的动作。每次派单前后按本文核对。

## 1. 派单前必须查重（一卡一 worker）

```bash
powershell -NoProfile -Command "Get-Process -Name claude -ErrorAction SilentlyContinue | Select-Object Id,StartTime | Format-Table -AutoSize"
hermes kanban --board <board> list
```

规则：**一张卡同时只能有一个 claude 进程。** 两个 worker 写同一个 git 树会互相覆盖产出，而产出校验只看 HEAD 是否变化——覆盖了也照样判 produced，等于把冲突藏起来。

看着板状态判断不准，必须两样都看：看板 `running` 但无 claude 进程 = 僵尸卡；有 claude 进程但卡是 `ready`/`triage` = 更危险，dispatcher 下一次 tick 会再派一份。

## 2. `exit=127` 先怀疑自己的 kill，再怀疑环境

`dispatch_claude.sh` 用 `CLAUDE_OUTPUT=$(claude ... 2>&1); EXIT=$?` 取退出码，失败即 `block` 卡。

**在 dispatch 父进程还活着时杀掉它的 claude 子进程（`Stop-Process -Id <claude_pid>`），脚本会把这次异常退出报成 `失败(exit=127) → block`。** 这是自己造成的，不是 `claude` 不在 PATH。

判别方法：在项目根直接跑一次

```bash
claude --agent <agent> --allowedTools Bash,Read,Write,Edit,MultiEdit,Grep,Glob -p "回答两个字：在线"
```

返回正常且 `exit=0` → 环境没问题，127 是 kill 造成的，不用去查 PATH / 认证 / 代理。省下的是几轮无损诊断。

只有在裸跑也失败时，才去查 `which claude`、`CLAUDE_CONFIG_DIR`、cc-switch 代理。

## 3. 僵尸卡的处理顺序

卡被 block-loop 升级成 `triage`、或 reconciliation 把 `running` 改回 `ready`，而 claude 进程还在跑时：

1. 选一个留下。要么让 dispatcher 自动接走的那个新 worker 干（它会重新 claim），要么留旧的。**不要两个都留。**
2. 杀掉不要的那个：`powershell -NoProfile -Command "Stop-Process -Id <pid> -Force"`；它的 dispatch 父进程若还活着也一并杀，否则父进程会再写一次 block。
3. 用 SQLite 把卡状态与留下的 worker 对齐（`kanban edit` 改不了这些字段）：

```python
import sqlite3, datetime
DB = r"D:\Ai\Agent\hermes\kanban\boards\<board>\kanban.db"
conn = sqlite3.connect(DB)
now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
conn.execute("""UPDATE tasks SET status='running', worker_pid=?, worker_started_at=?,
                claim_lock=NULL, claim_expires=NULL, block_kind=NULL,
                block_recurrences=0, consecutive_failures=0,
                last_heartbeat_at=? WHERE id=?""", (pid, now, now, tid))
conn.commit()
```

`block_recurrences` 必须归零，否则这张卡下一次失败会被 block-loop 直接推进 `triage`，不再进 `ready`。

4. 改完用 `kanban list` 读回确认，不要只看 SQL 返回值。

**把卡直接写成 `done` 时同样必须清 claim 字段。** 只改 `status='done'` 而留下 `claim_lock` / `claim_expires` / `worker_pid`，reconciliation 会发现锁指向一个已不存在的 PID，把这张卡重新判成 `running` 并再次派单——一张**已经验收通过**的卡会自己复活、重跑、覆盖产出，而且看起来像「审查结论丢了」。完整写法：

```python
conn.execute("""UPDATE tasks SET status='done', completed_at=?,
                worker_pid=NULL, worker_started_at=NULL,
                claim_lock=NULL, claim_expires=NULL,
                block_kind=NULL, block_recurrences=0, consecutive_failures=0
                WHERE id=?""", (now, tid))
```

巡检：`SELECT id, status, claim_lock FROM tasks WHERE status='done' AND claim_lock IS NOT NULL` 必须返回空。

## 4. 派单前确认卡存在

对不存在的 task id 调 `dispatch_claude.sh` **不报错**：脚本 claim 失败后直接退出，worker 日志是空文件。表现是「派了单但什么都没发生」。

派单前 `hermes kanban --board <board> show <id>` 确认卡存在且 assignee 正确。空日志 = 卡号错，不是 worker 挂了。

### 4b. 派单前确认 Agent 存在（关键）

**派单前必须验证 assignee 对应的 Claude Code agent 文件存在**：
```cmd
rem 检查 ~/.claude/agents/cc-<name>.md 或 CLAUDE_CONFIG_DIR/agents/cc-<name>.md
dir "%CLAUDE_CONFIG_DIR%\agents\cc-<assignee>.md" 2>nul || dir "%USERPROFILE%\.claude\agents\cc-<assignee>.md" 2>nul
```

**或用 CLI 验证**（更可靠，直接问 claude）：
```cmd
claude --agent cc-<assignee> -p "回答两个字：在线"
```

- 返回 `exit=0` 且输出包含「在线」= agent 存在且可用
- 返回 `exit=1` 且错误含 `--agent 'cc-<assignee>' not found. Available agents:` = **agent 不存在，派单必失败**

**实战教训（2026-10-29）**：任务 `t_c94b1392` assignee 写成 `cc-houduan`，该 agent 从未创建过。派单报 `--agent 'cc-houduan' not found`，卡被 block。改为现有的 `cc-planner` 后派单成功。

**规则**：建卡/改 assignee 时，**必须先验证 agent 存在**，不要凭记忆或推测写名字。

### 4c. 派单前确认 cron job 状态与 config.env 一致性

**两个常见静默失败原因**：

1. **cron job 处于 `paused` 状态** → 自动派单永不触发
   - 检查：`cat D:/Ai/Agent/hermes/cron/jobs.json | jq '.jobs[] | select(.name=="wf:xiangmu 自动派单哨兵") | .enabled'`
   - 修复：设 `"enabled": true, "state": "scheduled"`

2. **`config.env` 里的 `WF_BOARD` 与实际看板不一致** → 派单脚本读错配置
   - 检查：`grep WF_BOARD D:/Ai/Agent/hermes/scripts/hermes-wf/config.env`
   - 必须与目标看板同名（如 `WF_BOARD="xiangmu"`），否则 `kanban_tick.py` 会去捞错板的任务

3. **`WF_REPO` 路径指向不存在的子目录** → `NotADirectoryError` 派单异常
   - 检查：`grep WF_REPO D:/Ai/Agent/hermes/scripts/hermes-wf/config.env`
   - 必须指向 **git 仓库根目录**（含 `.git`），不是 `project/` 等子目录

**实战教训（2026-10-29）**：
- xiangmu 看板的派单哨兵 cron job `caa798b85865` 处于 `paused` 状态
- `config.env` 里 `WF_BOARD="window_tool"`（旧板名），`WF_REPO="D:/Ai/Agent/xiangmu/project"`（不存在的子目录）
- 修正后手动跑一次 `WF_BOARD=xiangmu WF_REPO="D:/Ai/Agent/xiangmu" python kanban_tick.py` 派单成功

**规则**：每次接手新看板/新项目，必须核对这三项：cron enabled、WF_BOARD、WF_REPO。

## 5. 建卡的正确姿势

```bash
hermes kanban --board <board> create "<标题>" \
  --assignee <agent> --priority <n> \
  --workspace "dir:<绝对路径>" \
  --parent <父卡id> \
  --body-file "D:/Ai/Agent/hermes/cache/scratch/body.txt"
```

- `--title` 不存在，标题是**位置参数**。
- `--body` 处理不了多行（静默只写最后一行），多行正文一律 `--body-file`。
- `--body-file` 的路径必须写成 `D:/...` 原生形式；MSYS 的 `/tmp/x` 不会被翻译，报 `No such file or directory: '\\tmp\\x'`。
- 已经存在的卡要改多行正文，走 SQLite 直改 `tasks.body`（见 `kanban` 本体记录），改完 `kanban show` 读回。

## 6. 审查闸门（Guard ⑦：dispatch_claude.sh 内置）

**默认开启**（`WF_REQUIRE_REVIEW=1`，关掉设 0）。流程：

```
产出校验通过
  ├─ 本次是审查员跑完 → 解析 docs/*REVIEW*.md
  │     ├─ 含 REQUEST_CHANGES → 自动 request-changes 打回父卡
  │     └─ 否则 → complete
  └─ 普通实现卡 → request-review 交 cc-code-reviewer（不直接 done）
```

实现卡跑完自动进 `review` 列，assignee 变为 `cc-code-reviewer`。

**审查卡正文必须写明**：逐项 `PASS / FAIL / NEEDS_CLARIFICATION`、FAIL 给 `文件:行号` 建议、结论 `APPROVE / REQUEST_CHANGES`、报告落盘到 `docs/*REVIEW*.md`（脚本按最新修改时间取）。

**依赖链**：实现卡 → 审查卡（parent） → 下游卡。下游卡的 `--parent` 必须指向审查卡，否则审查没过下游就开工。

**但 `request-review` 并不建新卡**：它把**同一张实现卡**的 assignee 换成审查员、状态改 `review`。走这条路时「父卡」根本不存在，审查员判 `REQUEST_CHANGES` 也没有对象可打回——卡会以 `done` 收场，下游卡同时被自动 promote 成 `ready`，等于拿未通过的产出解锁下一环。三件事必须手动补：

1. 读报告首行结论；`REQUEST_CHANGES` 时用 SQLite 把卡改回 `status='ready'`、`assignee=<原实现方>`，清 `completed_at` / `worker_pid` / `worker_started_at` / `claim_lock` / `claim_expires`，`block_recurrences=0`。
2. **把已被 promote 的下游卡压回 `todo`**：`UPDATE tasks SET status='todo' WHERE id IN (...) AND status='ready'`。少这一步，下一 tick 就按错的前提开工。
3. 打回原因写进 `tasks.body`（`kanban edit --body` 不支持多行），并给出「改哪里 / 怎么改 / 验收命令」。只写「不通过」等于挂起等人工。

对 `review` 状态的卡直接调 `dispatch_claude.sh` 会提示「claim 后看板状态为 'review'（非 running）」；确认要跑就加 `FORCE_DISPATCH=1`，不要因为这条警告去改卡状态。

**关键点**：
- 产出校验 ≠ 审查通过。产出校验只看「有没有 commit」，不看「对不对」。
- **闸门只负责把卡送进 `review`，不负责把它接走。** 两处会同时漏：
  1. Hermes 内置 dispatcher 只调度 Hermes profile，`cc-*` assignee 记 `skipped_nonspawnable`；
  2. `kanban_auto_dispatch.py` 的 `board_tasks()` 若没把 `review` 放进状态白名单，也只捞 `ready`/`running`。

  两条一起漏 = 卡永久停在 `review`，比没闸门更糟（看起来在审，实际没人碰）。
- 修法按序选：
  1. **协调层自己审**（首选，见 SKILL.md 硬规则 3）——审完直接 `complete` / `request-changes`，根本不进 dispatcher。
  2. 要交给子员工审：`kanban_auto_dispatch.py` 状态白名单加 `review`、`tick()` 待派列表改 `("ready","review")`、新增 `review_prompt()` 要求产出 `docs/REVIEW_{tid}.md` 且首行固定 `# 审查结论：APPROVE|REQUEST_CHANGES`（脚本靠这行 grep 出结论）。
- 协调层亲审时报告写 `docs/REVIEW_{tid}_COORD.md`，**不要覆盖**子员工那份；两份都留可对照，也能看出子员工哪次写了假结论。
- **落盘前先 `ls docs/ | grep -i <tid>` 找当前轮次。** 长跑项目里同一张卡会返工多轮，看门狗也可能已经让 `cc-code-reviewer` 先写了一版 `_R5.md`；直接按记忆里的轮次号写会被 `write_file` 的 stale-write 保护拒掉，白跑一趟。命名沿用 `_COORD.md`（首轮）/ `_COORD_R{N}.md`（第 N 轮），已占用就往下一个空号写，**永不覆盖**——历史轮次是判断「同一个问题被打回了几次」的唯一依据，也是决定该归档退出循环的凭据。

### 6b. 审查闸门的前置条件：必须捕获到 worker 退出码

`dispatch_claude.sh` 的 Guard ⑦ 在 `if [ "$EXIT" -eq 0 ]` 分支内，只有 worker 进程退出码被捕获时才执行 `request-review`。若 dispatch 父进程提前退出（进程树被清理、父进程 crash、系统重启），worker 即使正常跑完并提交，**卡停在 `running`，永远不进 `review`**。

现象：事件表只有 `claimed`，无 `completed`/`request-review`；`git log` 有新提交但卡状态没变。

**兜底修复**：在看门狗 `review_watch.py`（或独立 `stuck_task_fixer.py`）加检测：
```python
# 发现 running 但无 claude 进程的卡
if task.status == 'running' and not claude_running():
    # 有新提交（比对 HEAD 或工作区指纹）
    hermes kanban request-review <tid> --reviewer cc-code-reviewer
```

每 5 分钟 cron tick 时自动跑一次，防止「假跑完」卡死。见 `stuck_task_fixer.py` 实现。

### 6c. 手动派单兜底（cron 失效时）

NVIDIA API 402/429、cron monitor 报错等导致自动化停摆时，**手动派单完全可用**——只要环境变量/认证配置正确，`FORCE_DISPATCH=1 ./dispatch_claude.sh <tid> <agent> "prompt"` 直接跑，不依赖 cron/NVIDIA。

操作：
1. 确认无 claude 进程（`Get-Process -Name claude` 返回 0）
2. 卡状态为 `ready`（或手动改回 `ready`、清 `worker_pid`/`claim_lock`）
3. 手动派单
4. 等 worker 跑完 → 协调层亲审 → `complete` / `request-changes`

**不要等 cron 修好才推进**。手动派单 + 协调层亲审是主流程的降级路径，不是应急绕过。

子员工最常见的失败不是写不出代码，而是**把没跑过的结果写成「已验证」**。形式统一：文档里全 ✅、commit message 写「Pillow 验证通过」「本地实测 CER 4.2%」，而实际返回 False / 文件不存在 / 脚本不存在。

审之前自己跑这五样（少一样就可能放过假结论）：

```bash
# 1. 测试
python -m pytest tests/ -q
# 2. 文档声称的每条关键命令，挑真的跑
grep -n "✅" docs/*.md | head -30
# 3. 声称存在的文件/目录，挨个 ls（最常见造假点）
ls -la tests/asr/bench_cer.py docs/COMPATIBILITY.md
# 4. 声称的路径真能不能被发现（函数级复核）
python -c "from utils.path_helper import find_wechat_data; print(find_wechat_data())"
# 5. 全仓硬编码
grep -rn "wodwend\|wxid_\|4\.1\.0\.34" --include="*.py" .
```

**第 6 项：产物本身是不是垃圾。** 文档假 ✅ 只是第一层；第二层是**产物存在但内容是原始密文／占位数据的拷贝**。文件数、`pytest` 全绿、`PIL.verify()` 都能通过（源文件本来就没加密时），但「恢复了 143 个」实际 143 个都是改了扩展名的加密原文。查验方法：产物头部是否仍是输入密文的魔数、产物字节数是否与源文件 100% 相等、每个声称成功的文件是否都用真解析器打开过。完整探针与「成功率门槛逼出造假」的修法见 `evidence-backed-deliverables`。

三条判定口径：
- 文档写 ✅ 而实际 False → **REQUEST_CHANGES**，不讨论。
- 声称存在的目录 `exists=False` → REQUEST_CHANGES，并要求改成「待实测确认」。
- 只有「真跑过、能贴出命令与输出」才允许写「实测」；否则只能写「官方宣称 / 第三方来源 / 待实测」。**做不到写「未能实测」不扣分，编造实测直接打回。**

还有个隐蔽形态：**修了验证，没修发现**。例如为了「能找到数据目录」，只放宽了 `_is_valid_root()` 的校验，却没改候选根的生成逻辑（仍只拼「盘符 + 固定相对路径」）——结果校验通过一万条，一条候选也产生不出来。审查时必须调用**入口函数**看真实返回值，不能只看辅助函数是否变宽。

**实战案例（本会话）**：`find_wechat_data()` 返回空，`deep_scan(["D:"])` 也返回 0。根因是 `COMMON_DATA_DIRS` 只拼固定相对路径（`D:\xwechat_files`），而真实数据在 `D:\wodwend\xwechat_files`——中间的 `wodwend` 层从未成为候选根。上一轮加的 `_has_wxid_subdir()` 只用于**校验**候选根，不负责**产生**候选根，等于修了验证没修发现。修法是新增按目录名的有界递归扫描（`_scan_for_data_dirs`），命中后再校验，结果并入候选根、来源标记 `name_scan`；`deep_scan` 共用同一实现。

## 7d. 运行时契约审查（服务层 / UI 接入类交付必跑）

静态审查（pytest 全绿、py_compile 通过、grep 零硬编码）全过 **≠ 程序可用**。这类交付必须亲自调用入口函数，拿返回值与真实状态对撞。四条必查：

1. **返回值必须与真实状态自洽。** 典型形态：`initialize()` 返回 `True`，同时 `is_ready()` 返回 `False`、`_db_reader is None`——9 项服务里 4 项失败仍报成功，UI 因此直接进主界面，用户点任何功能都是空白，还以为软件坏了。断言写法：

   ```python
   ok = await svc.initialize()
   assert ok == svc.is_ready(), "initialize 与 is_ready 语义不一致"
   ```

   任一核心依赖为 `None` 就必须 `return False`，并把失败清单暴露给 UI；无条件 `return True` 等于对外宣称「一切正常」。

2. **列表数据必须真实、去重、排序。** UI 展示的每个列表都亲自数一遍：长度、每项关键字段、默认选中项。实测形态——账号列表返回 6 条，其中 4 条是 `all_users/login/` 登录记录与 `Backup/` 空备份（`msg_db_count=0`、几十 KB），默认取 `[0]` 恰好选中 25MB/5DB 的次要账号，而数据最多的 56MB/7DB 那个没被选。规则：过滤 `db_count==0 and size<1MB` → 同 id 去重保留最大 → 按 `(-db_count, -size)` 排序 → 取首个作默认。

3. **错误信息必须指向真实原因。** 「应用版本不支持」被写成「应用未运行」，用户会去重启程序，白折腾一圈。审查时把 UI 显示的 error 文案与日志原始异常逐字对照；异常按类型分支，版本类错误必须带版本号。

4. **证据文件必须真实存在。** 文档写「截图 ≥5 张存 `scratch/ui_screenshots/`」就先 `ls`：目录为空、`.png` 计数 0，而文档里 `[x]` 照打 = 造假。同理适用于日志、基准脚本、fixtures、模型权重。

判定口径与 §7c 一致：文档写 ✅ 而实测 False → `REQUEST_CHANGES`，不讨论。

**连带检查**：入口返回 False 时 UI 是否走降级页？没接降级分支，等于把「初始化失败」包装成「空数据」，比直接报错更难排查。

## 8. 429 限流 → 串行派单

通道限流时 dispatch 会连续 4 次 429，每次退避 300s，一张卡能拖掉近 1 小时并最终 `block`。429 不是代码问题，不要改脚本、不要查认证。

规则：**同时只跑一个 claude。** 派下一个前先测：

```bash
powershell -NoProfile -Command "@(Get-Process -Name claude -ErrorAction SilentlyContinue).Count"
```

返回 `0` 才派。并行派多个 worker = 自己制造 429，还会叠加双写同一 git 树的风险（见 §1）。

「串行」不等于「慢」：一张卡跑 20 分钟，排队也比四张卡全被 429 打回再重试快得多。

**实测重试模式（NVIDIA API / 公益站通用）**：
- 连续 4 次 429，每次退避 300s（5 分钟）
- 第 4 次仍 429 → worker 落回 `complete`（不再 `request-review`）
- 协调层应预期此模式：单卡最大等待 20 分钟，必要时手动 `FORCE_DISPATCH=1` 绕过

### GitHub API 限流（git clone/fetch/ls-remote）

**现象**：`git ls-remote https://github.com/...` 返回 `fatal: unable to access '...': Empty reply from server`；`git clone`/`fetch` 超时或 403/429。

**区别**：NVIDIA 429 是推理通道限流，GitHub 限流是 **源码获取层**，不影响已在本地的编译/构建。

**规则**：
1. **探测恢复**：定期 `git ls-remote <repo> HEAD`；返回 commit hash = 恢复。
2. **等恢复后再 unblock + FORCE_DISPATCH**：卡被 block 且 worker 日志显示 GitHub 连接失败，**不要在限流期间反复重派**；会白耗重试次数并连续失败。
3. **unblock 动作**：`hermes kanban unblock <tid> --board <board>` → `FORCE_DISPATCH=1 ./dispatch_claude.sh <tid> <agent> "prompt"`
4. **已 clone 的仓库不受影响**：`git fetch --tags`、`git checkout <tag>` 纯本地操作，无需网络。

**实战模板（后台探测 + 自动重派）**：
```bash
# 每 2-3 分钟探测一次
until git ls-remote https://github.com/ggml-org/llama.cpp.git HEAD 2>&1 | grep -q '^[a-f0-9]\{40\}'; do
  sleep 120
done
# 恢复后
hermes kanban unblock t_539a4db1 --board window_tool
FORCE_DISPATCH=1 ./dispatch_claude.sh t_539a4db1 cc-backend-developer "继续执行 P10b: clone + checkout tag"
```

## 7. 协调层的动作边界

用户要的是「看好工作流、做好分派协调，不要做多余的事」。

允许：查看板、查进程、派单、建卡、卡住时打回或重派、报结果。
禁止：散着做环境诊断（连着几轮 `claude --version` / PATH / 代理排查）、顺手改代码、顺手验证完就交。

用户问「你干嘛呢」= 已经在做多余动作，立刻收回到「盯卡 → 解锁就派 → 报结果」。

**通用配置要求（多机通用/换机通用）**：代码里不许出现本机具体路径/账号/版本（D:/wodwend, wxid_xxx, 4.1.0.34 等）。必须实现：
- 零硬编码红线（仅 tests/fixtures、docs 示例可出现）
- 5 层自动扫描：注册表 → 盘符遍历 × 6 路径 → 配置文件 → 进程反推 → 全盘兜底
- 手动目录选择：FilePicker 选任意目录（U盘/网络盘）+ validate_dir() 验证
- config/settings.json 持久化
- 3.x/4.x 双布局自动检测
- 多账号 list_accounts() 按活跃度排序
- COMPATIBILITY.md 规划

### 7b. 硬编码零容忍检查（每次派单前 / 审查后必跑）

```bash
# 全仓扫硬编码本机值（三个典型值，按项目增删）
grep -rn "wodwend\|wxid_\|4\.1\.0\.34" --include="*.py" core/ tests/ frontend/ 2>/dev/null
```

**零命中 = PASS**。任何命中（哪怕在 `__main__` 自测块）都要移到 `tests/fixtures/` 或改为命令行参数。这是多机通用的红线，不是建议。

### 7c. 假成功检测（产物存在但内容是密文/占位数据）

文档假 ✅ 只是第一层；第二层是**产物存在但内容是原始密文／占位数据的拷贝**。文件数、`pytest` 全绿、`PIL.verify()` 都能通过（源文件本来就没加密时），但「恢复了 N 个」实际 N 个都是改了扩展名的加密原文。

查验方法（审查必跑，顺序不省）：
```bash
# 1. 产物头部是否仍是输入密文的魔数（如 07 08 56 32 = V2 AES+XOR）
xxd output/**/*.bin | head -20
# 2. 产物字节数是否与源文件 100% 相等（说明只是改了扩展名）
stat -c '%s' src.dat output/**/*.bin | sort | uniq -c
# 3. 每个声称成功的文件是否都用真解析器打开过
for f in output/**/*; do file="$f"; case "$file" in *.jpg) python -c "from PIL import Image; Image.open('$file').verify()" ;; esac; done
```

**三档判定**：
- 文档写 ✅ 而实际 False → **REQUEST_CHANGES**，不讨论。
- 声称存在的目录 `exists=False` → REQUEST_CHANGES，要求改成「待实测确认」。
- 只有「真跑过、能贴出命令与输出」才允许写「实测」；否则只能写「官方宣称 / 第三方来源 / 待实测」。做不到写「未能实测」不扣分，编造实测直接打回。
- **产物是原始密文改扩展名** → REQUEST_CHANGES，并要求「失败不落盘、分类统计 decrypted/copied_plain/failed」。

**实战案例（本会话）**：P2 提交声称「154 个文件已恢复」，实测 143 个 `.bin` 头部全是 `07 08 56 32`（V2 魔数），字节数与源 `.dat` 完全一致，仅 11 个 `.jpg` 是源文件本来明文（纯复制）。根因：`_reassemble_fragments()` 只做 `read()` 拼接，**从未调用 DatDecryptor**，`verified` 结果被丢弃。修法：解密失败记入 `failed` 列表，**绝不写文件**，返回 `RecoveryReport(decrypted, copied_plain, failed, duplicate_skipped)` 四段结构。

## 9. 自动化协调：定时任务替你看卡（可选）

把「发现 review 卡 → 本人审 → 决定通过/打回 → 派 ready 卡」交给一个 Hermes cron 任务，`monitor` 门控保证空转时零 token。看门狗脚本示例与门控踩坑见 `watchdog-cron-patterns` 的「Agent 模式 + monitor 门控」一节。**实战实现见 `references/watchdog-implementation.md`**。

任务 prompt 必须自带这五条，否则定时任务会自己编规矩：
1. 审核由协调层本人做，不派 `cc-code-reviewer`。
2. 不采信子员工自述，自己跑命令。
3. 发现假 ✅ 直接 `request-changes`。
4. 绝不把卡留在 `review`。
5. `BUSY=1` 时不派新单（防 429 与双跑）。

建完必须实测一轮：等到下一次 tick，确认 `last_run_at` 有值、目标卡真的从 `ready` 转 `running`、claude 进程数变 1。只有「任务存在」不算建成。


## 10. 看板批量清理：SQLite 直改（CLI 不可用时）

**场景**：`hermes kanban archive`/`delete` CLI 不可用（模块未安装、环境异常），需批量归档 done 任务、删除冗余任务链。

**步骤**：
1. 定位 DB：`D:/Ai/Agent/hermes/kanban/boards/<board>/kanban.db`
2. **先杀掉占用数据库的 Hermes 进程**（gateway/serve 会持有 SQLite 锁）：
```cmd
taskkill /f /im hermes.exe 2>nul
```
3. 删除 WAL/SHM 文件释放锁：
```cmd
del "D:/Ai/Agent/hermes/kanban/boards/<board>/kanban.db-wal" "D:/Ai/Agent/hermes/kanban/boards/<board>/kanban.db-shm" 2>nul
```
4. 查看所有任务：`SELECT id, title, status, assignee FROM tasks;`
5. 批量归档 done 任务：
```python
import sqlite3
DB = r"D:/Ai/Agent/hermes/kanban/boards/<board>/kanban.db"
conn = sqlite3.connect(DB)
done_ids = ["t_1", "t_2", ...]  # 从查询结果收集
for tid in done_ids:
    conn.execute("UPDATE tasks SET status='archived' WHERE id=?", (tid,))
conn.commit()
```
6. 删除冗余/错误任务：`DELETE FROM tasks WHERE id='t_xxx';`
7. 验证：再次 `SELECT` 确认状态变更。

**实战模板（含解锁步骤）**：
```python
import sqlite3, subprocess
DB = r"D:/Ai/Agent/hermes/kanban/boards/xiangmu/kanban.db"
# 1. 杀 Hermes 进程
subprocess.run(["taskkill", "/f", "/im", "hermes.exe"], capture_output=True)
# 2. 删 WAL/SHM
import os
for f in [DB + "-wal", DB + "-shm"]:
    try: os.remove(f)
    except: pass

conn = sqlite3.connect(DB, timeout=10)
cursor = conn.cursor()
keep = {"t_c94b1392", "t_dda59156", "t_d45a1f2c"}
cursor.execute("SELECT id FROM tasks")
for tid in [r[0] for r in cursor.fetchall()]:
    if tid not in keep:
        cursor.execute("DELETE FROM tasks WHERE id=?", (tid,))
        print(f"Deleted: {tid}")
conn.commit()
cursor.execute("SELECT id, title, status, assignee FROM tasks")
for row in cursor.fetchall():
    print(f"  {row}")
conn.close()
```

**实战模板**：
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

