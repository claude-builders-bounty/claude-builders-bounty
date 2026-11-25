# 回退：把工作流退到已知良好点

用户说「回退到你还没接手的那」时读这份。核心风险不是找不到备份，而是**恢复被写者立刻覆盖**、
以及**回退顺手把不该动的环境一起改了**。

## 边界：只回退 Hermes 侧，绝不碰 Claude Code 环境

用户会明说「不要破坏我 claude code 的环境」。这是硬约束，不是客气话。

| 可回退（Hermes 侧） | 只读不动（Claude Code 侧） |
|---|---|
| 看板库 `kanban/boards/<slug>/kanban.db` | `$CLAUDE_CONFIG_DIR` 下的 `agents/`、`rules/`、`skills/` |
| 框架脚本 `scripts/hermes-wf-<board>/`（自成一个 git 仓库） | `settings.json`、`cc-switch.db` |
| 业务仓库 `WF_REPO` | cc-switch 应用 / 代理 / 它的守护 cron |

回退前先只读盘点，把「我改了什么」列成表 —— 含**未经批准**的改动。

## 验证「环境有没有被动过」：先只认生效目录，再按 mtime 分层，最后哈希取证

盘点之后用户接着会问「之前一堆乱改有没有影响到 Claude Code 环境」。答这个**不要凭印象**，三步出结论。

**① 只看生效目录。** `$CLAUDE_CONFIG_DIR`（本机 `D:\Ai\claude code`）下的才是活配置；
`~/.claude/` 是安装期留下的副本，在那里数 roster / 规则会得出错误结论。

**② 按 mtime 分层，别把「装完之后被写过」直接当成「被改坏」。**

| 类 | 例 | 判定 |
|---|---|---|
| 原始资产 | `rules/*.md`、`agents/*.md`、`commands/*.md` | 全停在**安装那天** ⇒ 未被动过；出现新日期 ⇒ 真被改过 |
| 运行时产物 | `projects/**/*.jsonl`、`sessions/*.json`、`plugins/cache/**/.in_use/*`、`backups/.claude.json.backup.*`、`cc-switch.db` | 每次 worker 起跑/看门狗 tick 都会写；**属正常运转，不是污染** |

实测一次盘点：生效目录下 **859 个文件**在安装日之后被写过，但 **102 个原始资产
（4 规则 + 40 角色 + 58 命令）无一例外全是安装日** —— 全部改动都落在运行时产物上 ⇒ 结论「环境完好」。
**先分层再下结论**，否则会把 worker 的会话日志说成「环境被改乱了」。

**③ 哈希取证，别只说「我看了下没变」。** 这类环境通常有 3 份同源副本（生效目录 / 遗留 `~/.claude/` /
交付时的桌面源），SHA256 全等即字节级证明：

```python
import hashlib, os
def h(p):
    with open(p, 'rb') as f: return hashlib.sha256(f.read()).hexdigest()[:12], os.path.getsize(p)
for f in sorted(os.listdir(live_rules)):
    print(f, h(os.path.join(live_rules, f)), h(os.path.join(desktop_src, f)))
```

报告里给「文件名 / 三份哈希 / 尺寸」三列，用户自己能复核。**哈希全等 + mtime 全为安装日**
才够格说「一个字节都没动」。

**配置层同理，用 diff 而不是 mtime。** cc-switch 每次 attach 都会重写 `settings.json`，
**mtime 新是常态、不代表内容变了**。拿它和各 `.bak-*` 逐一比键值，
「env 与其他键全等」比「时间戳是新的」有说服力得多。

## 三个可回退面

| 面 | 位置 | 手段 | 备注 |
|---|---|---|---|
| 看板库 | `<hermes_home>/kanban/boards/<slug>/kanban.db` | `cp kanban.db.bak-* kanban.db` | 见下方命名规律 |
| 框架脚本 | `<hermes_home>/scripts/hermes-wf-<board>/` | `git checkout -- .` / `git reset --hard <sha>` | **它自己就是 git 仓库**；最早一次提交 ≈ 装完那一刻 |
| 业务仓库 | `WF_REPO` | `git reset --hard <sha>` | 业务产出不可再生，**重置前必须先问** |

看板备份两类命名，`ls -la <boards>/<slug>/kanban.db.bak*` 一次看全，**按时间取最早的那个就是「还没接手之前」**：

- `kanban.db.bak-before-<事由>-<YYYYMMDD-HHMMSS>` —— 某次写库/救援前手动留的
- `kanban.db.bak_<YYYYMMDD_HHMMSS>` —— 批量动作前留的

`.gitignore` 通常挡住 `*.env.bak*`，但**看板备份不要指望 git** —— 全靠这些文件。

## 顺序（错一步就白做）

1. **先停写者，再恢复。** 派单哨兵每分钟写一次库；不停它，恢复出来的库 60 秒内被写回去。
   症状极具欺骗性：`cp` 明确成功、退出码 0，但 `kanban list` 还是新数据。

   ```bash
   hermes cron list                 # 现查 job id，别背
   hermes cron pause <派单哨兵 job>
   hermes cron pause <受阻卡自动恢复 job>
   hermes cron pause <协调者验收 job>
   ```

   停的是**三个流水线 job**（哨兵 / 受阻恢复 / 验收）。**不要停 cc-switch 守护与限流看门狗** ——
   它们属于模型链路，不是流水线，停了会让 Claude Code 通道跟着断。
2. 先留一份当前库再覆盖：`cp kanban.db bak-before-restore-<stamp>`，然后 `cp <最早备份> kanban.db`。
3. **用新进程读回验证**（不是看 `cp` 的返回码）：

   ```bash
   python -c "import sqlite3;con=sqlite3.connect('file:<绝对路径>?mode=ro',uri=True);print(con.execute('select count(*) from tasks').fetchone()[0]);print(dict(con.execute('select status,count(*) from tasks group by status').fetchall()))"
   ```

4. 隔几秒**再读一次**，数字不变即稳定；报告时给出「回退前 / 回退后」的卡片数对照。

## WAL / -shm 被宿主进程占着 —— 不要为此杀进程

`rm kanban.db-wal` 报 `Device or resource busy`，因为 **Hermes gateway 进程一直开着这块库**
（`dispatch_in_gateway: true`）。要分清三件事：

- gateway 是**当前会话的宿主**，杀了这个对话就没了。**绝不为清 WAL 去杀它。**
- `cp` 覆盖库文件**能成功**（gateway 以 share-delete 打开），所以恢复本身有效；
  `-wal` 里残留的旧事务 header salt 与替换后的库不匹配，SQLite 会忽略它。
- 彻底清干净只能**由用户重启一次 Hermes**。把这条作为「尾巴」如实报告，自己不动手。

## 回退点怎么定：列后果，让用户选

不要自己挑一个「最合理」的点，也不要把候选点讲成等价选项。带后果列出来：

| 方案 | 命令 | 后果 |
|---|---|---|
| 回到本会话之前 | `git checkout -- .` + 移走本会话新建的未跟踪文件 | 保留更早的机制，只撤本会话改动 |
| 回到最初安装态 | `git reset --hard <最早 sha>` | 撤掉**全部**后续修复，只剩装完那一刻 |

两个连带事实要一并讲：

- **未跟踪的新文件不会随 `git checkout` 消失**，要单独点名列出来（`git status --porcelain` 的 `??`）。
- **业务仓库的提交默认不撤**，哪怕是自己加的 —— 里面可能有唯一跑通的交付物。列入候选、说明它在 git 里还能捡回来，然后等用户拍板。

## 报告形态：逐项可核对

用户在这种时刻要的是对照表，不是散文：

1. **已回退** —— 项 / 状态 / 证据（卡片数、文件时间戳）
2. **未回退** —— 项 / 我改了什么 / 可选的回退命令 / 各自后果
3. **尾巴** —— 需要用户自己做的动作（如重启 Hermes 清 WAL）
4. 结尾只列「需要你定的 N 件事」，**不附方案、不再动手**

回退本身也要写进项目根的 `操作日志.log`（时间 + 动作 + 结果），否则审计链又断了。
