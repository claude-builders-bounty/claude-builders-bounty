# 测试记录（2026-11-26）

目标：证明这份 `CLAUDE.md` 里写的规则不是空话——按它描述的目录结构和迁移约定，
真建一个小项目，真跑一遍迁移。

## 环境

- Windows 11 / Node v24.21.0 / npm 11.19.0
- better-sqlite3 12.11.1（prebuilt 二进制）
- 目录：`demo/`（临时骨架，未提交）

## 1. 迁移执行器按 `NNNN_*.sql` 顺序应用，且可重复运行

```console
$ node src/db/migrate.mjs
apply 0001_init.sql
apply 0002_invoices.sql
done: 2 applied, 0 skipped, tables = _migrations, invoices, org_members, orgs, users

$ node src/db/migrate.mjs          # 第二次
skip  0001_init.sql
skip  0002_invoices.sql
done: 0 applied, 2 skipped, tables = _migrations, invoices, org_members, orgs, users
```

两次运行的结论：迁移按字典序应用、记录进 `_migrations`、重复执行不报错。
这就是文档里“每条迁移必须能跑两次”的实测依据。

## 2. PRAGMA 设置生效

`client.ts` / `migrate.mjs` 里的三行 pragma 在真实连接上有效：

- `journal_mode = WAL` —— 生成 `app.db-wal` 文件，读写不互锁
- `foreign_keys = ON` —— `org_members.org_id` 插入不存在的 org 会直接报错
- `busy_timeout = 5000` —— 并发写时等待而不是立刻 `SQLITE_BUSY`

## 3. better-sqlite3 的同步事务行为

`db.transaction(fn)` 内任一条语句抛错，整个事务回滚——迁移器用这个特性把
「执行 SQL + 写入 `_migrations`」绑成原子操作。

## 没能测的部分（如实说明）

“把 CLAUDE.md 放进新项目，Claude Code 不用追问就能理解上下文”这一条，我没有
Claude Code 账号，无法实测。我做到的等价验证是：把文档里出现的每条约定（目录、
命名、迁移命名、pragma、server action 形状）都落到一个可运行的骨架里，确认它们
自洽、可执行。
