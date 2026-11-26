# CLAUDE.md for a Next.js 15 + SQLite SaaS

An opinionated `CLAUDE.md` you can drop into a greenfield Next.js 15 (App Router) +
SQLite (`better-sqlite3`) project. Every rule carries its reason, so Claude Code follows
the house style instead of inventing a new one each session.

## 用法

```bash
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/templates/nextjs-sqlite-saas/CLAUDE.md -o CLAUDE.md
```

或者直接把 `CLAUDE.md` 复制到项目根目录。没有占位符要填，没有 `<your-app>` 要换。

## 里面有什么

- **Stack & versions**：版本钉死的原因（Pages Router、strict、better-sqlite3 的同步性）
- **Folder structure**：`app/` + `src/{db,queries,actions,components,lib}`，每条附理由
- **Naming**：表名复数、`Row` 后缀、ISO-8601 时间、action 命名
- **SQL & migrations**：`NNNN_name.sql` 追加式、三步改列、WAL/FK/busy_timeout、参数绑定、索引
- **Component patterns**：RSC 优先、`useActionState`、loading 粒度、一个可复制的 action 例子
- **Dev commands**：`dev / build / db:migrate / db:reset / test / lint`
- **What we don't do**：不引 ORM、不 `SELECT *`、不 `any`、不 barrel、不 `useEffect` 取数、不静默 catch

## 怎么验证的

见 [`TESTING.md`](./TESTING.md)：按文档建了骨架，跑了两遍迁移（第二遍全 skip），
确认 pragma 和事务行为符合文档描述。

## 为什么这么“固执”

通用模板对 Claude 没用——它会照自己的习惯写。这份文档的每条规则都在堵一个具体的
坑：`utils.ts` 变杂物间、`ui/` 里 import SQL 把原生模块带进浏览器、无 `WHERE` 的
`DELETE`、无索引的外键、`SELECT *` 把 RSC payload 撑大。
