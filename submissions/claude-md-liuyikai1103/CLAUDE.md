# CLAUDE.md — Next.js 15 + SQLite SaaS 项目指南

> 注意: 将该文件放在项目根目录。Claude Code 在读入项目时会自动加载。
> 适用于: Next.js 15 App Router + SQLite (better-sqlite3/Turso)

## 📁 项目结构

```
project/
├── src/
│   ├── app/                # Next.js 15 App Router 页面
│   │   ├── (auth)/         # 认证相关路由组
│   │   ├── (dashboard)/    # 仪表盘路由组（需要登录）
│   │   ├── api/            # API 路由
│   │   │   └── trpc/       # tRPC 路由处理器
│   │   ├── layout.tsx      # 根布局
│   │   └── page.tsx        # 首页
│   ├── components/         # React 组件
│   │   ├── ui/             # UI 基础组件 (shadcn/ui)
│   │   └── features/       # 业务组件
│   ├── db/                 # 数据库相关
│   │   ├── schema/         # Drizzle ORM schema 定义
│   │   ├── migrations/     # 数据库迁移文件
│   │   ├── queries/        # 数据库查询函数
│   │   └── index.ts        # 数据库连接
│   ├── lib/                # 工具函数
│   │   ├── auth.ts         # 认证逻辑
│   │   └── utils.ts        # 通用工具
│   ├── trpc/               # tRPC 设置
│   │   ├── router/         # 路由定义
│   │   ├── context.ts      # 请求上下文
│   │   └── index.ts        # tRPC 客户端
│   └── styles/             # 全局样式
├── public/                 # 静态资源
├── drizzle.config.ts       # Drizzle ORM 配置
├── next.config.ts          # Next.js 配置
├── tailwind.config.ts      # Tailwind 配置
├── tsconfig.json           # TypeScript 配置
├── package.json            # 依赖管理
└── CLAUDE.md               # 本文件
```

## 🏗️ 架构决策

### 理由充分的约定

| 约定 | 原因 |
|------|------|
| `src/` 目录存放所有源码 | 根目录整洁，配置文件与代码分离 |
| App Router (无 Pages Router) | App Router 是 Next.js 推荐方向，支持 RSC、布局嵌套 |
| Drizzle ORM (非 Prisma) | Drizzle 体积小、性能好，对 SQLite 支持原生 |
| tRPC (非 REST/GraphQL) | 端到端类型安全，无需 schema 生成，与 Next.js 配合极佳 |
| `drizzle-orm/better-sqlite3` (本地) + `@tursodatabase/libsql` (生产) | 开发环境零配置，生产用 Turso 边缘数据库 |
| `src/db/schema/*.ts` 一个文件一个模型 | 便于维护和迁移 |
| `src/app/api/trpc/[...route].ts` 单一入口 | tRPC 处理所有 API，不需要手动管理路由 |

### 命令速查

```bash
# 开发
npm run dev              # 启动开发服务器 (localhost:3000)

# 数据库
npm run db:generate      # 生成迁移文件（schema 变更后）
npm run db:migrate       # 执行迁移
npm run db:push          # 直接推送 schema 到数据库（开发用）
npm run db:studio        # 打开 Drizzle Studio (GUI)

# 构建与部署
npm run build            # 生产构建
npm run start            # 启动生产服务器
npm run lint             # ESLint 检查
npm run type-check       # TypeScript 类型检查

# 测试
npm run test             # 运行测试
npm run test:watch       # 监听模式
```

## 🎯 开发模式

### DO ✅ (模式)

1. **Server Components 优先**
   - 默认使用 Server Components
   - 只有在需要交互（事件处理、状态、浏览器 API）时才用 `"use client"`
   - Server Components 直接访问数据库，无需 API 调用

2. **数据库访问模式**
   - 在 Server Components 或 Server Actions 中直接调用 `db.query()`
   - 永远不要从 Client Components 直接导入 `db/*`
   - 使用 tRPC 作为 client ↔ server 的桥梁
   - 需要复杂数据获取时使用 tRPC Server Client

3. **迁移工作流**
   ```typescript
   // 1. 修改 schema
   // src/db/schema/users.ts
   export const users = sqliteTable("users", {
     id: text("id").primaryKey(),
     email: text("email").notNull().unique(),
     // 新增字段
     avatarUrl: text("avatar_url"),
   });

   // 2. 生成迁移: npm run db:generate
   // 3. 执行迁移: npm run db:migrate
   // 4. 从不手动修改 SQL
   ```

4. **错误处理**
   - tRPC 错误用 `TRPCError` 类
   - Server Actions 返回 `{ success: boolean; error?: string }`
   - 数据库错误用 try-catch，返回友好提示

5. **认证模式**
   - 使用 NextAuth.js / Auth.js v5
   - Session 在 Server Component 中通过 `auth()` 获取
   - Client 端用 `useSession()`

### DON'T ❌ (反模式)

1. **不要在 Client Component 中直接查询数据库**
   ```typescript
   // ❌ 错误
   "use client";
   import { db } from "@/db";
   db.select().from(users); // 浏览器端无法运行

   // ✅ 正确: 通过 tRPC 或 Server Action
   "use client";
   import { api } from "@/trpc/react";
   const { data } = api.user.getProfile.useQuery();
   ```

2. **不要直接修改迁移文件**
   ```bash
   # ❌ 错误: 手动编辑 SQL 迁移文件
   vi src/db/migrations/0001_*.sql

   # ✅ 正确: 修改 schema 后重新生成
   npm run db:generate
   npm run db:migrate
   ```

3. **不要使用 `npm run dev` 之外的 Node.js 环境**
   - Next.js 开发服务器处理所有环境配置
   - 不要单独运行 `ts-node` 或 `drizzle-kit push`

4. **不要在 Server Actions 中暴露敏感操作**
   ```typescript
   // ❌ 错误: 无权限检查
   export async function deleteUser(id: string) {
     await db.delete(users).where(eq(users.id, id));
   }

   // ✅ 正确: 先鉴权
   export async function deleteUser(id: string) {
     const session = await auth();
     if (!session?.user?.isAdmin) {
       throw new Error("无权操作");
     }
     await db.delete(users).where(eq(users.id, id));
   }
   ```

5. **不要将数据库 URL 硬编码**
   ```typescript
   // ❌ 错误
   const dbUrl = "file:./dev.db";

   // ✅ 正确
   const dbUrl = process.env.DATABASE_URL!;
   ```

## ⚡ 性能准则

1. **使用 React Suspense** 包裹数据加载区域
2. **页面级 Suspense boundary** = 每个路由段一个
3. **数据库查询要加 `limit`** — 防止全表扫描
4. **频繁查询用 `cache()` 或 `React.cache()`** 包装
5. **图片用 `<Image>` 组件** 并指定 `width/height`
6. **表单用 Server Actions** 不用客户端 fetch

## 🤝 贡献指南

1. 从 `main` 创建功能分支: `git checkout -b feat/my-feature`
2. 提交规范: `feat:` / `fix:` / `chore:` / `docs:` 前缀
3. 提交前确保: `npm run type-check && npm run lint && npm run test`
4. 在 PR 中运行 `bash changelog.sh` 确认 CHANGELOG
