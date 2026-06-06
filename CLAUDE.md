# CLAUDE.md — Next.js 15 + SQLite (better-sqlite3) SaaS 项目规范

> 本文件为 Claude Code 提供项目上下文。**每条规则都有明确原因，不写废话。**

## 技术栈与版本

| 依赖 | 版本 | 原因 |
|------|------|------|
| Next.js | 15.x (App Router) | 最新稳定版，Server Components 成熟可用 |
| better-sqlite3 | 11.x | 同步 API、零配置、单机性能最佳，适合 SaaS 早期 |
| TypeScript | 5.x | 严格模式，拒绝 `any` 泛滥 |
| Tailwind CSS | 4.x | 原子化 CSS，与 Server Components 配合最好 |
| Zustand | 5.x | 最小客户端状态管理，不会污染 Server Component 边界 |
| Vitest | 2.x | 与 Vite 生态一致，比 Jest 快 5-10 倍 |

**绝对不用**：
- ❌ Prisma / Drizzle — SaaS 早期不需要 ORM 那层抽象，手写 SQL 更快更可控
- ❌ tRPC — Server Actions 已经解决了端到端类型安全
- ❌ Redis / 消息队列 — 单机 SQLite 足以支撑 10 万 DAU，过早引入复杂度是自杀
- ❌ Docker 开发环境 — 一个 `npx create-next-app` 就够，别把环境复杂化

## 目录结构

```
project/
├── src/
│   ├── app/                    # Next.js App Router 页面
│   │   ├── (auth)/             # 登录/注册（路由组，不参与 URL）
│   │   ├── (dashboard)/        # 登录后页面（路由组）
│   │   │   ├── _components/    # 页面级组件（`_` 前缀 = 不暴露为路由）
│   │   │   └── settings/
│   │   │       └── page.tsx
│   │   ├── api/                # 对外 API（非核心逻辑，核心用 Server Actions）
│   │   ├── layout.tsx          # 根布局
│   │   └── page.tsx            # 首页
│   ├── components/             # 全局共享 UI 组件
│   │   ├── ui/                 # shadcn/ui 组件（别自己造轮子）
│   │   └── forms/              # 表单组件（react-hook-form + zod）
│   ├── lib/
│   │   ├── db.ts               # SQLite 连接单例（整个进程只有一个连接）
│   │   ├── schema.ts           # 建表 SQL + 迁移记录
│   │   ├── auth.ts              # 认证逻辑（better-auth 或自定义 session）
│   │   └── utils.ts            # 纯函数工具
│   ├── actions/                # Server Actions（每个文件一个业务领域）
│   │   ├── user.ts
│   │   ├── project.ts
│   │   └── billing.ts
│   └── types/                  # 共享类型定义
│       └── index.ts
├── data/                       # SQLite 数据库文件存放处（.gitignore 整个目录）
├── migrations/                 # SQL 迁移文件（按时间戳命名）
├── tests/
│   ├── unit/                   # 纯函数 + Hook 测试
│   └── integration/            # Server Action + API 测试
├── .env.example                # 环境变量模板（不含真实值，可提交）
└── CLAUDE.md                   # 本文件
```

**关键决策**：
- `_components` 下划线前缀：Next.js 不会把 `_components` 目录下的 `page.tsx` 暴露为路由，比放 `src/components` 更能表达"这些组件只属于这个页面"
- `actions/` 独立目录而非混在 `app/` 里：业务逻辑与路由解耦，`app/` 只做路由编排
- `data/` 而非 `/tmp`：数据库文件需要持久化，生产环境映射到持久卷

## 数据库规范

### 连接管理
```typescript
// lib/db.ts — 整个进程只创建一次连接
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = path.join(process.cwd(), 'data', 'app.db');

let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma('journal_mode = WAL');        // 读写并发不互斥
    db.pragma('busy_timeout = 5000');       // 5 秒等待而非直接报错
    db.pragma('foreign_keys = ON');         // 强制外键约束
  }
  return db;
}
```

**原因**：better-sqlite3 是同步的，单连接足够。WAL 模式让读不阻塞写。MySQL/Postgres 的连接池思维在这里不适用。

### 迁移规则
1. 迁移文件命名：`migrations/001_add_users.sql`、`migrations/002_add_projects.sql`
2. 每个迁移文件包含 `-- UP` 和 `-- DOWN` 两部分
3. 迁移执行后记录到 `_migrations` 表
4. **开发阶段允许删库重建**（`schema.ts` 有 `resetDatabase()` 函数）
5. **生产绝不自动执行迁移**——手动运行 `npx tsx scripts/migrate.ts`

### 建表规范
```sql
-- migrations/001_add_users.sql

-- UP
CREATE TABLE users (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),  -- ULID 风格，URL 安全
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  plan TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'enterprise')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_users_email ON users(email);

-- DOWN
DROP INDEX IF EXISTS idx_users_email;
DROP TABLE IF EXISTS users;
```

**原因**：
- `TEXT` 主键而非 `INTEGER`：不会暴露用户数量，URL 里也更安全
- `CHECK` 约束：用数据库而非 TypeScript 保证数据完整性
- 时间用 `datetime('now')`：SQLite 没有 `TIMESTAMP` 类型，TEXT 是最佳实践

### 查询规范
```typescript
// ✅ 正确 — 参数化查询，防止注入
const stmt = db.prepare('SELECT * FROM users WHERE email = ?');
const user = stmt.get(email);

// ✅ 正确 — 事务语法
const insertUser = db.transaction((data: UserInput) => {
  const result = db.prepare('INSERT INTO users ...').run(data);
  return result;
});

// ❌ 错误 — 字符串拼接
db.exec(`SELECT * FROM users WHERE email = '${email}'`);
```

## 组件模式

### Server Component 优先
```
默认新建的组件都是 Server Component。
只有需要 useState/useEffect/onClick 时才加 'use client'。
```

### 数据流
```
Server Component 直接读数据库 → 传给 Client Component 做交互
不要通过 API Route 中转，不要建 tRPC 层。
```

### 客户端状态
```typescript
// ✅ Zustand 用在这些场景，其他地方不要用
// - 表单临时状态（多步骤表单）
// - UI 开关（侧边栏、弹窗）
// - 用户偏好（主题、语言）

// ❌ Zustand 不要用于
// - 服务端数据缓存（用 React Cache + fetch）
// - 认证状态（用 Cookie/Session）
// - 跨页面共享数据（用 URL 参数或 Server Action 重取）
```

### 表单模式
```typescript
// 统一用 react-hook-form + zod
// Server Action 做校验 + 写入
'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { createProject } from '@/actions/project';

const schema = z.object({
  name: z.string().min(2, '项目名至少 2 个字符').max(50),
  description: z.string().max(500).optional(),
});

export function CreateProjectForm() {
  const form = useForm({ resolver: zodResolver(schema) });
  
  return (
    <form action={createProject}>
      {/* 用 Server Action，不要自己调 fetch */}
    </form>
  );
}
```

## 开发命令

```bash
# 开发
npm run dev                  # localhost:3000

# 类型检查（提交前必须跑）
npm run typecheck

# 测试
npm run test                 # vitest run（全部测试）
npm run test:watch           # vitest（监听模式）

# 数据库
npm run db:reset             # 删库重建 + 跑所有迁移（仅开发环境）
npm run db:migrate           # 执行未跑的迁移

# 代码质量
npm run lint                 # ESLint
npm run format               # Prettier
```

## 我们不做的事（以及为什么）

| 不做 | 原因 |
|------|------|
| GraphQL | Next.js Server Components 已经解决了 over-fetching。GraphQL 增加一个查询语言层的复杂度，早期不划算 |
| 微服务 | 单体 Next.js + SQLite 在 10 万 DAU 之前不会有瓶颈。微服务是组织问题，不是技术问题 |
| WebSocket | Server Actions + `revalidatePath` 能解决 90% 的实时需求。剩下 10% 等真有需求再加 |
| i18n 第一天搞 | 先用英文硬编码。多语言是产品验证之后的事 |
| 自建认证 | 用 better-auth 或 Clerk。自己写密码哈希/2FA/邮箱验证是浪费时间 |
| Tailwind 组件库之外的 CSS | shadcn/ui 已经覆盖了所有常见 UI 模式。自定义 CSS 只在品牌色/登录页用 |
| 环境变量验证 | 用 `t3-env` 或 `zod` 校验 `process.env`，启动时就报错而非运行时炸 |
| 日志框架 | `console.log` 在开发阶段足够。等需要结构化日志时再引入 pino |
