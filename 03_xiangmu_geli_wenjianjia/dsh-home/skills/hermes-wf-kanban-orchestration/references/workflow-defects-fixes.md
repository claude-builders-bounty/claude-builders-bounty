# 工作流三大结构性缺陷（及应有的防线）

这三条的共同后果：**worker 真的干完了活，但看板上是「受阻」，成果随时被下一次覆盖。** 只要缺陷还在，派单越多、丢的成果越多。

## 缺陷 1：worker 不 commit → 产出被当作零

**现象**：worker 退出码 0、回复里写「已完成」、文件确实改了 —— 但 `git status` 里还是 `??`（untracked）或 ` M`（未提交）。产出校验器比的是 git 快照，所以判 `verdict=EMPTY 零产出` → 卡 block。

**为什么危险**：blocked 不代表文件被回滚。改动还在工作区里；下一个 worker 从同一棵工作树开工，直接覆盖或误删。

**应有防线**：

- worker 契约里写死「改完必须 `git commit`」，并在回复里报告 commit hash。
- 产出校验器不要只看快照差异，同时检查 `git status --porcelain` 是否有新增 untracked/modified —— 有改动但未提交，要报「未提交」而不是「零产出」，因为两种情况的处置不同。
- 派单前如果仓库大面积 untracked（见缺陷 3），先做一次基线提交，否则任何校验都不可信。

## 缺陷 2：没有 review 环节，直接 done

**现象**：派单脚本是「worker exit 0 + 有产出 → 直接 done」。没人审代码，也没人复核 worker 自己声称的「pytest 通过」。

**应有防线**：收尾改成三段：

1. worker 完成 → 卡置 **review**，不是 done
2. `cc-code-reviewer` 或对应 reviewer 审：读 diff、跑测试、确认根因真的解了
3. 审过了才 done；不过就 `request-changes` 退回去重做，并写明具体改法

worker 的自述不能当证据 —— 它可能真的跑了测试，也可能只是声称跑了。

## 缺陷 3：仓库根目录大面积 untracked，校验器失去基准

**现象**：整个 `frontend/`、`backend/`、`docs/` 全是 untracked，`git log` 只有初始两条 commit。此时：

- 产出校验器拿「前后快照」比不出任何有意义的东西（所有文件都算「新增」或都不算）
- 任何 worker 的改动都无法回溯到具体一次派单

**应有防线**：项目开场做一次完整的基线提交（含 `.gitignore` 排除 `dist/`、`build/`、`__pycache__/`、`.coverage`、`*.spec` 等产物），之后每次派单的 diff 才有意义。

## 缺陷 4：429 撞在收尾环节，卡被误判为失败

**现象**：worker 干完全部活（改代码 + 跑测试 + 写交付物）后，调用 `kanban complete` 时撞 429。派单脚本把整个流程判为失败 → block。

**应有防线**：把「worker 执行」和「看板状态回写」分开对待：

- worker 已退出 0 且有产出 → 成果已落盘，不能回滚、不能丢弃
- 429 只影响看板写不回，应**重试 kanban 调用**（指数退避），而不是重跑 worker
- worker 重跑会重复劳动、重烧配额，且在幂等性差的脚本上会双写

## 卡状态自查

出问题后先看三个东西，再决定动作：

1. `hermes kanban --board <b> show <id>` —— 卡的真实状态与最近事件
2. `logs/workers/<id>.out` —— worker 实际跑到了哪一步（找 429 / exit / 产出校验行）
3. `git status --short` + `git log --oneline -5` —— 成果到底在不在仓库里

三者不一致时，以**磁盘 + git** 为准，看板只是记分牌。
