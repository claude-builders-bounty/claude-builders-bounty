# CLAUDE.md

> Opinionated instructions for Claude Code on greenfield **Next.js 15 App Router + SQLite** SaaS projects.
> Stack: Next.js 15 (App Router, Server Components by default), TypeScript, SQLite (better-sqlite3), Zod, React Hook Form, shadcn/ui, Vitest + Playwright.
> 读完本文后，Claude Code 应当能在不追问澄清问题的前提下直接开发。

---

## Stack 与版本

- 框架：Next.js 15 (App Router)
- 语言：TypeScript 5 (strict)
- 组件库：shadcn/ui + Radix UI + Tailwind CSS
- 表单：React Hook Form + Zod (服务端与客户端共享 schema)
- 数据库：SQLite (better-sqlite3)，Drizzle Kit 迁移
- 验证：Vitest (单元/集成) + Playwright (E2E)
- 部署：Vercel 或 Docker (Node 20)
- 包管理：pnpm

禁止：App Router 中混用 `pages/` 目录；使用任何未经审计的 npm 包；在服务端组件里直接操作浏览器 API。

---

## 文件夹结构

```
apps/web/                      # Next.js 应用
  src/
    app/                       # App Router 路由
      (auth)/                  # 路由组：登录/注册
      (dashboard)/             # 登录后路由
      api/                     # Route Handlers (REST/Webhook)
    components/
      ui/                      # shadcn/ui 基础组件 (不可随意修改)
      forms/                   # 表单组件 (Zod schema + React Hook Form)
    lib/
      db.ts                    # better-sqlite3 单例连接 (不可重复创建)
      validators.ts            # Zod schema 定义
      auth.ts                  # 会话/Token 工具
    migrations/                # Drizzle SQL 迁移文件 (按时间戳命名)
    types/                     # TypeScript 全局类型
  drizzle.config.ts
  package.json
packages/                      # 可选共享包 (types, ui)
```

---

## SQL / 迁移约定

1. **所有数据库变更必须走迁移文件**，禁止直接 `db.exec` 创建/修改表。
2. 迁移命名：`YYYYMMDDHHMMSS_description.sql`，放 `apps/web/migrations/`。
3. 表名：复数蛇形 (`users`, `projects`, `audit_logs`)。
4. 列名：蛇形 (`created_at`, `updated_at`, `user_id`)。
5. 每张表必须包含 `id INTEGER PRIMARY KEY`, `created_at`, `updated_at`。
6. 禁止 `SELECT *`；显式列出字段。
7. 禁止在客户端组件直接调用 `db`；数据库访问仅限 Route Handler / Server Action。
8. 迁移前必须在本地 SQLite 上运行 `pnpm db:push` 验证，再提交。

---

## 组件模式

- 默认使用 **Server Component**；仅需要交互/状态时才用 `'use client'`。
- 表单：客户端组件 + `react-hook-form` + Zod `resolve`；提交走 Server Action。
- 错误处理：每个 Route Handler / Server Action 必须返回统一形状 `{ success: boolean, error?: string, data?: any }`。
- 禁止在 UI 组件里写内联 `style`；使用 Tailwind 类 + shadcn/ui。
- 所有面向用户的字符串必须可提取为 i18n key（即使暂未启用 i18n）。

---

## 不做的事 (及原因)

| 不做 | 原因 |
|------|------|
| 客户端直接操作 SQLite | 服务端组件/Route Handler 才能访问数据库，防止泄露数据库文件到前端包 |
| `SELECT *` | 避免意外返回敏感列 (如密码 hash)、减少内存占用 |
| 在 Server Component 里调用浏览器 API (`window`, `localStorage`) | Server Component 无浏览器环境，会导致构建失败 |
| 混用 `pages/` 与 `app/` | Next.js 15 App Router 不应与 Pages Router 并存 |
| 未加校验直接写库 | 必须用 Zod schema 校验输入，防止注入与脏数据 |
| 硬编码数据库连接字符串 | 使用环境变量 `DATABASE_URL`，本地 `.env.local` |
| 提交包含 `console.log` / `debugger` 的代码 | 干净生产代码，日志走结构化 logger |

---

## 开发命令

| 命令 | 作用 |
|------|------|
| `pnpm dev` | 启动开发服务器 (Turbopack) |
| `pnpm build` | 生产构建 |
| `pnpm start` | 启动生产服务器 |
| `pnpm db:generate` | 生成 Drizzle 迁移 |
| `pnpm db:push` | 将 schema 推入本地 SQLite |
| `pnpm test` | 运行 Vitest |
| `pnpm test:e2e` | 运行 Playwright E2E |
| `pnpm lint` | ESLint + Prettier |

---

## Claude Code 交互约定

- 实现新功能前，先读取 `app/` 下相关路由与 `lib/validators.ts`，确认已有模式。
- 新增 API 路由必须附带 Zod 输入校验 + 统一返回形状 + 一条集成测试。
- 修改数据库 schema 前，先在 `migrations/` 新建 SQL 文件，并在 PR 描述中说明升级步骤。
- 所有变更必须通过 `pnpm lint` 与 `pnpm test`。

---

**END**
