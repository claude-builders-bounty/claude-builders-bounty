---
name: hermes-wf-kanban-orchestration
description: Orchestrate the Hermes+Claude Code kanban workflow.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [kanban, claude-code, orchestration, coordinator, multi-agent]
    category: devops
    related_skills: [claude-code, sdlc-review, feishu-im-alert]
---

# Hermes-wf Kanban Orchestration

Run the user's standing "Hermes + Claude Code 自动化工作流" (install dir basename `hermes-wf`). Hermes is the **coordinator**; Claude Code sub-workers are the **executors**; a kanban board is the **single source of truth**. Applies to every project the user runs through this workflow (one board per project). This is NOT the built-in kanban dispatcher review lane — for that, use `sdlc-review`.

> 项目验收交付后的收尾——归档、清理残留、重置 `WF_BOARD`/`WF_REPO`、暂停哨兵、建新项目根目录——见 `references/project-closeout.md`。新项目第一个动作必须是 `git init` + 首次 commit，否则产出校验永远判零产出。

> 派单前查重、`exit=127` 的真因、僵尸卡对齐（含把卡写成 `done` 也必须清 claim 字段）、建卡参数、审查卡怎么加、运行时契约审查四条（返回值自洽 / 列表真实性 / 错误文案准确 / 证据文件存在）、审查报告轮次命名——见 `references/dispatch-safety.md`。
> Python 项目测试/构建模式（dataclass 配置一致性、临时配置隔离、PyInstaller Windows 打包、热键注册验证、429 串行派单）——见 `references/python-project-patterns.md`。

## 派单与审查硬规则

1. **一卡一 worker。** 派单前必查 `Get-Process -Name claude` 与看板状态两样；两个 worker 写同一 git 树互相覆盖，而产出校验只看 HEAD 变化，覆盖了也判 produced。
2. **`exit=127` 先怀疑自己。** 在 dispatch 父进程存活时杀掉它的 claude 子进程，脚本会报成 `失败(exit=127) → block`。先裸跑一次 `claude --agent <agent> -p "回答两个字：在线"` 确认环境正常，再来判断，别去查 PATH/认证/代理。
3. **必须审查，协调层亲审。** 用户原话「我说你审」：审查是协调层本人的活，不许转派 `cc-code-reviewer`；产出校验只比 HEAD ≠ 通过；审完必须 `complete` 或 `request-changes`，绝不留在 `review`。
4. **不采信自述。** 子员工写「✅ 已验证 / Pillow 通过 / 本地实测」一律不算数；自己跑 `pytest`、文档声称的每条命令、声称存在文件的 `ls`。发现假 ✅ → 直接 `request-changes`。

协调层只做「盯卡 → 依赖解锁就派 → 报结果」；用户问「你干嘛呢」就是在说已经在做多余动作。

## 铁律：协调层不动手（最高优先级）

**协调层（Hermes 本会话）绝不直接改业务代码、不写调试脚本、不手工改交付物源码。**

**「把工作流停了」不是接管授权。** 用户叫停哨兵/杀 worker，是因为不满意当前这条流水线的推进方式，不是把执行权移交给你。停完之后协调层仍然不能自己改代码、不能重新打包、不能「顺手」验证完就交。正确动作是：停 → 如实报当前状态（哪些卡 blocked、成果在哪、哪些改动还没验证）→ 等指令。

判定口诀：**只要用户没明确说「你直接改」，任何代码改动都是派单。** 已自己动手的部分要如实说明是协调层做的，不要混进派单成果里汇报。 任何代码改动 —— 哪怕只是一个字符的 bug fix、加一行日志、写一个 `test_xxx.py` 探针 —— 都必须建卡派给 `cc-*` 子员工，由 worker 改、worker 跑、worker 提交。

Why：用户对「协调层自己修」容忍度为零，即使修对了也算违规，且破坏「看板是唯一事实源」。

协调层允许自己做的只有：读文件定位问题、写卡、派单、跑 `kanban` 查询、看 worker 日志、同步交付包（**仅当 worker 已在源码里改完**）、重打包 exe、把 product/交付物拷到发布目录。

**口头信号（命中即停手建卡，不解释、不先修完再说）**："为什么又自己修了" / "不下发到 Claude Code" / "我让你派个 Claude Code" / "你干嘛呢" / "工作流用来干嘛的" / "把工作流停了吧" / "别自己动手"。

> ⚠️ **本轮实测发现工作流三大结构性缺陷，详见 `references/workflow-defects-fixes.md`**。必须在派单器/验收器里补上对应防线，否则成果必丢、验收必失效。

> 📌 **审查闸门 + 僵尸卡兜底** 见 `references/review-gate-and-stuck-fixer.md`。

## 派单与看板：CLI 事实

停哨兵用 `hermes cron pause <id>`（没有 `disable`）；卡要换 assignee 只能新建一张（`kanban edit` 无此选项）；派单 prompt 里禁止反引号和 `$`，否则被 shell 展开、worker 收到残缺任务。429 是通道限流不是代码问题，先探测通道再派。

> 完整表格、模型别名改写机制、以及「用户叫停时到底停哪些东西」的清单，见 `references/coordinator-cli-and-scope.md`。

## 收尾三段：commit → review → done，缺一段等于白干

1. **worker 必须 `git commit`。** 只改工作区不提交 = 零产出。产出校验器比的是 git 快照，未提交的改动会被判「零产出」→ 卡 block，成果躺在工作区随时被下一次覆盖。卡正文里显式写「必须 `git commit`，message 写清根因」。
2. **有产出 → review，不是 done。** 直连 done 会跳过 `cc-code-reviewer`，等于没有质量闸。顺序：worker 提交 → 审核卡 / `kanban_request_review` → 审核通过才 done。
3. **429 撞在收尾时只重放 kanban 调用，不重跑 worker。** worker 已干完活，重跑会覆盖工作区。

诊断口诀：**卡变 blocked 但 worker 日志里有完整交付总结 = 收尾环节挂了，不是 worker 挂了。** 先 `cat logs/workers/<task_id>.out`，看有没有产出总结，再决定是重派还是只补收尾。

## When to Use

触发条件（命中任一即加载本技能）：

- 搭 / 改 / 体检 `hermes-wf` 工作流：安装目录、`config.env`、角色阵容、`dispatch_claude.sh`
- 向看板发卡、扩权改卡、回填正文、调优先级、接父子依赖
- 排查「卡不动了 / worker 假死 / 零产出 / 进 `triage` / 一直 ready / 被 block 后无反应」
- 回答「某个环节真的在工作吗 / 是直连完成还是过了审查 / 这道闸拦过东西吗」—— 走 `references/board-forensics.md`
- 给这个工作流加告警、巡检、无人值守自愈、故障注入验收
- 需要「真点窗口」的验收（桌面 GUI 端到端）—— 见下方「GUI 验收要单独派」

## GUI 验收要单独派

**`cc-frontend-developer` 不会点界面。** 它写代码 + 跑 `pytest`，从不启动窗口、不点按钮、不看渲染结果；同理 `cc-e2e-runner` 跑的是接口层集成测试。所以「选完目录界面还是空的」这类卡派给它们，拿回的永远是「单元测试通过」—— 而 bug 就在单元测试盖不到的那一层。

需要真实 GUI 交互时，卡必须指定一个带桌面自动化权限的 agent（角色名 `cc-gui-tester`，`--allowedTools` 要额外含 `computer_use`；`dispatch_claude.sh` 已按 agent 名自动注入这个旗标，新增类似 agent 时照抄那段 `case`）。卡正文要写明「必须真启动 exe、真点控件、失败必须附截图 + 完整日志」，否则 worker 依然会用模拟测试交差。

不适用：Hermes 内置派单器的 review 车道（用 `sdlc-review`）、与 kanban 无关的 Claude Code 配置（用 `configure-ccswitch-claude-code`）。

**Authoritative source:** the user's migration manual `Hermes自动化工作流迁移手册-v2.0.md` (on their Desktop under `hermes+claude code自动化工作流/`). Its Appendix A holds the full `install.sh`; Appendix B the config key table; Chapter 6 the reliability guards; Chapter 7 the coordinator's acceptance discipline; Chapter 9 the troubleshooting table. Read it before improvising — v1.0 of that manual is superseded and following it re-creates already-fixed bugs. 同目录还有 `Hermes看板机制说明书.md`（看板状态机）、`agents-and-commands.md`（执行层角色与 slash 命令体系）、`development-workflow.md`（执行层内部的 `planner` / `tdd-guide` / `code-reviewer` 工序）。**角色归属有争议时读这几份再回答**，不要凭印象分层 —— 用户会拿原版文档对质。

## Role discipline (five iron laws)

| # | Law | Why |
|---|---|---|
| 1 | The executor must be an **external coding agent** (`claude --agent <name>`); the coordinator does **not** write business code | writer and verifier must not be the same actor, or nothing is verified |
| 2 | The **kanban board is the only task source**; one card = one deliverable | verbal tasks get lost; multi-deliverable cards cannot be judged complete |
| 3 | Dispatching must **sync board state** (`claim → running → done/blocked`) | state that disagrees with reality → the card is dispatched twice → two workers double-write the same tree |
| 4 | **Zero output ≠ done** | exit code 0 with no commit is a *fake done*; the work sat in the tree and gets overwritten |
| 5 | **Never trust self-reports**; the coordinator re-verifies independently | "done" is the worker's claim, not a fact |
| 6 | **GUI launch + interaction must pass** before a card is accepted | unit/E2E tests bypass the UI layer; FilePicker, lambda closures, async handlers only fail on real window |
| 7 | **Code review must cover frontend/** | engine-only review misses 31 lambda NameErrors, FilePicker registration bugs, async/await omissions |

### 验收是协调者自己的动作，不是看板上的一个状态

原版对角色只有一句权威定义：**Hermes = 协调者（拆卡 → 建卡 → 派单 → 验收 → 汇报），
Claude Code 子员工 = 执行者，看板 = 唯一任务源与状态真相。** 协调层明写「不亲自写业务代码
（否则没有第二双眼睛）」。

## 铁律（用户反复强调，必须内化为派单前自检）

1. **Verification First（验证优先）**：任何涉及「有没有这个功能/参数/版本/命令/文件/路径/API/配置/版本号/CLI 参数/文档说法/官方行为」的问题或任务，**先去权威源拿地面真相**（`--help` / manifest / 官方文档 / 实测），**验证通过才许给方案**。违者即停。
2. **真实测试优先，禁止模拟替代**：GUI 测试、FilePicker 路径、exe 打包验收，**必须真跑 exe、真点控件、真输中文路径、真看结果**。模拟测试（直接调函数、pyautogui 坐标、单元测试替代端到端）不被接受。
3. **不接受挂起等人工**：任何卡卡住时，要么自动重试，要么直接打回重做——**不允许既不过也不打回地停在中间状态**。打回时必须写清具体原因和改法让执行方照着改，且有上限（反复不过归档退出循环），不能无限重打把资源耗光。
4. **全量环境配置一次到位**："把所有的agent的环境，环境变量，该配置的，改给的权限，能给的都给一下。别再出这问题了" —— 发现一类权限/配置缺口时，主动把同类 agent/组件全量审计并一次修完（含自动预检与救护脚本），只修当前报错那一个会被追问。
5. **清单是起点，不是范围上限**：任务卡/子任务/定时任务说明必须：主任务写完整范围并占据主体，已知项清单显式标注为「起点，不是范围上限」，并写明禁止「只做完清单上的 N 条就交差」。

**审查不在看板状态里。** 原版看板只有 `ready/running/done/blocked`，没有 `review` ——
这是设计如此，不是缺功能。手册 §6.3 原话：**「它只负责派。验收不在它里面 —— 完成后由
协调者负责 git 核验与回归。」** 所以「看板上没走 review」本身不说明链路坏了；那一段本来就
该是**协调者的手工作业**，它没被自动化过。

### GUI 冒烟与交互验收（铁律 6、7 的落地）

每张涉及 UI 的卡（界面、打包、交付）的验收**必须**包含：

1. **GUI 冒烟**：`python main.py` 真起窗口 → 等 5 秒 → 查进程存活 → 查窗口标题正确
2. **交互验收**：用 `pyautogui` / `pytest-qt` / `flet.testing` / **`computer_use` (CUA)** 真点按钮、改滑块、选目录、验不报错
3. **覆盖点**：FilePicker 选源/输出、所有滑块 on_change、所有开关、开始/取消按钮

代码审查卡的 body **必须**写明：逐文件过 `frontend/`、所有 lambda 闭包变量、所有导入可见性、所有控件注册位置、所有 async/await。

**不接受** "engine.py 无问题" 作为通过理由。

> ⚠️ **本技能文档已列出上述要求，但本轮实测发现：验收模板虽在，却未被真正执行**。GUI 冒烟与交互测试只是写在文档里，协调者未真跑。导致 FilePicker async/await、lambda 闭包 NameError、目录扫描不递归等阻断级 bug 全漏。
> **修正**：验收清单必须在协调者手中真跑一遍并附证据（进程截图、交互视频/日志），不接受 "文档里有" 作为完成标志。

### GUI 自动化测试专用 Agent：`cc-gui-tester` + `computer_use` (CUA)

**新模式（2026-10-22 落地）**：不再用 pyautogui/pytest-qt 模拟测试，**必须用真实桌面交互**。

- 创建专用 agent：`cc-gui-tester`，在 `tools:` 中声明 `computer_use`
- `WF_AGENT_DIRS` 映射 `cc-gui-tester=tests/`（GUI 测试脚本目录）
- `dispatch_claude.sh` 自动识别 `cc-gui-tester` 并在 `--allowedTools` 中注入 `computer_use`
- `config.env` 追加 `cc-gui-tester=tests` 目录映射
- Agent 预检 `agent_preflight.py` 需计入该 agent（agent 数量检查 30→31）

**测试卡正文模板**（注入 `cc-gui-tester` 的卡必须含）：
```
## 目标（要做什么）
真实 exe + SOM 元素定位 + FilePicker 完整交互 + 视觉验证

## 执行步骤
1. capture mode=som app="ImgBatchTool" 取元素索引
2. click element=<源目录按钮索引> → capture_after=True 验 FilePicker 弹出
3. type 源目录路径（含中文）→ key="return" 确认
4. click element=<开始按钮索引> → 等处理完成
5. capture mode=vision 验证结果文件存在、数量正确

## 验收判据
- SOM 捕获成功、元素索引有效
- FilePicker 真弹出、中文路径真选中、处理真跑完
- 视觉验证：结果目录文件数 = 预期数（如 29 个）
- 失败留证据：capture 截图 + 元素索引 + 异常堆栈

## 禁区
- 禁止用 pyautogui/pytest-qt 模拟替代真实交互
- 禁止只跑单测/E2E 绕过 UI 层
- 完成即送审，不自行标记 done
```

**关键差异**：pyautogui 是像素级模拟，**不走系统无障碍树**，FilePicker、原生对话框、Electron/Chromium 画布全打不中。`computer_use` 走 CUA 驱动，**背景输入 + SOM/Vision/AX 三模态**，不抢焦点、不切桌面、能驱动原生控件。

> **验收铁律**：GUI 卡若未走 `computer_use` 真实交互，协调者**直接判 MANUAL 留 review**，不接受模拟测试报告。

两个循环，别混：

| 循环 | 节拍 | 谁 | 干什么 |
|---|---|---|---|
| 快速 | 分钟级，自动 | 哨兵 | 读 `ready` 补并发 → 派单 → produce-check 收尾 |
| **慢速** | **人工 / 协调者** | **Hermes** | **看 `done`、`blocked` 卡 → 验收 → 补卡 → 调优先级** |

协调者验收三步（手册 §七，每张 `done` 卡都做，别跳）：

1. `git log --all --oneline --grep="<卡号>"` + `git show --stat HEAD` —— 真的 commit 了吗
2. `git show --name-only <sha>` —— 有没有越出卡面允许的文件域
3. 写**自己的**脚本重跑关键判据 —— 不采信 worker 自报的数字

外加 §7.4 一条总纲：**未回写 = 未测试**。

**两层审查，只做一层等于没做。** 执行层内部还有 Claude Code 的 `code-reviewer` agent
（`development-workflow.md`：编码后自调、处理 CRITICAL/HIGH），那是 worker 自己的工序；
协调层的 git 核验 + 对照实验是**独立于它**的第二双眼睛。

**最贵的失效形态：把验收时间花在修管道上。** 管道全绿 + 一批 `done` + 一张都没验过，
是这套流程最容易滑进去的状态 —— 修基础设施的即时反馈远强于验收，于是协调者退化成电工，
用户会直接指出来（「所有问题都在 Hermes 解决了」「审查角色应该是 Hermes 吧」）。
自查只要两个数：**多少 `done` 卡真过过验收**、**多少 `done` 卡的 worker 自述过「验收命令未执行」**。
`scripts/acceptance_audit.py` 一次出这两张表，跑它比回忆靠谱。

## Install a new project

1. **Make the repo a git repo and COMMIT THE SCAFFOLD before the first dispatch** (`git init`, set user identity, build the directory layout, `git add -A && git commit`). The produce-check fingerprint is `md5(sorted(git status --porcelain))`, and porcelain **collapses a wholly-untracked directory to a single `?? dir/` line** — so every write *inside* it leaves the fingerprint unchanged and the guard reports `verdict=EMPTY 零产出` for work that was really done, blocking the card into `triage`. Committing the scaffold makes nested writes show as ` M ` and restores the guard.
2. Add `.gitignore` with `.worktrees/` **and** credential paths. `.worktrees/` is never ignored by default; one `git add -A` commits an entire repo copy.
3. Extract `install.sh` from the manual's Appendix A if you don't already have the file: slice the first bash block after the heading `附录 A` up to `## 附录 B`. Verify `bash -n` passes and the line count matches the manual's stated count.
4. Install with an **isolated dir**: `bash install.sh --board <board> --repo <repo-path> --dir <hermes_home>/scripts/hermes-wf-<board>`.
   - `--repo` must be a forward-slash native path (`D:/x/y`) — git-bash `/d/x` and backslash forms break native tools.
   - `--dir` must live **under** `<hermes_home>/scripts/` — the cron job stores `--script` relative to that directory.
5. Verify: `hermes kanban boards list` shows the board, `hermes cron list --all` shows the sentinel job, and `logs/tick.log` gains a `tick rc=0` line within a minute.
6. **Diff what you asked for against what `config.env` actually holds, before reporting success.** The preserve-on-exists behaviour keeps EVERY old key, while the install banner still echoes your new `--repo`/`--board`. Read the effective values back:
   ```bash
   grep -vE '^\s*#|^\s*$' <dir>/config.env
   ```
   Compare `WF_REPO` + `WF_AGENT_DIRS` against the repo you passed. A stale `WF_REPO` is silent — the sentinel dispatches perfectly, just into the wrong tree. Also confirm `WF_PYTHON` is an absolute path that actually runs (`"$(...)" -c "import sys"`), not a `python3` stub.
7. **Count the agents matching `WF_AGENT_PREFIX` in the EFFECTIVE config dir — never in `~/.claude/`.** Zero matches is the quietest failure in this whole workflow: every tick exits `rc=0`, `dispatch.log` stays empty, cards sit in `ready` forever, and nothing anywhere reports an error. Resolve the dir first (`[Environment]::GetEnvironmentVariable('CLAUDE_CONFIG_DIR','User')`), then count `cc-*` there. Report **the number**, not "agents exist".
   An install is not finished until all of 5–7 pass. Steps 5 alone wins you a running sentinel that can never dispatch anything.

### Isolated dir vs reconfigure in place — the decisive rule

`install.sh` **preserves an existing `config.env`** when the target dir already exists. Consequences:

- Running it again with a new `--board` against the **same dir** silently keeps the old board. The new cron job is created but reads the old `config.env` → **two sentinel jobs now read the same board → 抢单 (double dispatch)**.
- To change the board in place you MUST use `--force` (resets `config.env`) **and** remove the previous sentinel cron job. Skipping either leaves a stale job that re-reads the new config and double-dispatches.
- To run a **second project**, prefer an **independent `--dir`** → its own `config.env` and own cron job. Two sentinels on **different** boards do not compete; two on the **same** board do.

When the user says keep only one sentinel, remove the other explicitly: `hermes cron remove <job-id>` (ids come from `hermes cron list --all`).

## Configure `config.env`

Full key table in `references/install-and-config.md`. The keys that bite:

- **`WF_AGENT_DIRS`** (`agent=subdir,...`) pins each sub-worker to a disjoint subdirectory — the first line of defence against parallel overwrite. **Must reference agent names that actually exist.** Leaving it empty makes every worker operate at the repo root and collide. It cannot be finalized before the repo layout and the agent roster exist. Give each role a disjoint **output and resource path too**, not just a code dir: the natural layout shares `output/analysis/`, `output/selection/`, `resources/templates/` across several roles, and two workers will write the same files unless you split them per role (`output/analysis/<role>/`, `resources/templates/<role>/`).
  **Every mapped subdirectory must exist before the first dispatch.** The dispatcher joins `WF_REPO/<subdir>`, and `dispatch_claude.sh` does `cd "$PROJECT_DIR"` → `exit 2` when the dir is missing (the card ends `blocked`, not with a path error). Creating a role dir also needs a `.gitkeep`: git does not track empty directories, so `git add -A` silently skips it and the git-based produce-check then sees an untracked tree. Role dirs with no natural home in the repo (ops / design / tests) must be created deliberately — leaving them out drops every one of those workers back to the repo root, which is the overwrite case this key exists to prevent.
- **`WF_AGENT_PREFIX`** (`cc-`) is the anti-grab mechanism: only cards whose `assignee` starts with it are dispatched, so the built-in gateway dispatcher never touches them. **Setting it to `""` does NOT disable the filter.** `wf_common.env()` is `os.environ.get(k) or cfg.get(k) or default`, and an empty string is falsy, so it silently falls back to `cc-` — the roles then match nothing, every tick stays `rc=0`, and nothing reports an error. Do not "turn the prefix off" to fit bare role names: even if it took effect, `assignee.startswith("")` is always true, so every `default`-assigned card would be dispatched to a non-existent `claude --agent default` and blocked. The roster must therefore share a real common prefix: copy every original agent to `<prefix><original-name>` (e.g. `backend-developer.md` → `cc-backend-developer.md`, changing only the frontmatter `name:`) and key `WF_AGENT_DIRS` by those full prefixed names, not by the bare role word. Do not invent a smaller hand-written roster when a complete one already exists — the user keeps a full set of domain agents and expects them all enabled, not a 5-role reimplementation (they will say so bluntly).
- **`WF_CLAUDE_ARGS`** must be **comma-separated** in `--allowedTools`. Space-separated is silently ineffective → the worker's first `Bash` hits the permission wall → silent no-op → exit 0 (fake done).
- **`WF_MAX_OUTPUT_TOKENS=32000`** — do not drop it; Claude Code's default 2048 truncates long reports and crashes the worker.
- **`WF_MAX_PER_AGENT=1`** — one card per agent at a time, so a single role never edits the same file batch concurrently.
- **`WF_VERIFY_KEYWORDS`** — a card whose **title** matches these (验收/巡检/复核/盘点/闭环/演练/审计/只读/排查/对照实验) legitimately produces no commit. Fix cards must use 修/修复/新增/实现 in the title instead, or their zero-output gets waved through.

### 改脚本默认值没生效？先看 `config.env` 有没有无条件赋值

`dispatch_claude.sh` 顶部 `source config.env`，而 `config.env` 里的 `KEY=value` 是**无条件赋值** ——
它同时盖掉两样东西：脚本里的 `${KEY:-默认值}`，以及调用方 `export` 进来的同名变量。
症状是「补丁明明写在脚本里，运行时却看不到」。

所以两条必须记住：

- **改默认值要同时改 `config.env` 那一行**，否则脚本里的新默认值永远轮不到生效。
- **想换测试替身（`WF_CLAUDE=fake`）做隔离实验，用环境变量是无效的** —— 必须临时改 `config.env`
  （或把该行改成 `${KEY:-...}`）再还原。否则你以为在测替身，实际跑的是真二进制，结论全错。

判定方法：派单前把实际生效值打一行日志（`echo "WF_CLAUDE=$WF_CLAUDE ARGS=$WF_CLAUDE_ARGS"`），
**看日志里的值，不要看脚本源码里的默认值**。

## Agents (executors)

- Claude Code reads sub-agent definitions from `$CLAUDE_CONFIG_DIR/agents/*.md`. On this machine `CLAUDE_CONFIG_DIR=D:\Ai\claude code`, so the live agents dir is `D:\Ai\claude code\agents\`.
- **`claude agents` / `claude agents --json` is the background-SESSION manager, not a roster listing.** It prints running/completed agent sessions and returns `[]` whenever none are running — reading that `[]` as "the new role was not registered" is a false negative that sends you rewriting good files. Enumerate the real roster with a deliberately bad name: `claude --agent __nonexistent__ -p hi` exits after echoing `--agent '__nonexistent__' not found. Available agents: …` (built-ins `claude` / `Explore` / `Plan` / `general-purpose` / `statusline-setup` are always in that list).
- **Prove which agents dir is live; do not assume it.** Write a uniquely named probe agent (`name:` equal to the filename) into exactly ONE candidate dir, run the bad-name enumeration, then delete the probe. Present → that dir is the loaded one; absent → it is not. This is the only reliable way to settle `$CLAUDE_CONFIG_DIR/agents` vs `~/.claude/agents` when both hold identical copies.
- **盘点角色阵容必须在生效目录里数，不要在 `~/.claude/` 里数。** 本机两份 `rules/` + `agents/` 同时存在（`$CLAUDE_CONFIG_DIR/` 与 `~/.claude/`），**只有前者被加载**。实测在 `~/.claude/agents/` 里数出 `cc-* = 0 个`，据此报告「角色文件缺失」——实际 10 个全在生效目录里，当场被自己的下一条证据推翻。先读
  `powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('CLAUDE_CONFIG_DIR','User')"` 确认指向，再列目录；两份内容可能全等，但**只有生效目录缺文件才是异常**。
- **`tools:` 是硬闸门 —— 命令行 `--allowedTools` 授不出 agent 没声明的工具。** 派「要产出文件」的卡之前，
  先读该角色的 frontmatter：`grep '^tools:' <config>/agents/<name>.md`，**必须含 `Write`（要改代码的还要 `Edit`）**。
  只读型角色（`architect` / `code-reviewer` 这类）常写成 `["Read","Grep","Glob"]`，此时 worker 会把整篇文档
  **当聊天回答输出到 stdout**、一个字节都不落盘 → produce-check 判 `EMPTY` → 卡进 `triage`；
  而 worker 日志里内容完整，极易误判成「模型不听话」或「任务描述不清」。
  修法是**直接改 frontmatter 的 `tools:` 数组**（生效目录与备份目录两边同步），不是在派单脚本里加旗标
  —— 加了也不会生效。派完先用一条最小写文件探针验证（`Write` 一个 2 字节文件 → `ls` 确认存在）再放开跑。

  **修完 `tools:` 还不够 —— agent 正文明写「只读」会让模型自我审查、照样不写文件。**
  只读型角色的完成须知常写「**只读**：只报告，不改文件」，模型读到就把整篇产出当聊天回复吐出，
  权限明明已经给了也不用。**闸门有两道：frontmatter 的 `tools:` 决定「能不能」，正文措辞决定「肯不肯」。**
  修法是在每个 agent 正文顶部注入一段**声明优先级高于后文任何「只读」措辞**的落盘规则：点名了路径就必须
  `Write` 落盘、只输出在对话里算没完成、写完用 `Bash` 自检存在性。批量治理不要逐个手改 ——
  写一个规范化脚本遍历全部 `cc-*.md`（补 `tools` + 幂等注入规则块 + 两个目录同步），并配一个
  **预检脚本**（agent 数量 / frontmatter 可解析 / 每个都含 `Write` / 规则块在 / 备份区同名 / 映射目录存在），
  以后每次改动 agent 或重装都先跑预检再派单。可复用实现见 `scripts/agent_preflight.py`。
- A card's `assignee` must equal `<WF_AGENT_PREFIX><agent-name>` for an agent file that **actually exists**. Check the roster before creating cards; create missing role files first.
- Create a role by **mirroring an existing generic agent file field-for-field** (same `name`/`description`/`tools`/`model` frontmatter shape) and matching `name` to the filename. A role whose frontmatter differs in shape is silently skipped — it does not error, it just never appears in `--agent` resolution.
- Validate the whole roster with the install's own `scripts/agent-health.sh`: it prints the effective config dir, the agent count, and name/filename consistency, so it separates "this file is malformed" from "the other config dir isn't the one being loaded".
- Generic developer/reviewer roles may already exist; domain-specific roles (business functions) usually do not.
- **Claude Code 侧和 Hermes 侧的东西不要混。** `coding-style.md` / `development-workflow.md` / `git-workflow.md` / `agents-and-commands.md` 是 **Claude Code 的规则**（放 `$CLAUDE_CONFIG_DIR/rules/`，由 `CLAUDE.md` 引用），不是 Hermes 的配置；Hermes 侧只实现迁移手册。用户会直接纠正把两边混为一谈的说法 —— 搭建前先分清哪份文件服务哪一层。
- **Claude Code 2.1.300 支持 `AGENTS.md`**（发现顺序含 `AGENTS.md` 与 `.claude/AGENTS.md`），但设置项 `instructionFiles` 默认是 `claude-md-or-agents-md`：**项目自己没有 `CLAUDE.md` 时才加载 `AGENTS.md`**；要让它与 CLAUDE.md 并存需设为 `claude-md-and-agents-md`。确定给项目铺哪个规则文件之前先确认这个设置，否则写了 `AGENTS.md` 也不会生效。
- `D:\Ai\claude code\skills\` **为空是正常的** —— superpowers 插件自带 15 个 skill，不经这个目录。别把「skills 目录是空的」当成待修的缺失。

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

> **模型链路与 cc-switch 代理完整配置（改写机制、验证脚本、NIM 测试、WF_CLAUDE_MODEL 策略、obsidian MCP 选型）——见 `references/model-channel-and-ccswitch.md`。**

### `triage` 是死状态 —— 没有 CLI 出口，只能防不能救

卡片掉进 `triage`（例：`card_produce_check` 判 EMPTY）后，**所有 CLI 出口都不可用**（已穷尽实测）：

| 命令 | 结果 |
|---|---|
| `promote` | 只吃 `todo`/`blocked` |
| `unblock` | 只吃 `blocked`/`scheduled` |
| `block` | **拒绝 triage**（`cannot block`）|
| `schedule` | `cannot schedule` |
| `complete` | `unknown id or terminal state` |
| `edit` | 无 `--status`（改不了状态），**但它能改活跃卡的 `--title/--body/--priority`** —— 回填卡片正文靠的就是它 |
| `repair` | 仅数据库完整性检查，**不改任务状态** |
| `specify` | 唯一设计上的出口，但常挂 `LLM error: PermissionDeniedError` |

**所以：协调者的首要任务是别让卡掉进 triage**（修 `card_produce_check` 的指纹根因、脚手架必须先入库），而不是想着事后捞。

**轻量恢复：`triage` → `ready`（只想重跑，不想伪造 done）。** 改库有两条重量级完全不同的路径，别混：

| 目标 | 要改的表 | 风险 |
|---|---|---|
| `triage` → `ready`（重派） | `tasks.status` + 一条 `task_events` | 低 —— 不伪造完成，只是把卡放回队列 |
| 任意 → `done` | `tasks`/`task_runs`/`task_events` + 时间戳四处镜像 | 高 —— 等于声明交付物已验收 |

前者实测有效且足够：备份 `kanban.db` → `update tasks set status='ready' where id=? and status='triage'`
→ 同事务补一条 `kind='status'` 的事件行说明原因 → 哨兵下一 tick 自动重派。**事件行不能省**，
否则审计链断裂（详见 Pitfalls「直接 UPDATE tasks 会断审计链」）。改完用 `show <id>` 读回
`status: ready`，不要看 SQL 的 `commit()` 返回值。可复用实现见 `scripts/kanban_rescue.py`
（同时处理僵尸 `running` 与父卡已归档的孤儿卡）。

真的需要正名到 `done` 时，唯一的路径是**直接写 `kanban.db`**（属高危改动，**必须先取得用户明确授权**），且必须照一张已有的 DONE 卡 **1:1 镜像**、不要自己发明字段值——DONE 卡在四处留下痕迹，只改 `tasks.status` 会留下内部状态不一致的暗坑：

1. `tasks` —— `status='done'`、`completed_at`、`result`、`consecutive_failures=0`
2. `task_runs` 最新一行 —— `status='done'`、`ended_at`、`outcome='completed'`、`summary`
3. `task_events` —— 新增一条 `kind='completed'`（带 `run_id`）
4. 时间戳统一用 Unix epoch 秒

事后必做两件事：`cp kanban.db kanban.db.bak-before-<事由>-<时间戳>`（**先**备份）和 `hermes kanban --board <slug> repair`（应输出 `integrity_check ok — no repair needed`）。

### 测 NIM 上的模型：必须用真实模型名，绝不用 Claude Code 的别名

NVIDIA NIM 上**没有 `claude-*` 模型**（那是 Anthropic 的模型名）。用 `claude --model opus|sonnet|haiku` 去探 NIM，参数会被解析成别名（如 `claude-opus-5[1M]`），上游必然不认识 —— 报「selected model 可能不存在或无权访问」或 404。**这种测试无效，不能据此判定某个真实模型不可用。**

正确做法：先用 `GET /v1/models` 查出 NIM 目录里的**真实模型名**（如 `deepseek-ai/deepseek-v4.1-flash`、`nvidia/nemotron-3-ultra-550b-a55b`），再用 `claude --model <真实模型名>` 直测；或直接绕开 Claude Code 调 `POST /v1/chat/completions`（OpenAI 格式 + `stream: true`）。

**豁免**：只有当别名在 cc-switch 的映射表里**命中**时（`ANTHROPIC_DEFAULT_<T>_MODEL` 的别名 ↔ 同名 `_MODEL_NAME` 的真实模型），别名才等价于真实模型，`proxy_request_logs.model` 列会显示真实模型名。查那一列就能确认映射到底有没有生效。

### obsidian MCP：选对版本，并先建 `.obsidian`

npm 上有两个同名易混的包，**只有一个是本地文件系统版**：

| 包 | 机制 | 适用 |
|---|---|---|
| `mcp-obsidian` | 要 Obsidian **开着** + Local REST API 插件 | 不适用（应用没装就跑不起来） |
| **`obsidian-mcp`**（v2.x）| **本地文件系统版**，直接读写 Markdown | ✅ 推荐；README 明写「Obsidian does not need to be open」|

正确调用：`obsidian-mcp serve --vault <id>=<绝对路径>`（需 **Node 22+**）。

**必踩的坑**：`obsidian-mcp doctor` 会报 `VAULT_NOT_INITIALIZED` —— 它要求库目录里存在 `.obsidian` 目录（该目录平时由 Obsidian 首次打开库时创建）。它只检查**存在性**，所以手写一个最小合法的 `.obsidian/app.json` 即可，无需安装 Obsidian 应用。

流程：先 `doctor` 拿到 `{"ok": true, "readable": true, "writable": true}` **再**注册；注册用官方 CLI（`claude mcp add <name> -s user -- <bin> serve --vault <id>=<path>`），不要手改 JSON；最后 `claude mcp list` 确认真的是 `✔ Connected`（能启动 ≠ 已连上）。

> 注意区分「MCP 能用」与「Obsidian 应用装了」：文件系统版 MCP 不需要应用，但要 GUI 浏览库仍需自行安装 Obsidian 并「打开文件夹作为库」——报告时要讲清楚这个区别。

`dispatch_claude.sh` 里 `MODEL_ARGS` 由 `config.env` 的 `WF_CLAUDE_MODEL` 驱动，但**模型唯一真相是 cc-switch，不是这个键**。

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

`ANTHROPIC_BASE_URL` 指向 `http://127.0.0.1:15721`（cc-switch 内嵌代理），而 **NVIDIA 只支持 OpenAI 格式（`POST /v1/messages` → 404），必须靠这个代理做 Anthropic↔OpenAI 转换**。所以：

- **cc-switch 一停，Claude Code 就完全不可用**（症状：调用挂死到 `REAL_EXIT=124`，输出全空；`netstat | grep 15721` 什么都没有）。
- cc-switch 没有 CLI，**执行 `cc-switch.exe` 就是启动它的 GUI + 代理**；它启动时会自动 attach 当前渠道并**重写 `settings.json`**。
- **它每次 attach 都会把我的手工改动覆盖回别名**（`ANTHROPIC_DEFAULT_SONNET_MODEL` 写回 `claude-sonnet-5[1M]`，真实模型名放在同名的 `_MODEL_NAME` 键里）。所以**不要手改 `settings.json` 的模型名**——那是 cc-switch 的辖地，改了也会被冲掉；要改就改 cc-switch 的 provider 配置（`cc-switch.db` 的 `providers.settings_config`），并在 app 停止时改（在跑时改会被回写覆盖）。
- **`WF_CLAUDE_MODEL` 不是最终真相 —— 代理会改写它。** cc-switch 会把客户端请求的**任何**模型改写成当前 provider 的主档位 `ANTHROPIC_MODEL`。所以「`config.env` 填了 X、`proxy_request_logs` 里 `used` 是 Y」= provider 主档位不是 X，**不是** `--model` 没传。
  五个档位要一起改：`ANTHROPIC_MODEL` 之外还有 `ANTHROPIC_DEFAULT_SONNET/OPUS/HAIKU/FABLE_MODEL` —— 只改主档位时，Claude Code 的子任务/降级调用仍跑旧模型，表现为「有时 X 有时 Y」，很难查。
  改完 `cc-switch.db` 也要重启 app 或改走界面（运行中的 GUI 不重读 DB）；**在 worker 跑着时不要重启**，重启会断代理、在跑的卡全废。判定脚本与证据取法见 `configure-ccswitch-claude-code` 的「我指定了模型，实际却跑另一个模型」。

## Dispatch and verify

### Card CLI syntax — the flag names are NOT what you expect

| Intent | Correct form | Rejected |
|---|---|---|
| Create | `hermes kanban --board <b> create "<title>" --assignee <a> --body-file <path>` | `--title` ❌ (`unrecognized arguments`), `--body` ❌ |
| Create (chained) | `… create "<title>" --assignee <a> --priority <N> --parent <upstream-id> --body-file <path>` | `--parents` ❌ |
| List / Show | `hermes kanban --board <b> list` / `show <id>` | — |
| Comment | `hermes kanban --board <b> comment <task_id> "<text>"` | `--body` ❌ |
| Block | `hermes kanban --board <b> block <id> "<reason>"` | `--reason` ❌ |
| Complete | `hermes kanban --board <b> complete <id> --summary "<text>"` | — |
| Unblock | `hermes kanban --board <b> unblock <id>` | — |
| Reclaim（僵死 running 卡）| `hermes kanban --board <b> reclaim <id> --reason "<原因>"` | 手工改库 ❌（`reclaim` 就是干这个的）|

- **The title is the positional argument; the body is a flag.** Both `--title` and `--body` draw `unrecognized arguments`, so a create command written from memory silently does nothing.
- **Pass multi-line bodies as `--body-file <file>`, never inline.** `--body "..."` is rejected outright; and a heredoc (`--body-file -`) still routes the body **through bash**, so any embedded double quote ends the string early — a body containing `"微信"` dies with `unexpected EOF while looking for matching ')'` and **no card is created at all**. Build the body in Python and write it to a temp file, then pass `--body-file <path>`: that survives quotes, newlines, CJK and full-width punctuation intact, and keeps the body recreatable after an `archive`. 串行建卡 + 父子依赖 + 优先级的可复制模式见下文「铺开角色阵容」。
  **`--body-file` 只能给原生正斜杠绝对路径**（`D:/x/cards/c1.md`）：MSYS 的 `/d/x/...` 会被拼成
  `'\d\Ai\...'` 并报 `kanban: --body-file: [Errno 2] No such file or directory`，**卡建不出来**（不是建成了空卡）。
  从卡号提取也一样：`create` 的普通输出里 `grep -o 't_[0-9a-f]\+'` 最稳，别依赖 `--json` 管道给 python 解析
  —— 上游一旦报错，管道拿到空串，`json.load` 抛 `Expecting value: line 1 column 1`，真正的建卡错误被这层噪声盖住。
- **`comment` takes `task_id` and `text` as positionals.**
- **`unblock` is enough to resume work** — it promotes `blocked` → `ready` (or parent-gated `todo`), and the sentinel auto-dispatches it on its next tick with no further action. Verify with `list` rather than dispatching by hand, or you race the sentinel and double-dispatch.
- When a card was blocked on a precondition you have just fixed, **comment the resolution on the card before unblocking** — the worker reads the card thread, and a bare unblock re-runs the worker against the same stale reasoning that blocked it.

- Create cards with `--body-file <path>` — multi-line bodies survive verbatim, and keeping the body in a file makes the card recreatable in one command after a `triage` dead-end. `--json` prints the new id.
- `hermes kanban block` takes the reason as a **positional** argument (`block <id> "<reason>"`); `--reason` is not accepted.
- Manual dispatch: `bash <dir>/dispatch_claude.sh <card> <agent> "<prompt>" <repo> <board>`.
- One sentinel round: `python <dir>/kanban_auto_dispatch.py --once`; preview with `--dry-run`.
- **Always pass an explicit `--board`** on every kanban command — there is a global "current board" pointer that drifts when you work in other projects, and a bare command will claim a card on the wrong board.
- **Never pass `--project` when creating a card.** It anchors the task to a git worktree + detached branch: the board shows `done` while the commit never reaches mainline, with no error. This workflow computes the work dir from `WF_AGENT_DIRS`, not from the board's workspace field.
- Verify a completion yourself before believing it:
  1. `git log --all --oneline --grep="<card-id>"` and `git show --stat HEAD` — did it actually commit?
  2. `git show --name-only <sha>` — did it stay inside the card's allowed file domain?
  3. Re-run the key acceptance check with your **own** script; do not reuse the worker's numbers.

## 收到一个需求：先拆成卡 DAG，再建第一张卡

**用户给的是「一个产品 / 一个功能」，不是「一个任务」。** 协调者的第一个动作永远是拆卡，
不是把整段需求原样建成一张卡派给一个子员工。违反这一条会被当场纠正（用户原话：
「我三十个agent，你不拆分下任务就整个派出去了？」）—— 而且单卡多交付物本身就无法判完成（铁律 2）。

拆卡口径（**按角色分工切，不按功能清单切**）：

1. **一卡 = 一个交付物 + 一个负责人 + 一个目录**：规格 / 引擎 / 界面 / 单元测试 / E2E / 打包 /
   代码审查 / 安全核查 / 用户文档 / 汇总交付。功能清单写进各卡正文，不要一个功能一张卡 ——
   那会把 DAG 撑成大扇出，且多数功能共享同一批文件（会并发互写）。
2. **串行打头、并行中段、串行收尾**：第一棒是规格（后续所有卡的唯一依据）→ 中间按文件域可并行的并行 →
   打包依赖全部实现与测试 → 审查/安全依赖打包 → 汇总交付依赖审查。
3. **依赖用 `--parent` 表达**，不要靠「我记得」。`--parent` 要上游真实 id，所以必须**串行建卡并回传 id**；
   同一角色同时只能有 1 张在跑，所以同角色的多张卡天然串行。
4. **建完必须回读**：`show <id>` 里要看到 `parents`；并逐张确认 `assignee` 是真实存在的 `cc-*` 角色。
   脚本没报错 ≠ 依赖挂上了，≠ 角色存在。

⚠️ 这和「业务链深度 ≤ 2 跳」不矛盾：那条针对**内容/运营类**链（选品→策划→制作→上架，跨系统、
上游可能永不 done）。**同一仓库内的软件构建链**文件域互斥、上游确定性 done，多跳是正常的 ——
判据是「上游卡能不能真的 done」，不是跳数本身。

## 铺开角色阵容：共享上下文 + 父子依赖 + 优先级 + 阵容体检

一次把整条业务链交给全部闲置角色的标准流程（实测 10 张卡一次发成、依赖全对、哨兵自动开跑）。

### 1. 每张卡都注入同一段「真实业务状态」和硬约束

业务域角色最容易吐出的东西是**通用 AI 套话**。要让它「基于真实情况」分析，就得把真实状态直接写进卡片正文：盘子里有多少商品、**实际在售几件**、那几件的想要/客询/成交分别是多少、账号历史成交能力、当前数据断点在哪、已有结论是什么。

再附一段**硬约束（违反即视为无效交付）**：不许编造数据（指明用 `tools/` 下哪个探针取真数，拿不到就写「拿不到」）、凭证零泄露、合法合规、产出写各自 output 目录、报告结构「结论 → 证据 → 动作」。

给了这些，worker 才不会在沙地上分析；不给，你只会拿到正确但无用的废话。

### 2. 链式环节用 `--parent`，独立环节不带

`--parent` 需要**上游卡的真实 id**，所以发卡脚本必须**串行创建并回传 id**（不能并发发卡再补依赖）：

```python
tid = create_card(title, assignee, parent=None, priority=10, body=CTX + suffix)
create_card("下游卡", "cc-other", parent=tid, priority=9, body=CTX + suffix)
```

- 父卡未 `done` 前子卡停在 **`todo`**（不是 `blocked`）—— 不占并发位、不计熔断。
- 全部父卡 `done` 后自动升 `ready`，哨兵下一 tick 自动派。**不要手动 promote**，会与哨兵抢单。
- 发完**必须回读核验**：`show <id>` 里要出现 `parents: t_xxxx`。脚本没报错 ≠ 依赖挂上了。

### 3. `--priority` 决定哨兵先派谁

哨兵按优先级降序取 ready 卡（实测 `priority=10` 先于 `priority=8` 派单，`logs/dispatch.log` 直接可见）。**给链首卡最高优先级**，否则支撑类卡会把并发位占满、链首被饿死。并发上限 `WF_MAX_CONCURRENT`，满位时其余 ready 卡排队，**每完成一张自动补位**，无需人工干预。

### 4. 阵容体检：`done` 的卡 ≠ 这个角色在干活

「迁移 / 搭架子」类卡也会 `done`，但不产生任何业务产出。判断某个角色是否真在工作，**唯一可靠证据是它自己的产出目录里有没有真文件**——脚手架留下的 `.gitkeep` 是空占位，不算产出。

```bash
find output -name '.gitkeep' | wc -l             # 空占位
find output -type f ! -name '.gitkeep' | wc -l   # 真实产出
```

逐个 `output/<域>/` 看时间戳：全停在建目录那一天 ⇒ 该角色从没开工。**报告时必须把「卡 done 了」和「角色在干活」分开讲**，否则会把一批搭架子的卡说成整条链在运转——用户会当场纠正。

### 5. 模型档位体检：漏登记 = 静默错派

`WF_AGENT_MODELS` 是**白名单**：只给登记过的角色分模型，**未登记的静默回落到 `WF_CLAUDE_MODEL`**。所以只钉了一半角色时，落单的重活角色会安安静静拿小模型，**没有任何报错**。

审计法：把**全角色清单**逐个走一遍与 `dispatch_claude.sh` 相同的解析逻辑（登记表 → 回落值），打出「角色 / 职责 / 实际模型 / 档位」四列表，再对照分工意图逐行看。**只要「分析/设计/审查」类角色落在小模型上，就是漏登记。**

⚠️ **agent 文件 frontmatter 里的 `model:` 字段是死的。** 派单脚本始终传显式 `--model`，会覆盖它 —— 改 agent `.md` 的 `model:` 对实际执行**毫无影响**，要改模型只能改 `WF_AGENT_MODELS`（或 cc-switch 的 provider 配置）。

⚠️ **别把「档位可能不对」说成「已经出错」。** 若跑过的卡全是机械活（拷贝 / 迁移），它们**根本不触发推理能力差异**，此时没有实证能说小模型导致了失败 —— 这是**潜在风险**，要如实这么讲，不要为了把结论说重而虚构因果。

## 调度机制：闸门 / 提升 / 熔断（读 `kanban_auto_dispatch.py` 实测确认）

回答「还要等多久 / 要人工介入吗」这类问题时，**读代码 + 实测**，别凭印象答。核心三轮逻辑（`tick()`）：

```python
tasks  = board_tasks()        # ⚠️ 只收 status ∈ (ready, running)，且 assignee 以 WF_AGENT_PREFIX 开头
running = [t for t in tasks if t["status"] == "running"]
slots = MAX_CONCURRENT - len(running)
if slots <= 0: return         # 满位 → 本轮直接退，什么都不派（tick.log 里表现为空输出 rc=0）
ready = sorted([...未冷却且未熔断...], key=lambda t: -t["priority"])
```

**四条必须记住的推论：**

1. **`todo` 卡永远不在候选池**（`board_tasks()` 只要 ready/running）。`todo` 不是在等并发位，是在等父卡 —— 这两件事不要混为一谈。
2. **父卡 `complete` 的瞬间，子卡自动升 `ready`，不需要人工 promote。** 隔离实验（在无人使用的板建 P→C，`complete P` 后立刻查 C）实测：`C: todo → ready`，全程无 promote/dispatch 调用。**别手动 promote** —— 会和哨兵抢单。
3. **`WF_POLL_SECONDS` 只在常驻模式生效**（`while True: tick(); sleep(POLL_SECONDS)`）。走计划任务/`--once` 时，真实节拍 = **计划任务的间隔**（本机 2 分钟），与 `WF_POLL_SECONDS` 无关。
4. **熔断绝不能是「失败满 N 次就不再派」—— 那是死状态。** 失败计数在**派单那一刻**就 `+1`，只有卡进 `running` 才清零。若候选条件是 `fail < N`，一张连续失败 N 次的卡会**永远不进候选池**：不派、不告警、不归档，看板上一直挂着 `ready`，哨兵再也不理它。这恰好是用户明令禁止的「既不过也不打回」形态。
   **正确形态是三档熔断**（`_eligible()` 里判，阈值走 `config.env`）：
   ```
   fail <  WF_FAIL_FUSE            → 正常派
   WF_FAIL_FUSE ≤ fail < WF_ABS_MAX_FAIL  → 长退避 WF_LONG_BACKOFF_SECONDS 后再试
   fail ≥ WF_ABS_MAX_FAIL          → archive 退出循环，归档时写清失败次数 + 日志路径
   ```
   退避档必须**按最后失败时间算**，不是「失败够了就永不派」；归档档必须有，否则长尾卡会把配额全吃掉。实测参数 `WF_FAIL_FUSE=5`、`WF_ABS_MAX_FAIL=15`、`WF_LONG_BACKOFF_SECONDS=1800`。
   排查「卡一直 ready 不动」时**必查** `logs/dispatch_state.json` 的 `fail` 字典：
   ```bash
   python -c "import json;d=json.load(open('logs/dispatch_state.json'));print(d.get('fail'))"
   ```
   计数是**按 id**存的，会残留到已归档卡上（`archived` 不进候选池，无害）—— 别把残留计数误报成故障。
   **验证候选策略不要靠读代码**：把 `board_tasks()` monkeypatch 成只返回一张构造卡，再真调 `tick(dry_run=True)` 看它派不派。五个档位各测一遍（正常 / 退避未到期 / 退避已到期 / 退避上限 / 超上限），比通读 `_eligible()` 可靠得多。

### 派单器必须单实例：常驻哨兵 + cron 会双派

**同一个派单器同时存在两个进程时，一张卡会在十几秒内被派两次、被归档两次，配额双倍燃烧，而日志里看不出异常。** 实测：手工起的常驻哨兵与 cron 的 `--once` 撞上，同一张卡的 `claimed` 事件相隔 14 秒来自两个 pid。

对策是 `dispatch.lock` 里的 pid 文件锁：进 `tick()` 前 `_acquire_lock()`（文件里 pid 还活着就直接退，打印「已有派单器在跑」），退出时释放。**锁要在 `--dry-run` 之外也生效**，否则人工排查时的 dry-run 会挡住真哨兵一整轮。

**顺带一个会自己挖坑的操作陷阱**：这类脚本的 `main()` 默认就是**常驻守护模式**，不认识的参数会被**静默忽略**。所以 `python kanban_auto_dispatch.py --max-slots 1`（参数名不存在）不会报错，而是**直接起一个常驻进程**——你以为在做单次实验，实际开出了第二个派单器。手工触发的唯一正确形式是 `--once`（或 `--dry-run`），敲之前先看 `main()` 到底认哪些参数。

### 网关 dispatcher 与哨兵共存 —— 不冲突，是分工

本机 **Hermes 网关在跑**（`hermes gateway status`），而 CLI help 明写 `daemon` 已废弃：「dispatcher now runs in the gateway」。所以同时存在两个调度者，**但不会双派**：

| 调度者 | 职责 | 实测证据 |
|---|---|---|
| Hermes 网关 dispatcher | 提升依赖满足的卡；扫到 `cc-*` 卡报 **`skipped_nonspawnable`**（因为 `cc-<role>` 不是 Hermes profile，是 Claude Code 角色） | 卡事件流 `[01:20] skipped_nonspawnable {'assignee': 'cc-product-planner'}` |
| 本工作流哨兵（计划任务） | claim + 跑 `cc-*` 卡 | 下一行 `[01:21] [run 35] claimed` |

**所以卡事件流里出现 `skipped_nonspawnable` 是正常的、预期内的**，不是错误、不需要修 —— 那是 `WF_AGENT_PREFIX` 防抢机制在生效。排查「谁派的单」时看事件流就能分清：`claimed` 才是真的被派了。

（`kanban.dispatch_profiles: any` 意味着网关会考虑**任意** assignee，但 `cc-*` 一律 spawn 不了 → 一律跳过。这正是设计意图。）

### worker 的两道硬墙：僵尸占位 与 `-q` 模式无审批

**① 前台阻塞无超时 → worker 永久吃满并发位。** `dispatch_claude.sh` 是前台阻塞调用，
模型链路卡住时进程会一直挂着：卡显示 `running`、slot 被占满、后面 ready 卡全部饿死，
而 `logs/dispatch.log` **没有任何报错**（看起来一切正常）。

**但 GNU `timeout` 在 Windows 上杀不动原生 exe —— 不要拿它当安全网。**
git-bash 的 `timeout` 靠 POSIX 信号；`claude.exe` 是原生 Windows 进程，不响应 SIGTERM，
于是 `timeout` 自己先退出、把 claude.exe 孤儿化，卡永远停在 `running`。三条同时成立即确诊：

1. `claude.exe` 的父进程是 `bash.exe`（派单脚本），**不是** `timeout`
2. 进程表里查不到 `timeout.exe`
3. 已跑时长超过 `WF_AGENT_TIMEOUT_SEC`，却既没被杀、也没 block

```bash
# 确诊
powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='timeout.exe'\" | Select ProcessId"
# 真正能杀的：按 Windows PID 杀整棵进程树（bash 里双斜杠，否则 MSYS 会改写参数）
taskkill //F //T //PID <pid>
```

**验证超时必须用真目标二进制。** `timeout 3 sleep 60` 返回 `124` **不能**证明超时可用 ——
`sleep` 是 MSYS 程序、认信号；换成 `claude.exe` 立刻失效。这是个假阳性陷阱，会让人以为
guard 已经装好了。测什么就杀什么。

**CPU 低判不了僵尸。** 上游慢时（NVIDIA 单次 30~300s）CPU 就在 1% 上下浮动，
**真在干活和真卡死在这个指标上长得一模一样**。可靠判活证据是**上游请求日志有没有新行**：

```bash
tail -F "$CLAUDE_HOME/logs/cc-switch.log"   # 每 30~90s 一条「请求目标」= 活着
```

`claude -p` 非交互模式**只在结束时才打印结果**，所以 worker 日志长时间空白是正常的。
组合判断：日志空白 + CPU 低 + **请求还在打** = 正常（在等慢上游）；
日志空白 + CPU 低 + **请求也停了** = 真卡死。后者才是僵尸。

**所以正确形态是「进度感知超时」，不是墙钟超时。** 三个条件同时满足才动手：
`超时 && 近 N 分钟上游无新请求 && worker 日志无增长` → `taskkill /F /T` + block 卡 + 告警。
只按墙钟杀会误杀「慢但在跑」的 worker，把还能出活的成果直接扔掉；判据改动涉及杀进程，
先跟用户确认再上。

> 用 `powershell.exe -File x.ps1` 做进程探测时，**脚本内容必须是纯 ASCII**：
> Windows PowerShell 5.1 按 ANSI 读 `.ps1`，UTF-8 无 BOM 的中文会被打碎成乱码并抛
> `ParserError: UnexpectedToken`。中文标注放到 bash 侧用 `sed` 加前缀。

**② `-q` 模式没有人能审批 → 被判危险的命令一律 BLOCKED。** 内置派单器起 worker 的命令是
硬编码的（`kanban_db_dispatch.py`：`cmd.extend(["chat", "-q", f"work kanban task {task.id}"])`），
**没有 `--yolo`/`--oneshot`**。所以 worker 里的 `python -c`、heredoc、`execute_code`
这类「脚本执行」会被直接拒绝：

```
BLOCKED: Command flagged as dangerous (script execution via -e/-c flag)
         but single-query mode (-q) runs without a user present to approve it
```

**危害是静默的**：文件照样通过 Write 工具落地、produce-check 也能过，但**没有任何命令真的被跑过**
（没跑测试、没跑验收、没 commit）。对策二选一：

- **推荐**：卡片正文写明「不要用 `-c`/heredoc/`execute_code`，把脚本用 Write 写成 `.py` 再 `python <file>`」，
  并在完成须知里要求把命令的实际输出贴回（没有输出 = 没跑）；
- **要解锁**才给 worker 加 `--yolo`（绕过全部危险命令审批，官方原话 `use at your own risk`）——
  这是安全取舍，**必须由用户拍板**，且改的是 Hermes 核心文件，升级会被覆盖。

注意：修好 `auxiliary.approval` 的模型（见 `troubleshoot-hermes-config`）能修掉「审批判定超时」，
但**不会**解掉这条 —— `-q` 无人在场是结构性限制，与审批模型好坏无关。

**判定规则别猜，直接读权威源** `<workspace>/tools/approval_detection.py`（`_execution_flag_findings()`）：
```python
family = _interpreter_family(命令名)   # python/python3/node/perl/ruby/deno/pwsh...
if family and _interpreter_exec_flag(...):     → "script execution via -e/-c flag"
elif family and 任一参数以 '<<' 开头:         → "script execution via heredoc"
# 另：bash/sh 带 -c 且有 payload → "shell command via -c/-lc flag"
```
两个容易写错约束的地方：该规则**只对解释器生效**，纯 shell heredoc（`cat <<EOF > x.txt`）不命中，
但仍统一要求用 Write 工具（可复盘）；`approval_detection.py` 里 `_REMOVED_PATTERN_KEY_ALIASES`
存的是**已移除的旧规则**，别拿它当现行判定列表。

**约束要三层注入，少一层就有卡漏网**（共用一份文本，勿各写一版）：

| 层 | 位置 | 覆盖谁 |
|---|---|---|
| 模板 | `create_card()` 里 `body = with_exec_constraint(body)` | **新建**的卡 |
| 回填 | `kanban edit <id> --body <原文+约束>` | **已在看板里**的旧卡（模板管不到） |
| 派单 | prompt 拼装处包一层 `with_exec_constraint(...)` | 走自己派单器的 cc-* 卡 |

逐层补充：

- 注入函数必须**幂等**（marker 已存在就原样返回），否则模板 + 回填 + 派单会叠成三份。
- 回填用 `kanban edit <id> --body <新正文>`，**不要用 shell 拼字符串**——用 Python `subprocess`
  传 list（无 shell），否则 CJK + 引号会碎。回填完**每张读回** `show --json` 校验 marker 存在。
- 内置派单器（`chat -q "work kanban task <id>"`）**不经过**你自己的派单器，它只读卡片正文 ——
  所以对 `default` assignee 的卡，「回填正文」那一层是唯一生效的一层。

**回归脚本（可重复跑，别只靠目测代码）**：`verify_card_template.py` 真建卡→读回正文→归档；
`verify_dispatch_prompt.py` 验旧卡/新卡/空正文三分支各只能出现 1 次 marker（自己抄原表达式，
不要只复述逻辑）。

### 隔离实验法：验证调度机制不要去动生产板

要确认「提升 / 依赖 / 并发」这类机制行为时，**在没人用的板上建一对一次性的 P→C 卡做实验，做完 `archive` 掉**，不要拿生产板或正在跑的卡试。本机 `hermes kanban boards list` 可见多个板，`xiangmu`/`default` 当时都是空的 —— 拿它们当试验场，零干扰、可重复、结论可信。

### 巡检任务的真实形态 + 告警通道（不查清楚会以为“已通知”）

巡检**已经存在**：job「维护快照（健康检查落盘）」= `healthcheck/maintenance_snapshot.py`（`no_agent` 薄包装，调 `healthcheck.py --append-log`）。

**先分清两个「巡检」**：看板上标题带「巡检」的卡通常是**业务功能**（如客服未读消息巡检），跟流水线健康无关；用户说「不是有巡检卡吗」时，先确认他指的是 cron 巡检，别拿业务卡去答。当前排程 `*/30 * * * *`。改排程用 **`hermes cron edit <job_id> --schedule "*/30 * * * *"`**（实测可用，另有 `--name`）；`cronjob_manage(action='update')` 也可，但**不要**去猜 `cron update` / `cron updata` 这类不存在的子命令。停用/恢复用 `hermes cron pause|resume <job_id>`，**它不吃 `--reason`**（实测报 `unrecognized arguments`，但任务照样被 pause）—— 想留理由就写进 job 名称或项目日志。

**别把周期设成 3 小时以上。** 实测 3 小时档在 8 小时的夜间只跑 2~3 次：中间堆了 1751 个垃圾脚本、10 张卡各打回 8 次后归档、并发槽被 14 小时僵尸占满——巡检下一次才看见，等于没巡。30 分钟是**可用的上限**，且脚本很轻（一次 `kanban list --archived --json` + 几个文件 stat），频率不是成本瓶颈。

自加检查项时就加在 `healthcheck.py` 里（新增一个 `check_*()` 并加入 `main()` 的调用串），**不要另建脚本** —— 那样只会多出一条没人维护的链路。

**四类必须有的静默故障检查**（这四类发生时看板看起来完全正常）：

| 检查 | 阀值 | 级别 |
|---|---|---|
| 派单熔断 | `dispatch_state.json.fail[tid] >= WF_FAIL_FUSE` 且该卡**未归档/未完成** | FAIL |
| 哨兵活性 | `tick.log` 末条时间戳 >15min | FAIL |
| 僵死 worker | `running` 卡的 **worker 日志 mtime** >15min（判据见下）| FAIL |
| 真实产出 | `output/` 真实文件数 vs `.gitkeep` 占位数 | WARN |
| 派单器实例数 | 同名进程 >1 → 双倍烧 RPM 且重复派单 | FAIL |
| 治理文件完整性 | 行数跌到「磁盘/快照/git HEAD 三者最长」的 60% 以下 | FAIL |
| 卡面冲突措辞 | 未归档卡的 title+body 含「不要标记 done / 不得把本卡标记 / 本卡不执行 / 保持未完成状态」 | WARN |

**⚠️ 判僵尸绝不能用 `started_at`，也别用 `claim_expires`。** 卡被反复认领时 `started_at` **不刷新**，一张刚跑 10 分钟的新卡会显示成「11 小时」；`claim_expires` 同样不可靠（自建派单器直写库，不走 CLI 续租）。两者都会让巡检去 reclaim **正在干活**的 worker，把成果直接扔掉。唯一可信信号是 `logs/workers/<tid>.out` 的 **mtime**：>15 分钟无输出才算僵死，卡没有日志文件也算（那是派单失败的残留）。这与派单器自己的 `slots` 回收判据一致。

### 巡检发现可自愈的问题必须动手修 —— 只报不修 = 挂起等人工

巡检报 `✗ 派单 worker 超长运行 … 需 kanban reclaim` 然后就没有然后了，而用户在睡觉 —— 这就是明令禁止的「既不过也不打回」形态。报警文案里写「需人工 X」本身就是设计缺陷：**能在本机确定性修掉的，巡检必须自己修**。

| 故障 | 自愈动作 |
|---|---|
| `running` 卡日志超时无输出 | `hermes kanban --board <b> reclaim <id> --reason "巡检自愈：worker 日志超 N 分钟无输出"`（`reclaim` 有 CLI，不必写库）|
| 治理文件被覆盖/删除 | 从**最长副本**恢复并同步刷新快照 |

`--no-heal` 保留只诊断模式（人工排查时用），默认必须是自愈。自愈结果照实报成 WARN 并写清「已自愈 1 张」，不要静默。

**还缺一道结果指标告警**：以上全是「机制在不在」，没有一个盯「有没有出活」。实测出现过连续 1 小时 0 张 `done` 而巡检一声不吭——因为「零完成」不在检查项里。要补的是：最近 N 小时 `done` 数为 0 且 `ready` 非空 → FAIL（这才是用户真正关心的「流水线死了吗」）。

⚠️ **测完注入故障后必须把假记录从 `维护日志.log` 里删掉**。`--append-log` 会把注入的 FAIL 写进滚动日志，不清理就会让历史撒谎（下次看趋势时会以为真出过事故）。

### 巡检的活归执行层：Hermes 只发卡，code 侧去修

巡检本质是**修代码**的活，不该由 Hermes 侧 cron 承担 —— 脚本只能「查一查、报一报」，
查出僵尸卡最多在报警里写「需 kanban reclaim」，把动作留给人；人在睡觉，这就是挂起。

| 角色 | 干什么 |
|---|---|
| Hermes（cron，约每 2 小时） | 跑发卡器：看板已有活着的巡检卡就跳过，没有才发一张。**只发卡，不干活** |
| 执行角色（如 `cc-framework-manager`） | 领卡 → 跑 `healthcheck.py --no-heal` 拿现成诊断 → 逐项查 → **就地修** → 提交 → 写报告 → 卡上评论 |

发卡器三个必须：

1. **幂等**：`triage/todo/scheduled/ready/running/blocked/review` 任一状态存在标题前缀匹配的巡检卡就跳过。
   不幂等就每 2 小时叠一张，把并发位和配额吃光。
2. **不让 worker 自己建下一张**。worker 建完立刻被派单器捡走 → 兩分钟后又一轮 → 无限递归。
   节奏必须由协调层控。
3. **巡检卡给高优先级**（实测 `priority=50`）。并发位长期满，普通优先级永远排不上队 ——
   用户会以为「巡检没跑」，实际是饿死在队列里。

巡检卡正文必备项：

- 把 `healthcheck.py --no-heal` 列为**第 0 步**（它是诊断工具，不是执行者），它报 FAIL 的项就是本轮要修的项
- 每项都写「修法 + 对应 CLI」（`reclaim` 有 CLI，不必写库）
- 要求「真修真提交，报告含真实命令输出，不许写『已检查，正常』」
- **给 `hermes` 的绝对路径变量**：worker 环境下 `hermes` 未必在 PATH（cron 不继承用户环境），
  裸 `hermes kanban ...` 会 command not found，整轮空转

`healthcheck.py` 保留为**只读诊断器**（`--no-heal`），巡检卡负责动作 —— 两者分工，不要二合一。

### 🚨 告警可能根本到不了用户手上（两层独立断裂）

**别假设「设了 cron 就会通知用户」。** 本机实测两层都断：

**第一层：会话类型本身没有 push 通道。** 桌面 App / CLI / TUI / stateless HTTP 会话都**收不到** cron 投递 —— `cronjob_manage` 创建时直接告知：
> "CLI/TUI and stateless HTTP API sessions have no live-delivery channel. To be notified, recreate or update the job with deliver set to a gateway-connected platform."

所以导入 `deliver='local'` 的 job 写“只存不投”是**双重无声**：既没有通道，自己又是 local。要真告警必须 `deliver` 指一个 **gateway 已连接的平台**。

**第二层：唯一配的平台可能是坏的。** 本机 `config.yaml` 的 `home_channel` 指向 feishu，但 adapter 创建失败。修它要过**四道关**，每道都会让前面白干：

```
WARNING gateway.platform_registry: Platform 'Feishu / Lark' config validation failed   ← 缺凭证
INFO    gateway.platform_registry: dependencies missing — attempting install...
WARNING gateway.platform_registry: requirements not met                                 ← 依赖版本不对
ERROR   gateway.run: ✗ feishu error: feishu connect timed out after 30s                 ← 连上了但卡住
```

| 关卡 | 真正的判据 | 怎么过 |
|---|---|---|
| 凭据 | `.env` 里有 `FEISHU_APP_ID`/`FEISHU_APP_SECRET` | 诊断：`grep -oE '^FEISHU_[A-Z_]+' .env` 为空即根因 |
| **依赖版本** | 插件钉**精确版本**：`Requires-Dist: lark-oapi==1.6.8` | `pip install lark-oapi` 装最新版（1.7.5）**不行**，必须 `==1.6.8` |
| **装到哪个解释器** | 机器常有 2 个 install / 5 个 environment，逐个都要能 `find_spec('lark_oapi')` | uv 建的 venv **没有 pip**（`No module named pip`）→ 用 `uv pip install --python <venv>/Scripts/python.exe` |
| 连接 | `_connect_websocket()` 卡在 `_hydrate_bot_identity()`（/bot/v3/info 无超时） | 走下面的直连 IM API 绕开 |

诊断依赖时**读源码不要猜**：`grep -rn "requirements not met"` 定位到 `platform_registry.py:416`，
再往上看到 `entry.check_fn()` → 插件里是 `pm.extras.available("feishu")` → 源码只是
`all(_importable(a) for a in _anchors(extra))`，`_importable` 就是 `find_spec`。
**所以“装没装”完全取决于运行该进程的解释器的 sys.path** —— 这是多环境机器上最容易漏的。

## 受阻卡：blocked 是终态，评论不会解锁

**`blocked` 没有任何自动恢复。** 派单哨兵只捞 `ready`；人工在评论里回“允许/同意”
只是一条留言，**对状态机零影响**，卡会永久停摆。必须显式 `hermes kanban unblock <id>`。

真实事故：worker 03:14 因“需人工决定”被 block，用户 03:16 评论“允许一次自愈”，
之后 20 分钟系统毫无反应 —— 用户会问“为什么受阻之后没反应了”。

**补齐闭环：每 2 分钟跑 `blocked_recovery.py`**（本项目已有，job `76c1806cab62`）：
- 新 blocked 事件 → 推飞书（卡号/标题/原因/怎么回复），按事件时间戳去重
- blocked 之后出现人工评论 → 自动 unblock + 回推飞书确认（否则人不知道系统有没有动）
- 防环：只认 block **之后的新**评论，恢复一次即不再触发；另加每卡上限兜底

**⚠️「每卡上限」的默认值只有 3 —— 无人值守过夜必须先改掉。** 上游不稳定时 worker 每几分钟失败一次，
「卡数 × 3」在半小时内就会耗尽，之后 `blocked` 只涨不降、`dispatch.log` 照样每分钟一行、
看起来在跑，实际整夜空转。过夜前把它抬到 50~100（`WF_BLOCKED_MAX_RECOVER="80"`）、
并把 `WF_AGENT_TIMEOUT_SEC` 从 7200 降到 1800（并发=1 时它是整个队列停摆的上限）。
完整交接清单（含 powercfg 免休眠实测、三哨兵核对、早间判据）见
`references/unattended-overnight-operation.md`。

**怎么区分人工 vs agent 评论（实测）**：`kanban comment --author` 默认取
`$HERMES_PROFILE or 'user'` ⇒ agent 落库为 `default`，桌面端用户回复为 `desktop`。
所以人工判定用 allowlist（`desktop,user,cli,web,telegram,feishu`），**不要**用
“非 default 即人工”这种反推。

**拿事件/评论的结构化数据用 `hermes kanban show <id> --json`**（顶层 `task/
latest_summary/parents/children/comments/events/runs`；`events[].kind` 取值含
`created/promoted/claimed/spawned/heartbeat/commented/blocked/unblocked/`
`skipped_nonspawnable`）。`kanban log` 给的是 agent 运行转录，**不是**事件流。
`list --json` 不包含 parents 字段，查依赖必须逐张 `show`。

### ✅ 绕开适配器：直连 IM API 发告警（推荐，链路短得多）

网关适配器要 websocket 长连接，插件内部还有无超时的阻塞调用；而 `feishu_notify.py`
（取 `tenant_access_token` → `POST /im/v1/messages`，纯 stdlib）已验证可用且能优雅降级。
**巡检告警这种单向推送不需要 websocket** —— 别为了让它“看起来正确”去修适配器。

**但直连 IM API 的第一道坑不是权限，是“bot 不在任何群里”**。新应用默认无群，发什么都 230002。
**自救办法（实测有效）：机器人自己建群 —— `POST /im/v1/chats` 成功则 bot 自动入群。**

- 建 **`chat_type="public"`** 的群：可被搜索加入，用户搜群名就能进，**不需要 open_id**
- 建 `private` 群没用：bot 能发但无人可见，且 `GET /im/v1/chats/{id}/link` 会返回 **404**
- 发一条消息（code=0 拿到 message_id）算真正通了
- **用户加入后要转私有：“更新群信息”是 `PUT /im/v1/chats/{chat_id}`，不是 PATCH**。
  用 PATCH 不报错但**静默无效**（响应没有 `code` 字段，`chat_type` 原封不动）—— 这类“看起来成功但其实没生效”的调用必须改完立刻 GET 回读校验。
- `DELETE /im/v1/chats/{chat_id}` 可解散自己建的群（清理建废的试验群）
- 拿到群成员列表就顺带收获了**该应用下的用户 open_id**（`/im/v1/chats/{id}/members?member_id_type=open_id`），以后可直接私聊

推送侧的四个真实报错码，遇到直接对应处理，别瞎试权限：

| code | 含义 | 处理 |
|---|---|---|
| `230002` | Bot/User can NOT be out of the chat | **bot 不在该群** → 自建 public 群，或人工拉群 |
| `99992361` | open_id cross app | 这个 open_id 是**另一个应用**签发的，跨应用不可用 |
| `99991672` | Access denied（缺 scope） | 缺 `contact:user.id:readonly` 等，无法按邮箱/手机反查 open_id |

**两个容易误导人的 API 事实：**
1. `GET /im/v1/chats` **只列群，不列私聊**。返回空不代表用户没私聊过 bot。
2. **用户私聊 bot 并不能解决问题** —— bot 收消息靠事件订阅（ws/webhook）；适配器没连上时，
   用户发的话 bot **根本没收到**，也不会因此建出会话。别让用户去白做这一步。

查 bot 到底在哪：`GET /im/v1/chats`（**空 = 不在任何群**，这是 230002 的根因）；
查 bot 自己是谁：`GET /bot/v3/info`（返回 `app_name` + `open_id`）。
关键推论：**换了 app_id 后，旧 config.yaml 里的 chat_id/user_id 全部作废** —— open_id 是按应用签发的。

收尾：`maintenance_snapshot.py` 已改成「健康完全静默 + 有 FAIL 才推 + 推送失败只写 stderr」，
推送是 best-effort，**绝不能因为发不出去而影响快照本身**。

诊断告警通道时按顺序验证：`config.yaml` 的 `home_channel` → 网关日志里 adapter 是否创建成功 → 凭证键是否存在 → 依赖包是否可 import → job 的 `deliver` 值。**缺凭证时不要自己编，也不要把「装个依赖」当成修好了** —— 拿不到凭证就不能声称链路已修复。

## 审查环节：状态机支持 ≠ 链路接上

Hermes 的看板有完整的 review 通道（`request-review` / `request-changes` / `reopen-review`，
DB 层有 `request_review()`），**但自建派单器根本不走它**：派单 prompt 只塞标题 + 正文 + 执行约束，
worker 干完直接 `kanban complete`。实测结果 —— **每张卡都是 `running → done` 直连，0 张经过 review**。

两个连带后果，都让「已完成」不可信：

- **worker 主动请求审查会被吞掉。** 包装脚本退出时只看 exit code 和产出指纹，
  不看 worker 正文里那句「建议标记 review」—— 照样 `complete`。**worker 的文字请求对状态机零影响。**
- **验收没跑也能 done。** worker 自述「三条验收命令均未执行」「无法断言语法正确」时照样 `complete`；
  而 produce-check 只判「有没有产出」，判不了「产出对不对、验收跑没跑」。

要真审查必须自己接线：worker 端改走 `request-review` → 一个周期任务扫 `review` 卡 →
逐条核对卡上的验收判据 → 通过才 `complete`，不通过 `request-changes` 打回，三次打回则 block + 告警。
**先做「同角色 + 自动判定」这一档** —— 加独立 reviewer 角色会直接吃掉一半并发位。

**回答「某个环节在工作吗」不能靠印象或看板列名，必须查事件流。** 看板列里有 `review`、
CLI 有 `request-review`、卡能停在 `review`，这三件事都**不能**证明有卡真走过它 ——
唯一证据是 `task_events` 里存在对应 `kind` 的行。查询方法见 `references/board-forensics.md`。

### 已落地：`hermes_acceptance.py`（协调者验收器）

`scripts/hermes-wf-xianyu/hermes_acceptance.py`，把原版手册 §7.1「三件事」代码化：

| 模式 | 作用 |
|---|---|
| 无参 | 处理 `review` 队列（cron 调） |
| `--audit` | 只读审计 `done` 卡，报告写到 `output/maintenance/` |
| `--card <id>` | 单卡验 |
| `--dry-run` | 只判定不落库 |

判定**三档，不是两档**：

- `PASS` → `complete`
- `FAIL` → **`reopen-review <id> --reason "<缺项>"`** 打回（**不是** `request-changes`）；连续 `WF_ACCEPT_MAX_REJECT` 次 → `block` + 飞书
- `MANUAL` → **留 review 等人工**，不假装通过、也不冤枉打回

**`request-changes` 从定时任务调必失败**：它要求该卡处于**活跃 review run**（得有 reviewer 先认领），协调者由 cron 直接判定时没有 run，报 `task is not in an active review run` 就什么都不动 —— 卡会永远停在 `review`。自动验收一律用 `reopen-review --reason`：它不需要 run，直接把卡送回 `ready`，哨兵下一 tick 重派。

三档是必须的：`①无卡号提交` 既可能是假 done，也可能只是 worker 没写卡号 ——
一刀切判死会误杀，一刀切放过等于没验。

判定细节（每条都踩过坑）：

- ① `git log --all --grep=<卡号>`；查不到时回退查**文件域内有无提交**作弱证据 → 转人工而非判死
- ② 越界比对要**豁免治理文件**（`项目状态.md` / `操作日志.log` / `.gitkeep` / `docs/`），
  否则每张卡都「越界」；**聚合提交**（一个 commit 含多个卡号）不判越界 —— 归属无法归因
- ③ 交付物存在性：`output|analysis|evidence|docs` 缺失 = 硬伤 FAIL；
  `src/` 缺失更可能是「待迁源文件」或改名 → 转人工；**空目录算未交付**
- MIG 卡常常没有「交付物」段，交付目标写在「文件域」里 → 用文件域兜底
- 占位符 `src/roles/<其他角色>` 必须过滤，否则被当成真实路径

实测 17 张历史 done 卡：`PASS 6 / FAIL 0 / MANUAL 11` —— 11 张全是卡面没写文件域或交付物。
**验收能否自动化取决于卡面质量，所以约束必须写进卡片模板**（见下）。

### 卡片侧前提：卡面 + 提交必须机器可判

`wf_common.EXEC_DELIVERY`（marker `交付纪律 —— 必读`，由 `with_exec_constraint()` 注入）要求：

1. 只在文件域内动手
2. **一卡一提交，提交信息必须带卡号**（`t_xxx ROLE 一句话`），不许聚合提交
3. 交付物必须真实存在（目录不能空）
4. 验收命令必须真跑并贴真实输出，不接受「应该没问题」

`with_exec_constraint()` 现在是**两段幂等注入**（执行约束 + 交付纪律），各自查自己的 marker。

### 🚨 只有约束、没有目标的卡 —— 没人知道该干什么，done 卡因此批量失真

实测一张 97 行的卡：1–64 行（1561 字符，62%）全是「不许做 X」+ 交付纪律，
后半段是文件域/交付物/验收判据/禁区 —— **0 行说明要做什么**。同类卡在一批 34 张 `done` 里占 33 张。

后果不是 worker 不动，而是**它自己发明任务范围**，两个方向都踩过：
照角色定义写 `output/marketing/`、照卡面写 `products/`，两轮都没交付；
或者写一个「生成器脚本」交差，而脚本从没跑过 —— **准备脚本 ≠ 交付物**。

规则：**卡面必须先说「要做什么」，再说「怎么交」。** 硬顺序：

```
## 目标（要做什么）   ← 具体步骤 + 交付物清单 + 范围钉子（「只做这一个 SKU」）
## 交付物
## 文件域
## 验收判据
## 禁区
· 执行约束 / 交付纪律（由 with_exec_constraint() 自动追加在末尾）
```

落地三件（都在 `wf_common.py`）：

- `TASK_MARKER = "## 目标"` + `has_task_section(text)` —— 判定函数，回填与体检都靠它
- `build_card_body(goal, steps, deliverables, domain, acceptance, bans, task_id)` ——
  **建卡一律走它，禁止手写卡面**，段序由函数保证
- `with_exec_constraint()` 对**没有目标段**的卡在正文最前插一行告警
  `⚠️ 【本卡缺少「## 目标（要做什么）」段 —— 建卡时就漏了】`

自查一条判据：把全部未归档卡的正文过一遍 `has_task_section()`，缺目标段的数量必须是 **0**。
存量卡补目标段要**置顶**（`kanban edit` 或直接写 SQLite），**追加到末尾等于没写**。

**卡面文件域 > 角色定义文件域。** 两个真相源冲突时（角色 md 写 `output/marketing/`、
卡面写 `products/OA-004/**`），worker 两轮各听一个，两轮都交不成。这个裁定必须显式写进
`EXEC_DELIVERY` 第 1 条（**冲突时只看卡面**），并在卡面里附一句同样的话。

### 坑：`kanban edit --body` 写不了多行正文

实测 2026-10-18：

- `--body "20 行中文"` → 返回 `Edited`，但正文被写成**最后一行**（10 字）
- `--body "---\n..."` → 直接 `rc=2`（`---` 被当成选项）
- 短单行（25 字）正常

后果：一次「回填 12 张卡」的脚本**全部静默失败却报成功**，直到逐卡读回才发现卡正文还是原始 25 字。
**改正文必须走 SQLite**（`kanban.db` 是唯一真相，`kanban show` 读同一份），写完用 CLI 读回确认 ——
参考 `backfill_delivery_constraint.py`（先备份 DB，再 UPDATE，再 `cli_body()` 读回比对）。

**通用教训**：`kanban edit` 之后的「成功」一律用 `kanban show` 读回验证，不看返回码。

### 抗漂移：写进会自动加载的文件

角色契约落在仓库根 `AGENTS.md` —— Hermes 的 `coding_context.py`（`_CONTEXT_FILES` 含 `AGENTS.md`）
会把它注入会话上下文，换会话、上下文压缩后仍在。
**光靠当轮对话里的口头约定，压缩一次就没了。**

## cc-switch 上游 500 的诊断与禁区（实测，2026-10-18）

看到 cc-switch 界面上一大片 HTTP 500 时，按这个顺序查，不要先归因于配置错误：

1. **先看 `is_streaming` 字段。** `SELECT status_code,is_streaming,COUNT(*) FROM proxy_request_logs GROUP BY 1,2`。实测 272 条 500 **100% 是 `is_streaming=0`（非流式）**。
2. **分组算成功率。** 实测流式 42/42 成功(100%)、非流式 36/210 成功(17%)。非流式里 175/210 的 `input_tokens < 1K` —— 是微小辅助调用在坏通道上反复重试。
3. **直连上游对照，绕开代理。** 实测直连 NVIDIA：流式 4/4、非流式 2/4 —— 证明是上游非流式通道半死，不是代理配置错。
4. **查 `request_model` 与实际 `model` 是否相等。** 相等 = cc-switch 没做映射、把客户端原名直发上游。实测 `claude-sonnet-5 → claude-sonnet-5` 51 次 0 成功，而 `claude-sonnet-5 → nvidia/...` 10 次 10 成功。

### 禁止的做法（实测会直接搞死 agent）

- ❌ **`CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK=1`**。听起来完美（“全部走健康的流式”），实测 3 次对照：**关掉 0/3 成功**（全部 `Stream ended without receiving any events`），**保留 3/3 成功**。原因：上游流式约一半时间返回**空流**（代理 HTTP 200 但只有 `message_stop`、无内容事件），那时非流式回退是唯一救命路径。**日志里 500 刷屏是上游症状，不是可消除的故障 —— 宁可看它刷，也不能关回退。**
- ❌ `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`、`CLAUDE_CODE_NONSTREAMING_TIMEOUT_RETRIES=0` —— 同样导致 `Stream ended` 直接失败。
- ❌ 用档位别名（`claude-sonnet-5`）作为 `--model` 传给 claude.exe。cc-switch 首次尝试会把别名**原样**发上游（上游不存在 → 503），只有重试才替换成真实模型，而客户端拿到的是首次的失败码。**派单应发真实模型名。**

### 环境变量的真相来源

想确认某个 `CLAUDE_CODE_*` 变量是否真存在，别搜文档（页面渲染不全），直接抠二进制：
```bash
grep -aoE "CLAUDE_CODE_[A-Z0-9_]{4,}" "<claude.exe 路径>" | sort -u
```
实测能抠出 771 个。

**⚠️ 环境变量必须在派单脚本里 `export`。** cron/派单器进程早于用户级环境变量存在，子进程继承的是旧环境，读不到注册表里的用户变量 —— 改了 `[Environment]::SetEnvironmentVariable(...,'User')` 却不 export，等于没改。

**⚠️ cc-switch 会过滤 provider env 里的环境变量**，生成 settings.json 时只放过白名单内的键。写进 DB 不等于会传到 Claude Code，必须读 settings.json 验证，没传过去的改用 Windows 用户级变量 + 脚本 export。

## 上游速率预算：40 RPM 是“分钟总量”，真瓶颈是“突发”

NVIDIA Build/NIM 默认 **40 RPM**（账号级、按 key 计，提高需付费部署）。但把并发开到接近这个数会出错：

- 实测并发 3 时，仅 **23 RPM 的那一分钟就吃到 4 个 429**，且 429 之间只隔 1~4 秒 —— 上游按**突发窗口**限流，不是平滑的分钟桶。
- **cc-switch 的重试也吃配额**：`max_retries=6` 意味一次逻辑请求最坏消耗 6 个 RPM，而且重试是**连续立即重发**（config 里没有退避参数可调），几秒内就能把瞬时速率拉爆。

可用的三个旋钮，按优先级：

1. **派单错峰（最有效）**：容量给 3，但 `WF_DISPATCH_PER_TICK=1` —— 每分钟只新起 1 个 worker，后续分别在下一、二分钟起跑。让 cron 的 1 分钟节拍白赚一个天然限速器。
2. **RPM 闸门（最后一道保险）**：每 tick 读 cc-switch 的 `proxy_request_logs`，统计**最近 60 秒实际请求数**（含重试），≥ 40×80% = 32 就跳过本轮。不要按“派了几个 worker”估算，要查真实日志 —— 重试会把估算打偏好几倍。
3. **并发数**：它只决定“同时在跑几辆”，不决定瞬时速率；调它解决不了 429。

```sql
-- 闸门用的查询（created_at 是 10 位秒级；列长分布可自证）
SELECT COUNT(*) FROM proxy_request_logs
 WHERE created_at > strftime('%s','now')-60
    OR created_at/1000.0 > strftime('%s','now')-60;
```

实测基线：并发 3 + 错峰后 7~16 RPM、429 归零；未错峰时 23 RPM 就爆 429。

### 🚨 闸门不是限流器：它管“要不要再派一张”，管不住已经在跑的会话

这是本工作流最贵的一次误判。**RPM 闸门全绿时上游照样能被打爆**，因为已经起跑的 worker
不受它约束 —— 实测单个 Claude Code 会话 30 分钟打了 **3219 次请求 = 107.8 RPM**，
而同期正常会话是 **5–14 RPM**。闸门 32 就停派，可那一个会话自己就是上限的 2.7 倍。
定位跑飞会话只需一条查询（按 `session_id` 归集，见下方 reference）。

推论：**判“速率是否健康”只能看单会话 RPM，不能看派了几个 worker**；并发数与闸门都不构成对在跑会话的限速。

#### 反方向同样致命：闸门常红 = 业务链整体饿死

同一个闸门还有个更常见的死法 —— **它不是偶尔误拦，而是永远关着**。闸门统计的是「最近 60s 上游请求数」，
而这个数**包含正在跑的 worker 自己发的请求**。实测：闸门上限 32，而在跑的 3 张卡自身就是 **81–162 RPM**，
于是每轮日志都是同一行 `速率闸门：最近 60s 已发 162 RPM（上限 32），本轮不派单` ——
**新卡永远拿不到槽位，而流水线看起来完全正常**（哨兵每分钟 rc=0、日志有行、看板有 ready 卡）。
后果：整条赚钱链 10 张卡躺了 22.4 小时、0 次尝试。

三条结论，别再犯：

- **不要在派单层做速率闸门。** 派单层只能决定「要不要再起一辆车」，它对在跑的会话零作用，却会把排队饿死。
  速率控制只留**一处**：上游限流代理里按每次尝试排队（见 `references/upstream-rate-limit-discipline.md` §6）。
- **并发数才是派单层的正确闸门**（`WF_MAX_CONCURRENT`）；RPM 一律交给代理守。
- 已经装了闸门时，**先数它的判定分布**：`放行 / 拒绝` 各多少次。拒绝占比接近 100% ⇒ 它不是保险，是路障。

#### 监视器和被监视对象不能共用同一份稀缺配额

巡检一旦做成「发一张卡让 worker 去查」，它就变成了**同一条链路上的消费者**：吃并发位、吃 RPM、
与被巡检对象抢同一份上游配额。实测最坏形态 —— 一段 30 分钟的上游故障里，那个把上游打到 key 冷却的
**107.8 RPM 风暴源，就是巡检 worker 自己**；而同一时段巡检卡被派了 3 次、全部在跑，却什么也没发现
（它无法观测自己造成的伤害）。

规则：**巡检默认走脚本 + cron，不调 LLM、不发卡。** 只有「必须就地改代码」的那一类自愈才发卡，
且必须幂等、低优先级、不与业务链争槽位。

### 🚨 重试必须重新占名额，否则限流代理就是放大器

给上游加 429 重试时，`LIMITER.acquire()` **必须写在重试循环内**。写在循环外（进函数时拿一次、
之后就重发）时，6 次重试全部绕过限流器 —— 出站速率最高是计数速率的 7 倍，再乘上 cc-switch
自己的 `max_retries`。实测后果：限流器显示 `RPM=31/90 平均等待=0.0s`（看起来空转），
而每分钟还有 80–130 条重试，实际出站 ≈130 次/分 = 官方上限 3.3 倍。
**「限流器没在拦」本身就是放大器的症状。**

### 🚨 429 归因三问：不要用“实验”证明“跟速率无关”

一次阶梯测速（10s 间隔首发就 429、3s/1.5s 间隔全 200）会被读成“429 是随机抖动，速率不是瓶颈，
可以把上限提到 90”。**这个读法在账号已经进入冷却簇时必然得出**，因为它测的是抖动不是上限。
提上限之后实测第一分钟就 84 RPM = 官方上限 2.1 倍，key 被打进服务端硬冷却。

正确归因顺序（三条命令内出结论）：

| 观测 | 结论 |
|---|---|
| **孤立单发**（间隔 >5s、只发一次）也 429 | 不是我们的瞬时速率，是**账号/key 级冷却** |
| 同上但 `GET /v1/models` 仍 200 | key 有效，**不是鉴权失败**（别去换 token/查权限） |
| 同时刻换另一个 key：3/3 全 200 | 确认是**按 key 冷却** → 该做 key 轮换，不是降速重试 |

**绝不因为“想让它快点跑”而提高 RPM 上限。** 官方 40 就是天花板；调高只会把 key 打进冷却，
恢复成本（半小时以上 + 换 key）远高于省下的那几分钟。

### 🚨 假健康：成功率 92% 而吞吐只剩 1/5

代理在内部消化 429 时，`proxy_request_logs` 里**看不到失败** —— 客户端最终拿到 200。
所以状态码成功率会回升到 92–94%，看起来“修好了”，实际每个请求要烧 6 次上游尝试、单请求最坏
**73s** 才返回，在跑的 worker 吞吐从 5–14 RPM 掉到 **1.5–1.7 RPM**。
**判健康要看三个数，缺一个就会被骗**：单会话 RPM、单请求实际耗时、重试行数占比。
只看 `status_code` 分布 = 只看了被代理擦干净的那一面。

完整取证配方（按 session 归集的 SQL、429 归因脚本、代理侧必须守住的两条铁律）见
`references/upstream-rate-limit-discipline.md`。

## 验收打回：这些坑会让卡永远停在 review 或无限循环（全部实测）

协调者（Hermes）从 cron 判定 review 卡时，四个连环坑，踩中任何一个流水线就死：

1. **`MANUAL` 的理由存在 `r["manual"]`，不在 `r["problems"]`。**
   直接 `"；".join(r["problems"])` 得到空字符串 —— 日志里会看到 `会打回 t_xxx：` 后面空空的，
   worker 收到空原因根本没法改。必须读 `r["manual"]`，并给具体改法。

2. **打回计数只数 `changes_requested` 永远是 0。**
   `request-changes` 路径记 `changes_requested`，但协调者从 cron 用的是 `reopen-review`，
   它记的是 **`review_reopened`**。只数前者 → 计数恒 0 → 死循环保险永不触发 → 无限打回。
   两种事件都要数：`kind IN ('changes_requested','review_reopened')`。

3. **`block` 当升级手段会死循环。**
   实测 block 掉的卡会被看板内核**自动 promote 回 ready**（事件序列
   `blocked → promoted → skipped_nonspawnable → claimed`），于是
   「派单→失败→打回→block→自动恢复→再派单」无限转，一张烂卡能耗死整夜的上游配额。
   **升级要用 `archive`**：彻底移出自动循环，不占并发、不占 RPM、不再吵人。

4. **`reopen-review` 会「生效了却返回非 0」。**
   实测事件 `review_reopened` 已写入、卡状态已变 ready，命令仍返回 rc=1，导致日志误报
   「打回失败」并触发重复重试。**不要信返回码，打完直接 `fetch_task(tid)["status"]`
   看卡是不是真的离开 review 了。**

另外：用户定调 —— **无法确证（MANUAL）不许挂起等人工，直接打回重做**。
挂起会让卡既不过也不打回，整条流水线停在那儿。打回是常态，`WF_ACCEPT_MAX_REJECT`
不要设太浅（实测 2 会反复升级成灾难，用 8）。

## 受阻卡必须按 `block_kind` 分流，否则无人值守等于没做

原逻辑（错的）：只在「有人类评论后」才 unblock 受阻卡。后果：worker 因上游 500 / 硬超时被
block 的卡会一直躺到人早上醒来才动 —— 夜间完全停摆。

正确做法：按阻塞原因分流，只有真需要人决策的才等人。

| block_kind | 处置 |
|---|---|
| `transient`，或 kind 为空且原因命中 `失败 exit=` / `子员工` / `硬超时` / `worker` / `500` | **自动 unblock**，静默重派，不推飞书 |
| `needs_input` | 推飞书告警，等人评论回复后自动恢复 |
| `capability` | 推飞书告警（缺权限/凭证，agent 自己做不了） |
| `dependency` | 留在 todo，父卡完成后由内核自动 promote，不需人也不需脚本 |

自动恢复必须带**冷却**（实测至少 120s），否则会和派单哨兵叠加把上游打死；
并带上限（`WF_BLOCKED_MAX_RECOVER`），避免一张卡无限重试。

**「卡被杀/报 503 了会重派吗」有三个互不相干的计数域，答一个就是答错。**

| 层 | 触发 | 计数 | 上限 |
|---|---|---|---|
| 派单脚本内重试 | 输出命中 `500`/`503`/`overloaded`/`Stream ended` | 循环计数 | `WF_CLAUDE_RETRY`（默认 5），间隔 20s |
| 卡被 block 后的自动恢复 | `block_kind` 或原因命中瞬时错误 | `task_comments`/事件 | `WF_BLOCKED_MAX_RECOVER` |
| 派单层失败计数 | 每派一次就 +1，进 `running` 才清零 | `dispatch_state.json` 的 `fail` | 三档熔断（见上文） |

三层叠加才是一张卡的真实寿命；改任何一层的上限都要把三层的总消耗算一遍（最坏 = 重试 × 恢复 × 失败上限），
否则会把配额耗在无残值的长尾卡上。另外别漏了第四道兑底：**worker 跑完没提交时协调者会代提交**，
所以即使这轮被 503 杀死，已经写出的内容也不会白费——汇报时要讲这一条，否则用户会以为失败就全丢了。

**踩过的坑**：`hermes kanban block` 的原因是**位置参数**，不是 `--reason`：
```bash
hermes kanban block t_xxx "子员工失败 exit=1"          # ✓
hermes kanban block t_xxx --kind needs_input "要人定"   # ✓ 带类型
hermes kanban block t_xxx --reason "..."               # ✗ 静默无效，卡不会被 block
```
用错语法时卡会停在 ready 并被真派单 —— 造测试卡时尤其要注意，造完立刻归档清除。

## 「一整天 0 张 done」的头号原因：卡片不要求提交

卡片正文通常只写「做什么」，**从没写「怎么交」**；而验收关要求提交信息带卡号。
两边一对不上，就是结构性不可能通过：worker 干完活、文件也写了、就是不 commit →
验收判「无卡号提交 = 疑似假 done」→ 全部打回 → done 永远不涨。

诊断方法（一分钟出结论）：
```bash
git -C <repo> log --since="8 hours ago" --pretty="%h %ad %s" --date=format:%H:%M | grep -c "^.*t_"
```
```sql
-- 看卡被派了几次，是不是永远那几张在打转
SELECT task_id, COUNT(*) FROM task_events WHERE kind='claimed' GROUP BY 1 ORDER BY 2 DESC;
```

**修复要把交付纪律写在派单脚本里，不要依赖卡片正文。** 每次派单无条件追加：
必须 `git commit` 且 message 以卡号开头、只 add 自己产出的文件、不要 `git add -A`、
临时脚本放 `scripts/tmp_` 并清理、验收不采信自述。
并在启动 claude 前打一条日志留痕，否则无法验证到底追没追加。

### 卡面里的反向指令会制造无限打回循环

比「没写怎么交」更糟的是卡面**明确禁止交付**。实测某张探测卡的正文写着
「本卡不执行该脚本、不写日志、不改任何其他文件」「不要把本卡标记 done」，
worker 照卡面做 → 永不提交 → 验收判「疑似假 done」→ 打回 → 重跑 → 再打回，
八次后自动归档，整张卡白烧。

**派单器强加的交付纪律与卡面正文同级时，worker 会照更具体的那段执行，所以卡面必须让位。**
铺卡或回填正文前，扫一遍这些词：`不要提交` / `不提交` / `不要 commit` / `不要标记 done` /
`不要执行` / `只写不跑`。命中就把它们改写成**交付方式**（「产出脚本并提交，但不执行它」），
而不是留着「不要提交」。要真不能提交，就把标题改成命中 `WF_VERIFY_KEYWORDS`
的验收类卡，让「零产出」成为合法结果 —— 两条路选一条，不能两头都要。

## 派单必须公平轮转，否则大多数卡永远轮不到

按 `-priority` 排序时，priority 全为 0 的卡顺序恒定 → 永远是头部两三张反复重试。
实测 16 张 ready 只有 2 张被派过，其余一次没跑。正确排序：

```python
key=lambda t: (int(STATE["fail"].get(t["id"], 0)),      # 失败少的优先
               float(STATE["recent"].get(t["id"], 0)),   # 越久没跑越优先(0=从没跑过)
               -t["priority"])
```

## 工具调用是否真的坏了的判定法

看到仓库里冒出大量 `run_*.py` / `git_*.json` / `do_git.py` 时，先别断定模型坏了 ——
那常常是「禁用 `-c`/heredoc，改成写脚本再跑」这类约束的副作用。
用 3 行命令去证伪：
```bash
claude --model <m> -p "用 Write 在当目录建 hello.txt，内容 WFTEST，然后只回答 DONE"
cat hello.txt   # 文件真实存在且内容对 = 工具调用正常
```
真坏了的特征是：**模型把工具调用输出成文本/JSON 存到磁盘**（文件内容形如
`{"type":"function","function":{"name":"execute_code",...}}`），那种才是上游降级导致的。

## 仓库污染：禁用 `-c` 的规则会造出上百个一次性脚本

AGENTS.md 写「禁止 `bash -c`/heredoc，改成 Write 写文件再跑」时，每个小命令都会
变成一个文件。实测一个上午在仓库根堆了 **199 个** `run_*.py` / `git_commit.py` /
`do_git.json`。必须在 `.gitignore` 里预先堵住：

```gitignore
/run_*.py
/test_*.py
/git_*.py
/do_*.py
/exec*.py
/verify*.py
/check*.py
/*.bat
/*.ps1
/scripts/tmp_*
```

验证方式：新建 `run_pollution_test.py`，`git check-ignore -v` 应指向你的规则行，
且 `git status` 里出现次数为 0。**只堵根目录与 scripts/，不要用全局 `*.json`** —— 会误伤 data/ 业务数据。

注意：已经被提交过的 `tmp_*` 不受 .gitignore 影响，要 `git rm --cached`。
清理时先分清两类：
- **提交尝试桩**（28 行、只有 `subprocess.run(["git",...])`）→ 删
- **实质分析生成器**（几百上千行）→ 留，它们是报告的复现依据，删了报告不可复算

## 清污染之前必须验证「未提交改动」是真工作还是垃圾

不能看 `git status` 有两百个改动就一律回退。判据是**能不能跑**：

```bash
# 例：一个把 sys.path 引导抽成 bootstrap 模块的重构
cd src/framework && python -c "import timeout_utils"
# 报 No module named 'src' → 行内引导本来能处理直接执行，重构后不能了 → 回退
```

行内引导会向上查找仓库根修正 sys.path；改成 `from src.x.bootstrap import` 后，
直接执行时 `src` 尚不可导入，必然失败。**未提交 + 未验证 + 破坏原调用方式 = 污染**。

另外要查 worker 有没有把交付物写到工作区却不提交 —— 那是真工作，应该先入库保住，
不要跟着垃圾一起清掉。

## 日志文件会被 worker 重写截断

`操作日志.log` 这类追加型文件，worker 可能用 Write 整个覆盖（实测 1338 行→17 行；同一份文件一天内被覆盖三次，2113 行→4 行）。
恢复源**取三者最长**（磁盘 / 守卫快照 / `git show HEAD:<file>`），不要无条件 `git checkout --` —— worker 会把**空文件** commit 进 HEAD（实测 `运维手册.md` 在 HEAD 里是 0 行），这时从 git 恢复等于把文件清零，比不恢复更糟。取最长的副本写回，并**把快照同步刷新成同一份**，否则下一轮又拿旧快照盖新内容。然后把丢掉的条目补回去。
清理动作本身也要写进日志，否则审计链断了。

**守卫只是兜底，不是修法。** 快照恢复有 10 分钟空窗，覆盖发生在这段窗口里就白丢一轮。真正的修法在派单提示词的交付纪律里写死：**治理文件（`操作日志.log` / `项目状态.md` / `运维手册.md`）只能追加，永远不许 Write 覆盖、更不许删**，要记录就用 `printf '%s\n' "..." >> 操作日志.log`。worker 用 Write 是因为它只会这一个写文件工具——不明确禁止，它就会当成「更新文档」把整份重写。

## worker 永不提交：四层根因，必须逐层排掉

worker 「干完活却不 commit」不是它懒，是四道墙叠在一起。少拆一道就还是一张 done 都没有。

**① 没 Bash 工具** — `--allowedTools` 无论怎么传都没用：
```bash
--allowedTools "Bash,Read,Write"     # 逗号串 → NO_BASH
--allowedTools Bash Read Write      # 空格分开 → NO_BASH
（不给）                              # → NO_BASH
--permission-mode bypassPermissions # → Bash 可用，能自己 commit
```
判定：直接问 agent「用 Bash 建 hello.txt 并 cat，没有 Bash 就回答 NO_BASH」。
无人值守跑批本来就不该有人审批，这个旗标是必需的。

**② 工作目录是仓库子目录** — worker cwd 常是 `src/roles/xxx`，它按仓库根相对路径
`git add docs/x.md` → `fatal: pathspec did not match`，于是它以为「环境不支持提交」。
派单时用 `git rev-parse --show-toplevel` 求真实仓库根写进提示词。

**③ 提示词里的反引号会被当命令执行** — `PROMPT="... "git add docs/x" ..."` 里的反引号
在字符串赋值时就会跑，日志里会出现 `pathspec: command not found` 和假的 git 报错。
拼提示词永远不用反引号，用单引号或裸写。

**④ 角色文件域 vs 卡面约束互相矛盾** — 角色 md 写「文件域 = src/roles/xxx/」，
卡面又写「只准 Write、禁止一切 shell 重定向」，worker 宁可写 `commit_via_python.py` 也不敢 commit。
先修约束矛盾；修不干净就上守卫：worker 退出 0 但无提交时由派单器代提交。

**改完派单参数，只有「改动之后新起的 worker」才生效。** 已经在跑的 `claude.exe` 继承的是旧命令行，
会继续报「无 Bash / 无法自行提交」。判断补丁是否生效看**开工时间**：卡 `started_at` 早于改动时间，
就忽略它的自述，等新一批 worker 再判 —— 否则会把「旧进程」误判成「补丁无效」而反复重改同一处。
同一逻辑适用于任何派单层改动：过渡期里两种行为并存是正常的，不是没修好。

### 代提交必须按时间过滤，否则会偷走别人的活

```bash
# 派单开始时打时间戳
RUN_MARKER="${TMPDIR:-/tmp}/wf_run_${TASK_ID}_$$.marker"; : > "$RUN_MARKER"
# 代提交时只收本次之后变化的文件
[ ! "$REPO/$p" -nt "$RUN_MARKER" ] && continue
```
**必须 `git status --porcelain -uall`**：未跟踪目录默认折叠成 `?? docs/_x/`，
时间检查会落在目录上，导致整目录（含其他 worker 的文件）被一起加进去。实测踩过。

### 🚨 代提交静默失效的头号原因：`core.quotepath` 把中文路径转义了

交付物基本带中文文件名（`docs/选品/xxx.md`），而 `git status` 默认
`core.quotepath=true`，输出的路径是 `"docs/\347\253..."` 这种八进制转义。
拿这个字符串去 `git add -- "$p"` → **路径不存在 → 失败 → 而且不报错**。

后果是最阴的那种：代提交什么都没做、也不出声，worker 又只在总结里写一句
「提交 git commit（提交信息带卡号）完成交付」**而实际没执行**，两边都没有提交，
验收只能判「疑似假 done」。实测一整个下午的卡都是这么挂的。

```bash
# ✗ 中文路径会变成 "docs/\347\253\226..."
git status --porcelain -uall
# ✓ 输出原样中文，git add 才能命中
git -C "$REPO" -c core.quotepath=false status --porcelain -uall
```

**并且所有「提前返回」都要出声。** 原来的 `[ -z "$paths" ] && return 0` 让人完全看不出
是哪种跳过；改成分支打日志：`exit!=0` 不代提交、`paths` 为空、暂存区无差异 三种情形各一行。
**代提交函数写完必须造样本实测，三个方向都测**：中文路径的交付物能入袋、旧文件被时间过滤排除、
垃圾脚本不入袋。只测「没报错」等于没测。

### 测 `dispatch_claude.sh` 里的函数：抽出来跑，不要只看代码

脚本是一整个 main 流程，改完无法整体回归。做法是把目标函数用 `awk` 从函数头切到 `}`，
source 进一个 harness 单独跑（临时文件写原生路径，别写 MSYS 的 `/tmp`）：

```bash
awk '/^auto_commit_produced\(\)/,/^}/' dispatch_claude.sh > "$TMPDIR/fn.sh"
. "$TMPDIR/fn.sh"        # 再造 old.md / new.md / run_junk.py 三个样本，调函数验证
```

判据必须**三个方向都测**：旧的被排除、新的入袋、垃圾不入袋。只测「新的入袋」会把
「把整目录一起 add」这种误伤整个漏过去 —— 那正是这个函数最容易犯的错。

## 上游忽 500 时必须自动重试

长会话（单卡 10~20 分钟、几十次工具调用）里任一次 500 就整轮报废。用 while 循环
包住 agent 调用，命中 `500|503|overloaded|Stream ended` 且非最后一次就等 20s 重试，
默认 5 次。实测重试日志能救回（`瞬时错误 → 20s 后重试`），直连 5 连测成功率 4/5。

## 环境守卫：worker 会破坏什么

三个实测发生过的破坏，都要自动兼底（cron 每 10 分钟，正常时完全静默）：
1. **追加型文件被整个覆盖** — `操作日志.log` 1338 行 → 17 行。留快照，行数掉到 80% 以下就用快照恢复并把新增行补回去。
2. **追加型文件被整个删除** — 同一天里 `项目状态.md` 与 `运维手册.md` 被直接删掉。
   只判「行数变少」的实现遇到文件不存在会 `continue` 跳过，于是**两个最核心的文档消失了却没有任何告警**。
   必顶：`if not exists(path)` 分支里从快照 `copy2` 恢复，并把这两份文件加进 `APPEND_ONLY`。
   验收方式是故障注入：`rm` 掉文件 → 跑守卫 → 行数与原文件一致。
3. **仓库里堆一次性脚本** — 一上午 199 个，八小时无人值守后回潮到 803 个。
   扫描时**不能靠 `git status`**：`.gitignore` 一旦挡住这些模式，它们就不在 status 里了（实测漏过一批）。
   要直接扫磁盘 + `git ls-files` 排除已跟踪文件。

**别用名字模式滤垃圾 —— 永远追不上。** 实测一个上午就换了三轮：`run_*` → `run*` →
`commit_*` / `compute_*` / `gen_*` / `append_*` / `bash_git.py` / `cc.py` / `tmp_exec_execute_git.py`，
每补一批规则又冒出一批新的；八小时下来仍是 1751 个。**改成结构性判据，按目录定规则：**

| 路径 | 规则 | 依据 |
|---|---|---|
| 仓库根 | **未跟踪即垃圾**（`STRUCTURAL_DIRS[""] = None`）| 根的合法文件全部已入库 |
| `scripts/` | 未跟踪即垃圾，**除非** `^cs_` | 业务脚本按约定带了前缀；其余是临时物 |
| `src/roles/*/scripts/`、`src/roles/*/tmp_*` | **未跟踪即垃圾** | 角色临时工作区；正式产物按 AGENTS.md 进 `docs/` 或 `output/` |
| `docs/` `data/` `output/` | **不动**（只按名字模式清明显的桩）| 这里是真交付物 |

两个必守的前提：① 只处理**未跟踪**文件（`git ls-files` 排除已跟踪），否则会删掉历史；
② 移入隔离区而非 `rm`，可回滚。**判据只有一条** —— 扫完 `git status --porcelain -uall | wc -l` 必须为 0，
非零就继续补规则，不许收工。

**别拿「正在跑的 worker」当借口放过。** 刚落盘的文件有 10 分钟冷却（防止写一半被搬走），
所以守卫跑完仍会剩几个 `run_*.json` —— 那是**当前这一轮**新写的，不是规则又漏了。
区分方法：看 `mtime`。旧的就该被清掉；新的（<10 分钟）下一轮会自动清。

## 卡面正文 vs 交付纪律：必须消毒，否则卡必死

卡片正文是给人看的工单，常写着「任务保持未完成状态（不要标记 done）」
「不得把本卡标记 done」「本卡不执行、不改任何其他文件」——这些是**范围约束**，
但 worker 会理解成「别提交、别标完成」，而派单器强加的交付纪律要求必须 commit
并进 review。**两条直接打架，worker 照卡面做就必然被验收打回，打到上限归档。**

实测：10 张业务卡就是这么死的（每张都是打回 8 次后归档）。

修法（两侧都做）：
1. **源头消毒**：注入提示词前割掉冲突短语，交付纪律开头写明
   「本节优先于卡片正文中的任何相反表述」。
2. **存量修正**：直接改 DB 里的 body，删掉那几句。

消毒的三条铁律（都是踩出来的）：
- **只割短语，不整行删**。整行删会把「创建 XX 文档」这种真目标一起抹掉。
- **不动合法范围约束**：「本卡不执行该脚本」「不得创建其他文件」「其他文件只读」
  都是正当要求，删了等于放开 worker 的手脚。
- **用 Python 不要用 sed**。MSYS 的 sed 按字节走，会切坏多字节中文——
  实测把「五小节齐全。」切成「五小节齐全�。��」。

### 复活归档卡之前，先复位打回计数

验收器用历史事件数打回次数（`changes_requested` + `review_reopened`）。
归档时的 8 次历史会跟着卡一起复活 → **首次不合格立刻又归档**，复活等于白做。
复活时插一条 `unarchived` 事件，计数只数「最近一次复活之后」的：
```python
cut = max([int(e["created_at"] or 0) for e in events if e["kind"]=="unarchived"] or [0])
return sum(1 for e in events if e["kind"] in ("changes_requested","review_reopened")
           and int(e["created_at"] or 0) > cut)
```

### 回收僵死的 running 卡

worker 死了但状态还挂在 `running` 会占满并发槽，新卡永远派不出去。
`worker_pid` 可能是 NULL 用不了，改看 `logs/workers/<tid>.out` 的 mtime：
超过 10 分钟没输出就改回 `ready` 并插 `reclaimed` 事件。

## 回答「我要办的事一件没办成」：六个数定性整条流水线

用户抱怨「一堆定时任务，但想办的事一件没办成」时，**不要逐项解释配置，直接算这六个数**。
全部只读、几分钟出结论，任何一个异常都足以定案：

| # | 指标 | 算法 | 健康线 | 实测反例 |
|---|---|---|---|---|
| 1 | **成卡率** | `done 卡数 / 被 claim 过的卡数` | >40% | 31/278 = **11.2%**（近九成派单白烧） |
| 2 | **打回率** | `review_reopened + changes_requested / review 相关请求数` | <30% | **95%**（130 次请求被重开 124 次） |
| 3 | **协调者越界率** | `done 卡里 assignee=default / 全部 done` | ≈0 | **48%**（铁律 1 名存实亡） |
| 4 | **cron 业务占比** | `业务类 job / 全部 job` | >0 | **0/10**（全是维护机器） |
| 5 | **提交用途比** | `git log --since=1day` 按「修机器 / 做业务」分类 | 业务 >50% | 修机器 **55%** / 业务 **11%** |
| 6 | **可售交付物数** | 真实可交付物（zip / 资源包 / SKU 包），不是 md | ≥1 | **0**（248 个文件，0 个能卖） |

第 6 条是终局判据：**其他五个数好看但这条是 0，就是没办成。** 反之第 6 条非 0 时，
前五条差也只是效率问题，不是方向问题。

```sql
-- 1、2、3 一次查完（看板库是唯一真相，别用日志估；表结构见 references/board-forensics.md）
SELECT (SELECT COUNT(*) FROM tasks WHERE status='done')                                AS done_n,
       (SELECT COUNT(DISTINCT task_id) FROM task_events WHERE kind='claimed')          AS claimed_n,
       (SELECT COUNT(*) FROM task_events WHERE kind IN ('review_reopened','changes_requested')) AS rej,
       (SELECT COUNT(*) FROM tasks WHERE status='done' AND assignee='default')         AS done_by_human;
```

```bash
# 4：两类分开数，别只数总数就下结论
hermes cron list | grep -cE '巡检|看门狗|验收|派单|测速|蒸馏'   # 机器维护类
hermes cron list | grep -c .                                    # 总数 → 差值 = 业务类
```

**别把「流水线在跑」当成「业务在产出」。** 哨兵 rc=0、日志每分钟一行、看板有 ready 卡，
这三件事都能在零产出时同时成立（闸门常红、卡全在 todo、worker 空转）。

### 一条业务链超过 2 跳，就等于不会交付

实测：一个「选品 → 策划 → 制作 → 上架」的目标被拆成 5 层、10+ 张微卡串行，整条链躺 22.4 小时、
0 次尝试；而它需要的原始素材（12 SKU 候选清单、253 件真实商品、39 条证据）**早就做完了**，
只是卡在链首那张 `todo` 上没被收口。

- **业务链深度 ≤ 2 跳**（生产 → 交付）。第 3 跳起，每多一跳就多一个「上游永不 done」的阻塞点，
  而 `todo` 不在候选池，哨兵根本看不见它，也不会告警。
- 已经做完的产出**立刻收口**（判 done 或归档），不要留着等新素材 —— 它会把整棵树拖住。
- 拆卡前先问：能不能一张卡 + 一个明确交付物做完？能，就别拆。

### 偏差审计：先查「这个概念在参考框架里存不存在」

对标原版框架做偏差评估时，最容易漏的是**我们自加了什么**。方法只有一步：
**拿这个机制的关键词去 grep 权威文档**。

实测：`grep -iE 'RPM|速率|限流|throttle' 迁移手册` = **0 处命中** —— 派单闸门、限流代理、巡检卡
这三样原框架根本没有，全是自造的。**自造层是偏差的主要来源**：它们不是「框架没搭好」，
而是「在框架外面又加了一层」，并以看不见的方式与框架自己的循环打架（闸门挡死派单、
巡检抢并发位、代理放大重试）。

评估顺序四段，每段都给数、不要给形容词：

1. 三层（协调 / 任务 / 执行）完成度
2. 五铁律逐条打分
3. **自造层清单** —— 框架里没有的东西 + 它实际造成的后果（这一节往往才是用户问题的真答案）
4. 缺失层 —— 框架有而我们没有的（多网关、冷热记忆、真实交付物）

**由此推出一条选型原则：用户要「通用型架构」时，优先评估现成的上游项目，不要把本地这套清洗成通用。**
本地实例的价值几乎全在项目特定的补丁上（速率闸门、巡检卡、角色文件域），而这些恰恰就是上面第 3 段列出的
自造层 —— 拿它们去通用化，等于把已经证明会与框架打架的东西复制进新项目。要通用就换一个干净骨架，
本地经验只用来**验收新骨架**，不要整段搬迁。评估候选项目看**四样，第 0 样是硬门槛**：

0. **能不能在目标平台跑起来** —— 见下节。**这一条不先做，后面三条全是白算**：平台不通时，角色链再漂亮也一行都跑不起来。
1. 入口是不是用户要的那个（会话 / Issue / webhook）
2. 执行层是否可插拔地接外部 agent
3. 有没有人工门禁

产出物是方案文档时按 `plan` 技能的「决策型方案文档」一节写，且不执行任何安装动作。

### 🚨 选型第一步：平台可运行性体检（先于安装、先于写方案）

**README 里没写「不支持」不等于支持。** 「从头到尾不提 Windows + 模块顶层 `import fcntl` + 安装段只有 `brew install`」
三条同时成立 ⇒ 它是 Unix-only。把「文档说支持、实测为准」写进方案，等于把未验证的假设当结论交上去，
用户会在你装到一半时叫停。**先跑机械体检，再决定要不要写方案。**

```bash
cd <候选仓库>
# ① 平台声明：frontmatter 的 platforms、README 有没有提 Windows
grep -rn "^platforms:" --include=SKILL.md . ; grep -in "windows\|win32" README*.md
# ② Unix-only 模块（命中且无非-posix 等价分支 ⇒ 本机不可用）
grep -rnE "^import (fcntl|pwd|grp|termios|tty|resource)\b" --include=*.py . | grep -v /tests/
# ③ 外部二进制耦合度：tmux / ttyd / screen 在 Windows 没有原生对应物
grep -rlc "tmux" --include=*.py .   # 涉及文件数
grep -c  "tmux" core.py             # 单文件次数：个位数可适配，几十上百次是架构核心，只能换项目
# ④ 作者有没有考虑过别的平台（有分支也要回头看 ② 的顶层 import 是否已拦死）
grep -rn "os.name == 'posix'\|sys.platform" --include=*.py . | grep -v /tests/
```

**「纯 skill 包」和「带 runtime 的插件」是两类东西**：前者只有 markdown 剧本，平台无关；
后者要常驻进程 / 终端复用器 / Web 终端，天然绑 Unix。**目标机是 Windows 时，默认先看纯 skill 类。**

已实测的候选结论、Windows 侧三项依赖怎么验、以及 `hermes config path` 返回的是文件不是目录这类安装期坑，
见 `references/orchestration-framework-selection.md`。

## Pitfalls

### ⛔ COORDINATOR MUST NOT WRITE BUSINESS CODE — EVER

**This is the single most violated rule in this workflow.** User's verbatim correction: **"为什么又自己修了？不下发到Claude code?"**

- **Any code change** (bug fix, one line, typo, config tweak) **must go through kanban → Claude Code worker**
- Coordinator role: create card → dispatch → verify independently → report. That's it.
- Self-fixing breaks the loop: no card trace, no acceptance record, no second pair of eyes, artifact unauditable.
- "Too slow to dispatch" is NOT an excuse — the user explicitly rejected this reasoning.
- Violation = severe dereliction. No exceptions.

---

- **bash 里调用尚未定义的函数是静默失败，会把告警吞掉。** 派单脚本在 `log()` 定义（位于文件后段）之前
  就调用了 `log`，实测只输出 `line 106: log: command not found`，那条「卡面含冲突表述已割除」的告警
  **一次都没打出来过**。辅助函数要么定义在文件最前，要么在调用点内联 `echo`；
  排查方法是比一比定义行号与调用行号的大小。
- **僵尸 running 卡永久占坑，哨兵只派 ready。** `kanban_auto_dispatch.py` 的 `board_tasks()` 只收 `ready/running`，把 `running` 视为占用并发位，但从不检查 worker 进程是否还活着。一张僵尸卡能永久占坑、永不重派 —— 表现为「空转几小时没反应」。
  **修法**：在 `tick()` 里加 `reclaim_stale()` —— running 卡若 pid 已死，或 worker 日志超 `WF_STALE_RUNNING_SECONDS`（默认 1800s）未更新，自动打回 ready 重派。双向实测：死 pid → 回收 ✅；活 pid → 不误杀 ✅。
- **假完成（文件有变化 ≠ 可用）是最大的后门。** `card_produce_check.py` 只看 `tree_fingerprint` 变化就给 `produced`。卡 4 单元测试因 pytest 从未装、测试全挂，却因文件变化被判有产出，一路带到交付。
  **修法**：新增 `_test_gate()` —— 带 `tests/` 的项目，必须真跑 pytest 且全绿才算有产出。可用 `WF_TEST_GATE=0` 关闭（仅限明确知道测试环境不可用时）。
- **测试/审查盲区覆盖不到真实 GUI 交互。** 单测只测 `engine.py` 纯函数，E2E 绕过 UI 直调引擎，审查只盯 `engine.py` → 31 处 lambda 裸调 `save_config`、`FilePicker` async 不 await、注册错位置全漏。
  **对策**：新增「GUI 冒烟测试卡」（`python main.py` 真起窗口、等 5s、查存活、查标题）、「交互测试卡」（pytest-qt/flet.testing 真点按钮、改滑块、验不报错），审查卡 body 强制逐文件过 `frontend/`、所有 lambda/导入/控件注册。
- **flet 1.0.4 破坏性变更（8 处）必须一次性全改，别靠重启试错。**
  `ft.app(target=main)` → `ft.run(main)`；`ft.Color(hex)` → 裸 hex 字符串；`Switch.label_style` → `label_text_style`；`Dropdown.on_change` → `on_select`；`ft.MaterialStateColor` → `ft.ControlState` dict；`ft.border.all` → `ft.Border.all`；控件 `.update()` 需 try/except 或 `_safe_update()` 统一吞；`FilePicker.get_directory_path()` 是 coroutine 需 await。
  **验证手段**：`check_flet_kwargs.py`（AST+反射签名）+ `mock_build_ui.py`（Mock Page 跑完整 build_ui）一次性抓全不兼容点。
- **flet 桌面客户端在 site-packages 外，裸 PyInstaller 收不到** → 打出来的 exe 换机器必崩。`flet pack` 是官方入口，会自动把 `~/.flet/client/flet-desktop-full-<ver>/` 整个带进单文件。`build/requirements.txt` 必须锁定到实测版本（flet==1.0.4 / flet-desktop==1.0.4 / Pillow==13.0.0），附不可降级注释。
- **PyInstaller 单文件模式下 `__file__` 指向临时目录**，配置若跟着写进去，每次重启都丢、用户也改不到。
  **修法**：`_runtime_root()` 返回 `sys.executable.parent`（frozen 时）或 `__file__.parents[1]`（源码时），`CONFIG_PATH = _runtime_root() / "config.json"`。
- **GUI 启动测试必须纳入 `_test_gate()`**，否则 "文件有变化 + 测试全绿" 仍可能漏掉 "exe 起不来 / 窗口标题不对 / FilePicker 不弹" 这类阻断级 bug。
- **FilePicker 在 flet 1.x 的正确注册模式**：
  ```python
  async def pick_src_dir(e):
      fp = ft.FilePicker(on_result=on_result)
      page.services.append(fp)          # 不是 page.file_picker =、不是 page.overlay
      await fp.get_directory_path(...)  # 必须 await
  ```
  三错并发：`page.file_picker` 属性不存在、`page.overlay` 非注册位、协程不 await → `Unknown control: FilePicker` + 对话框不弹。
- **`save_config` 必须模块级导入**：`ui.py` 顶部 `from backend.config import AppConfig, save_config`。文件内 31 处 lambda 裸调 `save_config(cfg)`，仅靠函数内局部 import 撑不住 lambda 闭包 → 任何滑块/开关一动就 `NameError: save_config`。
- **Worker 方向性错误（方案本身是废的）是最贵的失效**——文件存在、测试能过、日志显示完成，但产物换机器就是废的（裸 PyInstaller 漏 38MB flet 客户端、flet==0.21.2 降级炸弹、frozen 态配置写临时目录）。对策：协调层必须独立验证真实路径，不采信任何自述。
- **目录扫描不递归**：`Path.iterdir()` 只扫顶层，子目录图片全漏。必须用 `Path.rglob("*")` 或 `os.walk` 递归扫描，并配合 `f.suffix.lower() in valid_exts` 过滤。这是典型的 "代码写了、单测能过、真实目录却找不到文件" 的阻断级 bug。
- **协调者越权直接修代码（工作流纪律铁律）**：用户明确纠正——「不 走Claude ？自己改啊？」。**任何业务代码修改（哪怕只是修一个 bug、改一行）必须走看板派单给 Claude Code 子员工，协调层绝不直接写源码**。直接改代码会破坏工作流闭环：没卡追踪、没验收记录、没第二双眼睛、产物不可审计。哪怕觉得「这点小事派单太慢」，也要建卡、派单、等 worker 完成、验收。这是用户立下的硬规则，违反即视为严重失职。
- **交付包同步缺失**：worker 在项目目录修复代码通过测试，但协调者未将变更同步到交付包目录（`img_batch_tool/`）并重新打包，导致用户跑旧 exe 仍复现已修复的 bug。修正流程：项目目录测试通过 → 同步源码到交付包 → 重新 `flet pack` → 同步 exe 与配置 → 交付包内再次真跑验证。

---

## 关联参考文档

- `references/flet-1.0.4-breaking-changes.md` — flet 1.0.4 破坏性变更速查表 + 迁移清单 + 验证脚本
- `references/pyinstaller-frozen-path-anchor.md` — PyInstaller 单文件模式路径锚定模式（`_runtime_root()`）
- `references/test-gate-zombie-reclaim.md` — 产出校验测试闸门（`_test_gate()`）+ 僵尸卡回收（`reclaim_stale()`）+ GUI 冒烟/交互测试模板
- **交付物真实，但「叙述里的数字」来自另一次运行 —— 这是本周最贵的打回形态。** 实测：同一张探测卡被派 4 轮；产物（`docs/**/_probe.md`）来自第 3 次运行，而 worker 在卡片评论和 `操作日志.log` 里手抄的是第 1 次的数字（18582 文件 / 370.86MB vs 18606 / 376.60MB）。两组数各自真实，配对关系被打散，reviewer 只能打回。判据不是「数对不对」，而是「数能不能在产物里按行号找到」。修复：先追加一条规则级订正（不改写历史行），再重跑一次让产物与叙述同源。构造与复核的完整工法见 `evidence-backed-deliverables`。
- **`-q` worker 的证据捕获会掉进 `/tmp`。** 用 `> "$TMPDIR/stdout.txt"` 成功后，`read_file` 读同一个文件会报 `File not found`（MSYS 的 `/tmp` 与原生工具解析的不是同一处）。证据一律写到显式原生路径。被 `-e/-c`、heredoc、`execute_code` 拦下的替代方案见 `unattended-agent-execution`。
- **`kanban.dispatch_profiles: []` 是让 Hermes 彻底退出执行层的唯一开关。** 不设它时，`assignee=default` 的卡会被 Hermes 网关 dispatcher 抓走，用 `hermes_cli.main ... work kanban task <id>` 直接执行 —— 绕开 Claude Code、也绕开验收关（跑完自己 complete）。症状就是用户说的「所有活都是 Hermes 干了，还不走审批」。设成空列表是 fail-closed：本机网关一张卡都不认领，全部落进 `skipped_nonspawnable`。用 `hermes config set kanban.dispatch_profiles '[]'` 改，别手改 YAML。
  **实测验证法**：建一张 `assignee=default` 的测试卡，等 3 分钟 —— `spawned` 计数不增、每 tick 都是 `skipped_nonspawnable`、卡停在 `ready`，才算真挡住了。不实测就宣称「已关闭」等于没做。
  **注意**：`skipped_nonspawnable` 同时也会记录 cc-* 卡（网关天生不认它们），所以这个计数大不代表故障，要看 `spawned` 有没有增。

- **拆子卡会把 assignee 写成 `default`，连根卡都可能被重置。** 事件实证：`decomposed {"child_ids":[...], "root_assignee":"default"}`。这些卡派单器（只收 `cc-` 前缀）永远不派 → 不 done → 子卡全部锁死。修法是派单器每个 tick 先跑 `kanban_role_assigner.repair()` 按标题关键词修回角色。
  **匹配必须标题优先、正文兜底**：正文常抄了别的卡的上下文，实测会把「SKU 清单与交付规格」误判成竞品分析（因为正文里出现了「定价」）。直接 `title + body` 一起正则 = 必然误判。

- **cron 里任何“标记一次”的动作必须幂等，否则会刷屏。** 验收审计每 2 分钟扫最近 90 分钟的 done 卡，不去重的话同一张卡会被评论几十次、而且 cron 的 stdout 会直接投递给用户形成骚扰（实测：8 张卡被灌了 4 轮，共 24 条重复评论）。模式：先查评论表里是否已有标记行（`SELECT COUNT(*) FROM task_comments WHERE task_id=? AND body LIKE ?`），**只对“还没留过痕”的新增违规输出并写库，无新增则静默 return**。修完必须实测幂等：复跑一次，stdout 为空、表里行数不增，才算好了。

- **验收关要能自动发现“绕过”。** 合法完成只有两条：进过 `review`（有 `review*` 事件），或 worker 显式写 `result` 带 `unreviewed=1`。两者都没有 = 绕过。验收 cron 里加一个 `audit_review_gate()`（扫最近 90 分钟的 done 卡）比事后人工翻账有用。

- **HTTP 500 与 503/504 必须分开查。** 实测：272 条 HTTP 500 记录中 **100% 是 `is_streaming=0`（非流式）**；330 条 504 **100% 是流式超时**。A/B 对照（同一模型同一条消息，只改 stream）：非流式 6/6 全 503，流式 6/6 全 200。所以看到成片 500 时，先看 `is_streaming` 字段，不要先归因到「模型挂了」或「配置错了」。不要拿一个错误码去解释另一个错误码 —— 先测。

- **`claude-haiku-5-5` / `claude-sonnet-5` / `claude-opus-5` / `claude-fable-5` 不是模型，是 Claude Code 内置档位代号。** 直连上游全部 404，必须由 cc-switch 映射。日志里 `0 0 — $0.0000` 的行是**失败请求的记账行**（无 token 产出），不是免费调用。测速时不能用这些代号（上游不存在），要用真实模型 ID。

- **改执行器环境变量前必须做「三次完整调用」对照，量的是调用成功率，不是单次请求的状态码。**
  一次单请求的 200 会骗人：同一个开关下，一次能成功、下一次可能 `Stream ended without receiving any events`。
  可用的判据只有多轮真调用后的成功比（例：同一开关关 0/3、开 3/3 才算定论）。
  测完发现有害就**立即撤销三处**：派单脚本的 `export`、Windows 用户级变量、cc-switch 的 provider env，
  并在代码注释里写「绝不可加 + 实测依据」—— 否则下一个人（或下一个自己）会重新把它加回去。
  另注：用「重试次数归零 / 关掉非必要流量」这类看起来更干净的开关时，先问一句它抬掉的是不是**唯一兜底路径**。

- **`assignee` 不以 `cc-` 开头 = 整条依赖链死锁，而且全绿无声。** 派单器只收 `assignee` 以 `WF_AGENT_PREFIX` 开头的卡（`kanban_auto_dispatch.py:140`）。一张 `assignee=default` 的**根卡**永远派不出去 → 它永远不 `done` → 所有子卡永远停在 `todo`（`todo` 不在候选池）→ `ready` 队列为空 → 哨兵每分钟 `tick rc=0`、`dispatch.log` 一行不写、没有任何报错。表面症状是「系统没反应了」，实际是**一张写错 assignee 的根卡锁死了整棵树**。
  真实事故：R7-A1 根卡 `assignee=default`，卡住 A2→A4→A5 三级；同时 `t_72df2639` 的 3 个父卡也是 `default`。
  排查顺序（三步，别跳）：① `list --status ready` **为空** ⇒ 不是并发满，是没卡可派；② 查所有 `todo` 卡的 `assignee` 前缀，`default` 的就是病灶；③ `promote --dry-run` 会直接报出未满足的父卡，比 `show` 逐张翻快得多。
  修复：改 `assignee` 到真实 `cc-*` 角色（`UPDATE tasks SET assignee=? WHERE id=?`，`tasks` 表**没有 `updated_at` 列**）。改完它们会在下一 tick 自动被派 —— 实测 06:20:39 立刻派出两张。
  另一个连带事实：`assignee=default` 的卡会被 **Hermes 网关 dispatcher** 抓去用 `hermes_cli.main ... work kanban task <id>` 执行 —— 那就是「Hermes 沦为执行层」的实际入口。

- **直接 `UPDATE tasks SET status=...` 会断审计链。** 事件流是看板唯一的「谁在什么时候改了什么」记录，
  走 CLI（`archive` / `block` / `complete` / `reclaim`）才写 `task_events`。实测一次批量归档后
  `tasks.status='archived'` 有 71 张而同名事件只有 42 条 —— **29 张卡的变更无迹可查**，
  用户问「这些卡哪来的、谁归档的」时答不上来。批量动作优先走 CLI 循环；非写库不可时，
  同事务里补一条对应 `kind` 的事件行，并在报告里写清改了几张、依据是什么。
- **看板「阶段」存在不代表它在运行。** 状态机 / CLI / 列名三者齐备，链路仍可能根本没人调。
  判据只有一个：`task_events` 里有没有对应 `kind` 的行（数量为 0 = 从没跑过）。
  同样地，**已有的一道闸是否有效，要数它的判定分布**（produced / EMPTY / skip 各多少次），
  而不是看代码里写了 if 分支 —— 一个永远走 skip 分支的闸和没有闸等价。
- **Two sentinels, one board → 抢单.** Adding a board must add an isolated install dir (or `--force` + remove the old cron). Never leave two jobs reading the same `config.env`.
- **`install.sh` preserves `config.env`**, so a new `--board` — or `--repo`, or any other key — on an existing dir is silently ignored while the banner still echoes the value you passed. Use `--dir` or `--force`, and always read the written keys back instead of trusting the banner.
- **Space-separated `--allowedTools` → fake done.** Comma-separate it; the symptom is a worker that exits 0 having done nothing.
- **Zero output → `blocked`, not `done`.** The dispatch wrapper already enforces this; do not "helpfully" mark such cards done.
- **Verify-type keywords match the card TITLE only.** Matching the body misclassifies fix cards (their bodies naturally contain 验收/只读) and lets zero-output through. **And the exemption is void once the card declares deliverables** — a card titled `…巡检机制` that lists four artifacts must still produce a card-numbered commit. Implement as `verify_only = verify_only and not parse_artifacts(body)`, falling back to the file-domain list when there is no 交付物 section. Without it, a legitimately-named build card (e.g. one whose title ends in 「巡检机制」 but whose body declares a SOP, a 话术库 and a patrol script) is waived despite four real files on disk and **zero** commits — the files only survive because someone later noticed and force-committed them.
- **Know the produce-check fingerprint's two blind spots.** It is `md5(sorted(git status --porcelain))` + `HEAD` (keep **one** implementation — a bash-side `git status | md5sum` disagrees on CRLF/LF and then always reports "produced"). (a) It **collapses a wholly-untracked directory to one `?? dir/` line**, so writes inside it change nothing → `verdict=EMPTY 零产出` false-blocks real work into `triage`; commit the scaffold to fix it. (b) When it blocks a card, **verify the files yourself** before believing it — a false block discards a worker's entire output and strands the card where the CLI cannot recover it.
- **A timestamp gap in `logs/tick.log` means the host slept**, not that the script broke. Check the log's continuity before debugging the card.
- **`python3` on Windows may be a Microsoft Store stub** — it resolves via `command -v` but fails on execution. Always prove python by running `python -c "import sys"`; set `WF_PYTHON` to an absolute path when needed.
- **The sentinel runs from cron, which does not inherit the user's environment variables — and both failures look like something else.** (a) `claude: command not found` / dispatch `exit=127` / card instantly blocked: the user's `PATH` never reaches cron, so pin the binary with `WF_CLAUDE=<absolute path>` and resolve it instead of calling a bare `claude`. (b) `--agent '<name>' not found` with an "Available agents" list equal to the **fallback** config dir's files plus Claude Code's built-ins (`claude`, `Explore`, `Plan`, `general-purpose`, …): `CLAUDE_CONFIG_DIR` didn't reach cron, so Claude Code fell back to `~/.claude/agents` and every agent you created is invisible. Pin it with `WF_CLAUDE_CONFIG_DIR` and `export CLAUDE_CONFIG_DIR` in the dispatch script. Confirm (b) by arithmetic — *available == fallback-dir files + built-ins* — and by `env -u CLAUDE_CONFIG_DIR claude --agent <name> …`, which reproduces it instantly. Put both pins in `config.env` (survives reinstall); the dispatch-script half is overwritten by a reinstall, so mark those blocks with a comment.
- **`triage` is a one-way door through the CLI.** A card escalates there after repeated block→unblock loops — commonly a produce-check false block. `promote` refuses it (only `todo`/`blocked`), as do `unblock`, `schedule` and `complete`; `specify`, the designed exit, makes an **LLM call** and fails outright when that call is denied. Recover with `archive` + recreate from the saved body file (another reason to create cards via `--body-file`). **Exception, with explicit user authorization only**: a card that genuinely *did* produce verified work can be renamed in place by writing `kanban.db` directly — but a DONE card leaves traces in **four** places, and setting only `tasks.status` leaves silent internal inconsistency. Mirror all four 1:1 from an existing DONE card: (1) `tasks` — `status`/`completed_at`/`result`/`consecutive_failures=0`; (2) the latest `task_runs` row — `status`/`ended_at`/`outcome='completed'`/`summary`; (3) a new `task_events` row with `kind='completed'` and the matching `run_id`; (4) Unix **epoch seconds** for all timestamps. Back up **first** (`kanban.db.bak-before-<reason>-<stamp>`), then `hermes kanban --board <slug> repair` must report `integrity_check ok — no repair needed`.
- **Never accept a worker's claim about its own toolset.** Workers on a fast/weak model have reported "this session has no Bash/Shell" — listing exactly their configured tools minus `Bash` — while the same invocation, re-run by the coordinator, had Bash and ran shell commands fine. The damage is silent: files still land through the file tools so the card passes the produce-check, but nothing is ever committed and no acceptance command is ever run. Put an explicit "you have Bash — run git/ls/python directly, do not assume you lack a shell" line in every role's 完成须知, and settle a dispute by re-running the invocation yourself.
- **`-q` 是 Hermes 的 flag，不是 `claude.exe` 的。** 直接 `claude -q "..."` 报 `error: unknown option '-q'`。
  手工复现 worker 调用必须照包装脚本的真实形态：
  `claude --agent <name> --model <real-model> --allowedTools Bash,Read,... -p "<prompt>"`。
  形态抄错会把「参数错误」误诊成「链路不通」，白花一轮探测。
- **超长/不可解析的 inline 命令会被硬拦（不是权限问题）。** 一次塞进过多命令或多段 heredoc，
  会拿到 `BLOCKED (hardline): command parser limit or malformed executable payload` —— 这条**绕不过去**
  （`--yolo`、`approvals.mode=off` 都无效），但**不是操作本身被拒**。命令已被保存到
  `<hermes_home>/cache/blocked-scripts/blocked-*.sh`，按提示 `bash <那个路径>` 即可执行。
  对策：**多步探测一律先 Write 成 .sh 再 `bash <file>`**，别写成巨型 one-liner。
- **Path form matters**: pass forward-slash native paths (`D:/x`) to native tools; the scripts' `native_path()` normalizes MSYS forms on read, but writes from bash must not emit `/d/x`. This bites hardest on the **executable path itself**, not just arguments: a helper Python script that shells out to the `hermes` CLI must hold `D:/.../venv/Scripts/hermes.exe` (native, with `.exe`); an MSYS `/d/...` value makes  `subprocess` die with `FileNotFoundError [WinError 2] 系统找不到指定的文件` before the CLI ever runs.
- **Windows 上 worker 跑裸 `python` 会把整轮烧在 `_pyrepl` 崩溃循环里。** Python 3.13+ 的新交互式 REPL
  在**没有真实控制台**的派单环境里仍去查终端尺寸，每行抛
  `OSError: [WinError 123] 文件名、目录名或卷标语法不正确`，无限刷 traceback ——
  实测整轮 30 分钟耗尽、交付物一行没写，而日志看起来「一直在输出」。
  派单脚本里 `export PYTHON_BASIC_REPL=1` 让裸 `python` 退回基础 REPL。
  顺带 `export PYTHONUNBUFFERED=1`：僵尸判活靠 worker 日志的 **mtime**，输出被缓冲时 mtime 会骗人。
- **完成事件的 `summary` 是 worker 自述，字数能出卖它。** 实测一批 `done` 卡的完成事件正文只有
  `{"result_len": 6, "summary": "子员工(cc-xxx) 完成"}` —— 6 个字符；而同卡 `task_runs` 里**第一次** run 的
  结局是 `outcome=blocked` + `exit=127`（模型名不被识别）。**「先崩一次、再跑一次就算完成」
  = 中间没有任何东西干过活。** 审计 done 卡时把 `task_runs` 的 outcome 序列与 `summary` 长度一起看，
  比只看状态列快得多，也比读日志便宜。

## User working preference (embed, do not relearn)

- **Land the infrastructure config first, then stop and report.** Do not slide from "set up the workflow" into building the workflow (agents, source code, cards) unprompted. A new window must not start with the agent doing things on its own. Correct sequence: install/configure → verify → report state + the open decisions → wait for direction.
- Report in **direct Chinese, no fluff**, and only claim what was actually verified (quote the real command output).
- **When the user asks for a 运行日志 write-up, answer their fixed questions in order and keep the section headings:** 这一轮做了什么 / 为什么这么做 / 得到了什么结果 / 踩了哪些坑 / 用户的需求（引原话）/ 做之前的方案 / 方案实施情况 / 下一步 / 在原版基础上改了哪些 / 主线任务外做了什么及必要性. Default location `C:\Users\Administrator\Desktop\运行日志\<主题>-<版本>.txt`. Write plain text with real command output, and keep explicit 「尚缺」/「未验证」 sections — a log that only lists successes reads as incomplete and will be sent back.
- **完成度要按层给，不要给一个笼统的百分比。** 「安装层 100% / 业务链路 0%」比「约 75%」有用得多：前者直接指出下一步该接哪根线，后者只让人以为快好了。
- Keep the project root's `项目状态.md` and `操作日志.log` current: record every requirement, completion, and operation, appending rather than overwriting.
- When the user names a decision the setup cannot resolve alone (agent roster, `WF_AGENT_DIRS`, repo layout), surface it as an explicit open question instead of inventing an answer.
- **「把环境维护好」是交付标准，不是补充说明。** 修完一轮必须跑完整自检并报**真实数字**：全部脚本
  `py_compile` / `bash -n` 通过、守卫在干净时静默、仓库 `git status` 为 0、看板各状态计数、在跑 worker 数。
  没跑自检就宣布「已修好」= 用户睡不安心。同样禁止「解决一个结果又带出一堆错」：一轮只改一类问题，
  先定位根因再动手，不要边猜边改；发现 A 的修法会波及 B，先停下来想清楚，不要先改完再收拾。
- **清理要果断，但先分清「真工作」和「垃圾」。** 用户授权「该删就删」不等于可以无差别 `checkout`。
  提交尝试桩、一次性脚本 → 移出（隔离区留档而非 `rm`）；worker 写出来但没提交的实质产出 → 先入库保住。
- **听到「先别做了 / 你越修越错」＝ 立刻切成只读，先出「设计要求 vs 现状」对照报告。** 顺序不能颠倒：
  ① 停止一切写操作（包括「顺手修一下」）；② 读**原始权威文档**（桌面框架目录下的迁移手册 / 看板机制说明书 /
  使用方法.txt），**不要**从自己的记忆或上一轮摘要里复述设计；③ 逐项给表：**设计要求 / 现状（带实测证据）/ 判定**；
  ④ 单列一节「我改了什么」（含未经批准的改动）；⑤ 结尾只给「需要你定的 N 件事」，不附方案。
  用户说「我要一样一样对」时用编号对齐，不要散文；这一轮**报告本身就是交付物**，不要再动手改东西。
- **换宿主是用户的决定，不是你为绕过阻塞可以自选的手段。** 目标平台跑不起来时的正确动作是
  **停下 → 报阻塞 → 给选项**；不要「既然 Windows 缺 tmux，那就去 WSL 里跑」。宿主一换，入口、看板、
  配置目录全跟着搬，用户会当场问「你跑 WSL 去弄了？」—— 他给的是「在这台机器上落地」，不是「随便找台机器跑通」。
  同一条约束适用于换容器、换 Python 解释器、换 Hermes profile。
- **破坏性批量操作必须先问。** 归档一批卡、删除产出目录、收紧验收判据 —— 这些改变的是**已有事实**，不是「修 bug」。
  自由度全开 ≠ 可以让已有卡片/文件消失或降级：凡涉及此类动作，先列清单 → 问 → 等答复。
- **偏离原设计要单独标注，不要悄悄收紧。** 把手册明写「验证型卡零产出 → done（不误伤）
- **GUI 启动测试必须纳入 `_test_gate()`**，否则 "文件有变化 + 测试全绿" 仍可能漏掉 "exe 起不来 / 窗口标题不对 / FilePicker 不弹" 这类阻断级 bug」的判据改成
  「声明了交付物就必须提交」是一次**偏离**，可以改，但必须在报告里单列并说明理由 ——
  否则用户核对时会把「按手册实现」和「按自己想法实现」混为一谈。
- **别用「清理残渣」的名字做实质性的结构删除。** 一次批量归档/删除如果不留痕、不报告数量，
  事后无法回答「这些卡哪来的、谁归档的」；用户对这类动作的容忍度远低于对代码修复的容忍度。
- **回退只限 Hermes 侧，绝不碰 Claude Code 环境。** 用户会明说「不要破坏我 claude code 的环境」——
  `$CLAUDE_CONFIG_DIR` 下的 `agents/` / `settings.json` / `cc-switch.db` / cc-switch 代理及其守护 cron
  一律只读不动。可回退的三面：看板库、`scripts/hermes-wf-<board>/`（自己就是 git 仓库）、业务仓库。
- **回退顺序不能颠倒：先停写者，再恢复。** 派单哨兵每分钟写库，不先 `hermes cron pause` 掉它，
  恢复出来的库 60 秒内就被写回去 —— 症状是「`cp` 成功且退出 0，但 `kanban list` 还是新数据」。
  停三个流水线 job（哨兵 / 受阻恢复 / 验收），**不要**停 cc-switch 守护与限流看门狗（那是模型链路）。
  完整工法见 `references/rollback-and-restore.md`。
- **恢复完不要试图清 `kanban.db-wal`。** 它被 Hermes gateway（当前会话的宿主进程）占着，
  `rm` 报 `Device or resource busy`；`cp` 覆盖库仍有效，残留 WAL 的 salt 不匹配会被忽略。
  彻底清干净需要用户重启一次 Hermes —— 如实报成尾巴，不要自己动手杀进程。

## Support files

- `references/orchestration-framework-selection.md` — 多 Agent 编排框架选型：各候选项目在 **Windows 原生能不能跑**的
  实测结论（kanban-agency / hermes-conductor / kanban-code-orchestrator 对比）、三项 Windows 依赖的验证命令、
  `hermes config path` 与 `kanban boards create` 两个安装期坑。**要评估或更换框架时先读它**，不要重新试错。
- `references/install-and-config.md` — full `config.env` key table, symptom→cause→action troubleshooting table, card templates, and a command cheatsheet.
- `scripts/expand_card.py` — expand an existing card safely: appends (never overwrites) with an idempotency marker, optionally retitles, then asserts the original body is still intact and the title does not collide with `WF_VERIFY_KEYWORDS`. Run it instead of hand-editing a card body.
- `references/board-forensics.md` — 看板取证：`task_events` / `tasks` / `task_runs` 的真实表结构与列名、
  证明「某个阶段有没有跑过」的可复制查询、按卡还原状态链、汇总成证据表的写法，
  以及**执行器侧会话转录**（`$CLAUDE_CONFIG_DIR/projects/<slug>/<uuid>.jsonl`）这个独立证据源。
- `references/upstream-rate-limit-discipline.md` — 上游限流与 429 取证：健康度曲线、按会话归因、
  429 三问（速率 / key 冷却 / 鉴权）、重试必须占名额、key 池轮换、**闸门放错层的两个方向**、
  以及「监视器不能是被监视对象的一部分」。判定上游是不是被自己打爆时读它。
- `references/unattended-overnight-operation.md` — 无人值守过夜交接：两个必须先改的默认值
  （`WF_BLOCKED_MAX_RECOVER` / `WF_AGENT_TIMEOUT_SEC`）、免休眠实测、三哨兵核对、早间进度判据，
  以及**早间盘点**：用户问「汇报运行状况」时的四个取证查询、必现的三类回潮、汇报形态。
- `scripts/acceptance_audit.py` — 协调者验收审计（只读）：统计 `task_events` 里 review 相关 kind 的条数、
  逐张 `done` 卡查 `git log --grep=<卡号>`、扫 worker 日志里的「验收未执行」自述，
  一次性打出「哪些 done 卡没被验过」。跑它代替凭印象回答「审查环节在工作吗」。
- `scripts/agent_preflight.py` — 子员工环境预检：`CLAUDE_CONFIG_DIR` / `settings.json` / `claude` PATH /
  agent 数量 / frontmatter 可解析 / 每个 agent 含 `Write` / 落盘规则块在 / 备份区同名 / `config.env` /
  目录映射存在 / `--allowedTools` / 哨兵 cron。`--fix` 能自动补 `tools` 与落盘规则块。
  **改完 agent、重装、或流水线突然“全绿但零产出”时先跑它**，比逐项手查快得多。
- `scripts/kanban_rescue.py` — 看板救护：`triage` 卡死 / 僵尸 `running` / 父卡已归档的孤儿卡。
  默认只诊断，`--apply` 才动手并自动备份 db（写库同时补 `task_events` 事件行，不断审计链）。
- `references/rollback-and-restore.md` — 回退到已知良好点：三个可回退面（看板库 / 框架脚本 git / 业务仓库）、
  **先停写者再恢复**的顺序、WAL 被宿主进程占着为什么不杀 gateway、回退点怎么带后果列给用户选、
  「只回退 Hermes 侧、绝不碰 Claude Code 环境」的边界，以及**验证环境有没有被动过**的
  「生效目录 → mtime 分层 → 三份副本哈希」三步取证。用户说「回退到你还没接手的那」时读它。
- `references/flet-1.0.4-breaking-changes.md` — flet 1.0.4 破坏性变更速查表 + 迁移清单 + 验证脚本
- `references/pyinstaller-frozen-path-anchor.md` — PyInstaller 单文件模式路径锚定模式（`_runtime_root()`）
- `references/test-gate-zombie-reclaim.md` — 产出校验测试闸门（`_test_gate()`）+ 僵尸卡回收（`reclaim_stale()`）+ GUI 冒烟/交互测试模板
- `references/gui-testing-computer-use.md` — **GUI 测试用 computer_use (CUA) 专用指南**：Flet 1.x 桌面应用真实交互测试工作流、FilePicker 中文路径处理、cc-gui-tester agent 配置、证据留存规范

## 扩权改卡：先定范围骨架 + 追加不覆盖 + 标题重查 + 故障注入验收

用户给一张**已在看板里**的卡追加职责（「这张卡再加上 X」）时，四件事必须一起做，缺一件就是给自己埋坑：

0. **先把「主任务」写成完整授权范围，再把已知项降级为起点。** 用户要的是「排查整体」，不是「修我列的几条」。
   把已确认缺陷写成「必查清单」并置于最前，结构上就**等于定义了任务边界** —— worker 修完那几条便认为完事。
   正确形态：第一段写宽泛主任务（「逐环节穷举整个工作流，找失效模式并建立自愈体系」）并占据正文主体；
   清单单独成节，标题写「已验证缺陷，优先处理；**不是范围上限**」，末尾再加一条禁令
   「不要只修清单上的 N 条就交差 —— 那是起点，不是范围」。**清单越具体，这句禁令越不能省。**
   宽泛任务要配**方法论**而不是只配步骤，否则「整体」落不了地。写自愈/巡检类卡时用这两张表：
   每个环节必答 4 问 —— 会不会静默失败 / 失败了谁会知道 / 它会自己恢复吗 / 恢复不了会卡住什么；
   必须覆盖的环节 —— 凭证登录态、数据源、派单器、worker 执行、产出校验、状态机、调度层、
   告警通道、配置层、契约层（文档与实现是否一致）、资源层、凭证安全。

1. **默认只追加，不重写**（例外见第 4 条）。先 `show <id> --json` 取原文，`new = old + 追加段`，追加段带一个幂等 marker（已存在就跳过）。改完**读回断言**：marker 在、原正文仍是新正文的**前缀**（一个字都没丢）、原有验收项还在。直接跑 `scripts/expand_card.py`，它把这三条断言做完了。
2. **改了职责就必须重查标题。** `WF_VERIFY_KEYWORDS` 匹配的是**标题**，而描述「巡检/排查/审计」的词天然会写进新职责里 —— 一旦命中，`card_produce_check` 就把「零产出」判成合法，worker 交一份空报告也能过。扩权后标题用 **修 / 修复 / 新增 / 实现** 这类动作词，把「巡检」留在正文。脚本内置了这个碰撞检查。
3. **「无人值守 / 自动恢复」的验收只能是故障注入。** 这类需求最容易被交成「修复报告 + 建议清单」—— 读起来完整，实际什么都没验证。正文必须写死：**注入一个真实故障，在不碰它的前提下系统自己恢复**，并交付「注入什么 / 预期 / 实际 / 是否自愈 / 耗时」的记录。同时防越界：不许开 `--yolo`（安全取舍归用户）、不许改只读参考仓库、不许为了让报告好看放宽或关掉检查项。

4. **追加不是无条件正确：追加段与原任务定义冲突时必须重写，而重写要先抢救 marker 块。**
   触发条件：原正文已经把「要做什么」写死成一份清单 / 一组子任务，追加段却要把它降级为起点。
   此时继续追加会出现两套互相矛盾的任务定义，worker 会照更具体的那套干。
   重写是「切两刀，不是切一刀」：
   - 用 `show --json` 取原文，先记下**每一段 marker 块的起止**
   - **执行约束块通常夹在正文中间，不在末尾** —— 只按「切割点之后全丢」处理会把它一起删掉，
     worker 便失去「不许 `-c` / heredoc」这条约束而毫无察觉（危险命令会被 BLOCKED，白跑一轮）
   - 拼装顺序固定为：`保留的前缀 + 新任务段 + 抢救出来的执行约束块`
   - **读回断言，不要目测**：marker 在、执行约束段特征串还在、原业务上下文数字仍在、标题不撞验收关键词；
     把这些断言写进脚本的 checks 字典，全 ✓ 才算改完
   切不到 marker 就**停下报错**，不要「猜一下大概在哪」—— 宁可不动，也不能静默丢约束。

扩权后同步 `项目状态.md`（用户原话 + 需求拆解 + 每条完成度），这是这台机器上所有项目的固定动作。

## Maintenance layer: a runbook, an executable check, and a rolling snapshot

The setup carries a pile of machine-local config that is **not in version control and is lost on reinstall** (the three `dispatch_claude.sh` patches), plus one **external hard dependency** (the cc-switch proxy). Maintenance knowledge must not live only in the last conversation. Fix it into three layers:

| Layer | File | Answers |
|---|---|---|
| **Runbook** | repo root `运维手册.md` | "**what do I do**" — a symptom→cause→fix dictionary, hard dependencies, the reinstall-loses list, disaster recovery, log map |
| **Check** | `hermes\scripts\healthcheck\healthcheck.py` | "**is it healthy now**" — ~20 executable checks, **including detection that the dispatch patches are still present** |
| **Snapshot** | repo root `维护日志.log` (cron every 6h) | "**when did it start breaking**" — silent when healthy, alerts only on FAIL |

**The two traps in a health check itself (both really hit, and both make the checker lie):**

1. **Cross-job bleed.** When parsing `hermes cron list`, **never search the whole output for `Last run`** — you will grab *another* job's record (a real incident: `auto-skill-distill`'s 429 got reported as the watchdog job's error). Split into per-job blocks first (block header matches `^\s+[0-9a-f]{8,}\s+\[`) and search inside the block; and **flush the last block after the loop**, or you silently lose it (the mirror-image bug: "no run recorded yet").
2. **A check must be validated in both directions.** Testing only the healthy path proves nothing. Verify with **real output + a synthetic sample** (one OK job, one error job) that both the OK and FAIL branches report correctly.

**Design constraints:**
- A `no_agent` cron's `--script` takes **no arguments** → write a thin wrapper when you need flags (see `maintenance_snapshot.py`).
- The rolling log records **only a summary plus exception details**, never the full report — full reports bloat it until nobody reads it; details come from running the full report by hand.
- Keep the rolling log **out of version control** (appending every 6h means permanent dirty state and noisy commits) — list it in `.gitignore` with the reason; durable maintenance events go in the tracked `操作日志.log` instead.
- A health check that only ever says OK is worthless: make it fail loudly on a real injected fault before you trust it.
- **A warning that is known-benign must be recorded as benign, not left as a permanent WARN.** Two states keep showing up and must not sit in the WARN bucket forever: an **intentional** setting (a config key deliberately cleared so a role falls back to the default) and an **external** failure (a provider returning `insufficient balance` / 429 on a helper job unrelated to the pipeline). Left as WARN they train the operator to skim warnings — which is exactly how a real WARN gets missed. Fix it at the source: report the intentional state as PASS with a one-line `intentional: <why>`, and bucket external/quota errors separately from operational ones so the operational count stays meaningful.
