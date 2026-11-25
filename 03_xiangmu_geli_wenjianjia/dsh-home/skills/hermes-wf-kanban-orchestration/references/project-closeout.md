# 项目收尾：归档 → 清理 → 环境隔离

一个项目验收交付后，工作区必须回到「可开下一个项目」的干净状态。当前一条流水线的产物留在原位时，下一次派单会派进旧仓库（`WF_REPO` 还是旧的）、旧看板混着旧卡、旧 exe 进程占着文件锁。

## 何时执行

用户说「归档」「结项」「清理残留」「准备下一个项目」「环境隔离」时，整套跑完，不要只做一半。

## 步骤（按序）

### 1. 建归档目录并复制三类产物

```bash
mkdir -p "D:/已完成项目/<项目名>"
cp -r <项目源码目录>   "D:/已完成项目/<项目名>/<Proj>_project_$(date +%Y%m%d)"
cp -r <交付目录>       "D:/已完成项目/<项目名>/<Proj>_delivery_$(date +%Y%m%d)"
cp -r <看板目录>       "D:/已完成项目/<项目名>/<Proj>_kanban_$(date +%Y%m%d)"
```

**交付目录要含可分发 zip**，不要只留 `dist/`。源码目录要含 `操作日志.log` / `项目状态.md`。

### 2. 导出看板为可读 JSON（DB 会锁、会坏，JSON 才可检索）

导出 `tasks` / `task_events` / `task_comments` 三表到 `kanban_export.json`。表名以实际 schema 为准，缺表就跳过并打印错误，不要让整个导出崩掉。

### 3. 归档看板上的卡

```bash
hermes kanban --board <slug> archive <task_id>
```

逐张归档，**每张单独一次调用**。写成 for 循环批量跑容易超时——一张一张来，或分批并放宽 timeout。归档完确认 `hermes kanban --board <slug> list` 返回 `(no matching tasks)`。

### 4. 清理工作区残留

| 清理对象 | 说明 |
|---|---|
| 项目源码目录、交付目录 | 已归档，删 |
| 调试脚本、`debug_*.log`、`test_*.py` 探针、截图 | 一次性排障产物 |
| worker 日志目录 | 派单日志，内容已进项目操作日志 |
| `__pycache__` / `.pytest_cache` / `htmlcov` | 构建缓存 |
| scratch 里的临时脚本 | 识图、探针、一次性转换脚本 |

### 5. 环境隔离（这一步最容易漏）

```bash
cp scripts/hermes-wf/config.env  config.env.project_<proj>_$(date +%Y%m%d)   # 先备份
```

然后把 `WF_BOARD` / `WF_REPO` 置空字符串（不是删除该行，注释要留着）：

```bash
WF_BOARD=""          # ← 新项目：填你的看板 slug（留空则用 default）
WF_REPO=""            # ← 新项目：填你的项目根目录（必须是 git 仓库！）
```

暂停哨兵，杀残留进程：

```bash
hermes cron pause <sentinel_job_id>
powershell -NoProfile -Command "Get-Process -Name claude -ErrorAction SilentlyContinue | Stop-Process -Force"
powershell -NoProfile -Command "Get-Process | Where-Object { $_.ProcessName -like '*<App>*' -or $_.ProcessName -eq 'flet' } | Stop-Process -Force -ErrorAction SilentlyContinue"
```

### 6. 建新项目根目录 + 一份「开项目必做」README

新项目统一放 `D:/Ai/Agent/projects/`，README 写明：

- **第一步必须 `git init` + 首次 commit**（见下节）
- 一个项目一个看板，不要复用旧板
- `config.env` 怎么填
- 可复用环境清单（不允许删）
- 收尾清单（即本文件）

### 7. 收尾验证（必做，逐项打勾再报完成）

```bash
du -sh "D:/已完成项目/<项目名>"                      # 归档大小
ls <归档>/dist/*.exe <归档>/*.zip                    # exe 与 zip 都在
hermes kanban --board <slug> list                    # (no matching tasks)
hermes cron list | grep <sentinel>                   # [paused]
grep -E "^WF_BOARD|^WF_REPO" config.env              # 都是空
get-process claude / <App>                           # 0 个
```

## 新项目的第一个动作：`git init` + 首次 commit

```bash
git init
echo "# <项目名>" > README.md
git add README.md && git commit -m "init"
```

**为什么不能省**：`hermes-wf` 的产出校验用 `git status --porcelain` 的指纹判断「这次派单有没有产出」。`porcelain` 会把**整个未跟踪目录压成一行 `?? dir/`**——之后在目录里怎么写，指纹都不变，worker 干完活照样被判 `verdict=EMPTY 零产出`，卡被打回 blocked。

先把脚手架提交，后续写入才会显示成 ` M `，校验才看得见。`config.env` 里 `WF_REPO` 那段注释已经写明了这一点，**读配置不要只读值不读注释**。

## 不允许动的可复用环境

Python 运行时与 `flet` CLI、Ollama（嵌入/视觉/小模型）、ChromaDB/向量库、Hermes 主程序与 skills、`D:/Ai/claude code/`（agents + cc-switch）、`scripts/hermes-wf/`、以及**不属于本项目的其它业务仓库**（例如闲鱼流水线）。清理只针对本项目产物。

## Pitfalls

- **只归档不清理 = 没做**。用户要的是「能开下一个项目」，旧目录留着，下一次 `cd` 就可能进错树。
- **只清理不隔离 = 下次派单进旧仓库**。`WF_REPO` 是静默失败项：哨兵照常派单，只是派错地方。
- **`WF_AGENT_PREFIX` 不能置空**。它防抢单，空串会让 `startswith("")` 匹配所有卡。清 `WF_BOARD`/`WF_REPO`，但别碰前缀。
- **看板归档按张调**。批量 for 循环串行调用会撞命令超时，超时后剩下的卡还在板上。
- **归档完先验证再报完成**。要给出每个目录的实际大小和 exe/zip 的存在证明，不要只说「已归档」。
