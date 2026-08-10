# CLAUDE.md — Next.js 15 + SQLite SaaS 项目开发指南

> 用途：让 Claude Code（或任何 AI 编码助手）在进入本项目时无需追问即可正确工作。
> 适用：Next.js 15 App Router + SQLite（better-sqlite3，本地文件数据库）。

## 1. 技术栈与版本（不要擅自升级）

| 层 | 选型 | 理由 |
| --- | --- | --- |
| 框架 | Next.js 15（App Router，React 19） | 稳定、RSC 生态成熟；App Router 是长期方向 |
| 语言 | TypeScript 5.x，`strict: true` | 类型即文档，减少运行时错误 |
| 数据库 | SQLite 文件 + better-sqlite3 | 零运维、事务强、单机 SaaS 首选；不引入 ORM |
| 迁移 | 自写 `migrations/` 脚本 + `schema_migrations` 表 | 无 ORM 时迁移必须显式、可回放 |
| 认证 | Auth.js（next-auth v5）+ 会话存 SQLite | 与 SQLite 同进程，无额外服务 |
| 样式 | Tailwind CSS v4 + shadcn/ui 组件 | 快速一致，不写重复 CSS |
| 测试 | Vitest + React Testing Library + Playwright（冒烟） | 单元/组件/端到端分层 |

## 2. 目录结构（约定优于配置）

```text
app/
  (auth)/                  # 登录相关路由（login/register/callback）
  (dashboard)/             # 需登录的页面组（layout 里校验会话）
    layout.tsx
    page.tsx
  api/                     # Route Handlers，按资源分目录
    webhooks/
    users/
  layout.tsx
  globals.css
components/
  ui/                      # shadcn/ui 原子组件（勿手改生成文件）
  forms/                   # react-hook-form + zod 表单
  features/                # 业务组件（按功能命名，如 billing/）
lib/
  db.ts                    # better-sqlite3 单例（唯一 db 入口）
  migrations/              # 迁移脚本 001_xxx.ts ...
  repositories/            # 数据访问层（每表一个模块：users.ts, plans.ts）
  auth.ts                  # 认证与会话辅助
  validators/              # zod schema（与 API/表单共用）
  utils.ts
middleware.ts              # 会话刷新/路由保护（如需 edge 中间件）
public/
tests/
  unit/  integration/  e2e/
```

## 3. SQL / 迁移约定（重要）

- **唯一写入口**：业务代码禁止直接 `db.prepare(...)`，一律走 `lib/repositories/*` 的函数。理由：统一事务、审计、测试替身。
- **迁移编号**：`001_`、`002_` 递增；已合入的迁移**永不允许修改**，改 schema 只允许新增迁移。理由：生产库不可重放。
- **每个迁移必须可逆**：提供 `up()` / `down()`。理由：本地开发需要干净回滚。
- **外键**：开启 `PRAGMA foreign_keys = ON`；删除父行前先处理子行。
- **时间字段**：统一 `INTEGER` 存 Unix 秒（`created_at`/`updated_at`），不用字符串。理由：排序、时区、比较都干净。
- **金额/计数**：金额用整数分（`price_cents`），不用浮点。理由：浮点误差不可接受。
- **软删除**：默认不软删；确需时用 `deleted_at` 字段并统一过滤。
- 迁移执行脚本：`npm run migrate:up` / `migrate:down`（见 package.json scripts）。

## 4. 组件与数据模式

- **默认服务端组件**：能不做客户端就不加 `"use client"`。理由：更小 JS、更快首屏、更安全。
- **客户端边界**：需要交互时再标 `"use client"`，并把数据获取留在服务端层（Server Component 或 Server Action 传数据）。
- **表单**：一律 `react-hook-form` + `zod`（schema 放在 `lib/validators/`，前后端共用）。
- **变更操作**：优先 Server Actions（`app/actions.ts` 或就近文件），需要流式/回调时才用 Route Handler。
- **API 返回**：统一 `{ ok: true, data }` / `{ ok: false, error }` 结构。
- **样式**：先查 shadcn/ui 有没有现成组件；业务样式用 Tailwind 原子类，不写全局 CSS 类名。

## 5. 开发命令

```bash
npm install            # 安装依赖
npm run dev            # 本地开发（http://localhost:3000）
npm run migrate:up     # 执行迁移
npm run db:seed        # 灌种子数据
npm run lint           # ESLint + tsc --noEmit（提交前必跑）
npm run test           # Vitest 单元/组件测试
npm run test:e2e       # Playwright 冒烟
npm run build          # 生产构建（部署前必过）
```

## 6. 我们不做的事（及理由）

- **不用 Prisma/TypeORM**：SQLite 单文件 + better-sqlite3 已够，ORM 增加抽象和生成代码噪音。
- **不在客户端直接查库**：数据库只在服务端进程内访问（RSC/Server Actions/API）。
- **不写大型 `_app`/全局状态库**：页面级状态用 Server Components + URL params，必要时才上 React Context；不加 Redux/Zustand 除非多页面共享复杂状态。
- **不用 `any`**：`tsconfig` 开 `noImplicitAny`；实在无法推断时用 `unknown` + 收窄。
- **不 catch 后吞错误**：所有 catch 至少 `console.error` 并向上抛（表单层给用户可见错误）。
- **不在组件里写 SQL**：数据访问与视图分离（见第 3 节）。
- **不给路由写无鉴权写操作**：任何写接口先过会话校验（middleware 或 handler 内 `getSession`）。

## 7. 工作流提醒（给 AI 助手）

- 改完代码**先跑 `npm run lint` 再提交**；涉及数据库改动必须写迁移。
- 提交信息用 Conventional Commits：`feat:` `fix:` `chore:` `refactor:`。
- 不确定业务规则时，先查 `docs/` 或问仓库维护者，不要臆造。
- 修改 `components/ui/` 下生成的 shadcn 组件前先确认是否有必要，避免升级冲突。
