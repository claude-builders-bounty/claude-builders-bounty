# 多 Agent 编排框架选型（Windows 原生机器的实测结论）

用户反复要「一个能跑通的通用型多 Agent 架构」。这份文件记录候选项目的**平台事实**与**验证命令**，
避免每次从头试错。核心教训一条：**角色链最漂亮的项目，平台不通就一行都跑不起来。**

## 结论速查

| 项目 | 类型 | 运行时依赖 | Windows 原生 | 通用性 |
|---|---|---|---|---|
| `Edaire/kanban-agency` | Hermes 插件 + runtime | tmux、ttyd、fcntl | ❌ **不可用** | 角色链最完整（analyst→architect→developer→tester）+ 浏览器 Cockpit |
| `forcewake/hermes-conductor` | **纯 skill 包**（2 skill + 7 pattern） | git worktree、外部 CLI | ✅ **可用** | 通用（任何改文件的 CLI） |
| `lichenrobo/kanban-code-orchestrator` | 纯 skill 包（3 个 worker skill） | 无额外 | ✅ 大概率可用 | 仅代码（Coder→Tester→Reviewer） |

## kanban-agency 为什么在 Windows 上跑不了（实测证据）

- `core.py:6` **模块顶层** `import fcntl` → Windows 无此模块，任何子命令一启动就 `ModuleNotFoundError`
- `tmux` 在 `core.py` 里出现 **392 次** —— 会话层 `tmux -> claude TUI -> ttyd pane` 是架构核心，不是可省组件
- `ttyd` 提供浏览器 Cockpit；Windows 侧需要另行解决
- README（英文 + 中文）**全文没有出现 windows**，安装段只给 `brew install tmux ttyd`

它在 WSL 里能跑（实测 `--help` 出 15 个子命令，`advance` 能建出正确的 4 角色依赖链），
**但不要为此把入口搬到 WSL** —— 用户的入口约束是「Hermes 会话」，在 WSL 再起一套 Hermes
等于又造两块互不相通的看板，正是要消除的污染形态。

### 附带发现（将来若真要在 Linux 上用它）

- `scan` 只按标题/正文里的角色词路由到**单个**角色卡（`match_roles` → `route_to`），**不读 `workflow:` 字段**；
  4 角色链来自 `advance`（内部 `ensure_workflow`），不是 `scan` / `start`
- `ensure_workflow` 把 provider **硬编码成 `"codex"`**（`core.py:3110`），`roles.yaml` 对 4 角色链无效 ——
  想用 claude 必须装 codex，或改这一行

## hermes-conductor 为什么可用

纯 Hermes skill 包，没有 runtime、没有 tmux/ttyd/fcntl：

```
skills/kanban-orchestrator/   ← 协调层 playbook
skills/kanban-worker/         ← 执行层 playbook
patterns/                     ← 7 个生产模式
```

执行层用 **git worktree 隔离 + 外部 CLI headless**（`claude -p`），两样在 Windows 都原生支持。
入口就是 Hermes 会话，看板用 `hermes kanban watch`，**没有第二套 Web UI** —— 正合「入口只在 Hermes 会话」。

它的八条铁律里最该先读的两条：协调者永不实现（`Route only`）；**外部 agent 自述永远不算完成证据**
（控制器自己重跑测试、看 worktree diff、拿 commit ID 才关卡）。

安装形态：`hermes skills install <owner>/<repo>/skills/kanban-orchestrator` 装协调层，
每个 worker profile 再装 `kanban-worker`。

## Windows 侧三项依赖的验证命令（跑通才算数）

装任何「Hermes 当协调层 + 外部 CLI 当执行层」的框架之前，先跑这三条：

```bash
# ① Hermes 版本（多数要求 v0.20+）
hermes --version

# ② git worktree（worktree 隔离是并行安全的前提）
cd <scratch>/main_repo && git init -q && echo hi > a.txt && git add -A \
  && git -c user.email=t@t -c user.name=t commit -qm init \
  && git worktree add ../wrtest -b testbranch && git worktree list
# 期望：wrtest 目录出现，git worktree list 有两行

# ③ 执行器 headless 单发（判据是输出内容，不是退出码）
timeout 180 claude -p "只回复两个字：可用"
# 期望：真的打印出内容。空输出 / 124 = 模型链路不通，先修链路再谈框架
```

三条全过，「Windows 原生」才成立；任一条不过，先别装。

## 安装期的两个 Hermes CLI 坑

- **`hermes config path` 返回的是 `config.yaml` 文件路径，不是目录。**
  `cd "$(hermes config path)"` 直接报 `Not a directory`；要目录用 `dirname "$(hermes config path)"`，
  或者直接用已知的 Hermes home。
- **建板是 `hermes kanban boards create <slug>`**，`hermes kanban init <slug>` 会报
  `board '<slug>' does not exist. Create it with 'hermes kanban boards create <slug>'`。

## 网络侧：GitHub 直连不通时的克隆通道

`git clone https://github.com/...` 在部分网络下报 `Recv failure: Connection was reset`。
先用镜像前缀试通，再决定要不要配代理：

```bash
git clone --depth 1 https://ghfast.top/https://github.com/<owner>/<repo>.git <dir>
```

`ghfast.top` / `ghproxy.net` / `gitclone.com` 三个前缀轮着试；用 `--depth 1` 减少传输量。
**先用 `curl -sS -o /dev/null -w "%{http_code}" <镜像根>` 探活再 clone**，别盲试。

## 换项目时不要重复的错

- 不要把「WSL 里能跑」当成「能用」—— 先确认入口和看板是不是用户实际看的那一套
- 不要因为某个项目角色链最漂亮就选它 —— 平台不通时，漂亮的部分一行都跑不起来
- 候选自带的 `tests/` 通常不覆盖 Windows 路径；`pytest` 全绿不代表本机能跑
- 选了平台不兼容的项目，正确的收尾是**明确告诉用户「这是 Linux 原生项目，不适合 Windows」并换候选**，
  而不是打补丁硬上（补 fcntl 也补不出 tmux）
