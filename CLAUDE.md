# CLAUDE.md — Next.js 15 + SQLite SaaS 生产模板

> 本文档是 AI 编程助手（Claude Code、Cursor、GitHub Copilot 等）的「操作合约」。
> 所有参与本项目的 AI 和人均需遵守此文档。

---

## 一、技术栈与版本（严格锁定）

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 15.x (App Router) | 全栈框架 |
| React | 19.x | UI 库 |
| TypeScript | 5.4+ (strict 模式) | 类型安全 |
| SQLite | 3.45+ | 生产数据库 |
| better-sqlite3 | 11.x | 本地 Node.js SQLite |
| Turso/libSQL | latest | 边缘部署 SQLite |
| Drizzle ORM | 0.30+ | 类型安全 ORM |
| NextAuth.js | 5.x (Auth.js) | 认证 |
| Stripe Node SDK | 14.x | 支付 |
| Tailwind CSS | 4.x | 样式 |
| Vitest | 1.x | 测试 |
| shadcn/ui | latest | 组件库 |

**锁定原因**：
- Next.js 15 App Router 的 Server Action、Streaming 是核心特性，必须启用
- TypeScript strict 模式可在编译期捕获数据结构漂移
- SQLite 保持 MVP 简单、低成本、可靠，同时支持真正的关系约束
- Drizzle 让 SQL 可见、迁移文件可审查；避免隐藏查询形状的 ORM

---

## 二、项目结构（强制约定）

```
my-saas-app/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # 路由分组：登录/注册
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/             # 路由分组：仪表盘（需认证）
│   │   ├── layout.tsx           # 认证检查 Layout
│   │   ├── overview/page.tsx
│   │   ├── settings/page.tsx
│   │   └── billing/page.tsx
│   ├── api/                     # API Routes
│   │   ├── auth/[...nextauth]/route.ts   # NextAuth 路由
│   │   ├── users/route.ts                # REST API
│   │   ├── webhooks/stripe/route.ts     # Stripe Webhook
│   │   └── trpc/[trpc]/route.ts       # tRPC（可选）
│   ├── layout.tsx               # 根 Layout（字体、ThemeProvider）
│   ├── page.tsx                 # 落地页 / 注册页
│   ├── not-found.tsx           # 404 页面
│   ├── loading.tsx             # 全局 Loading UI
│   └── globals.css            # 全局样式
├── components/                 # React 组件
│   ├── ui/                    # shadcn 基础组件（不允许修改）
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   └── dialog.tsx
│   ├── forms/                 # 业务表单组件
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   └── BillingForm.tsx
│   └── layouts/              # 布局组件
│       ├── DashboardShell.tsx
│       ├── Sidebar.tsx
│       └── Navbar.tsx
├── lib/                       # 工具函数（纯逻辑，无 UI）
│   ├── auth.ts                # NextAuth 配置
│   ├── db.ts                  # SQLite 客户端单例
│   ├── stripe.ts              # Stripe 客户端单例
│   ├── validators.ts          # Zod Schema 集中定义
│   ├── utils.ts               # 通用工具函数
│   └── constants.ts          # 常量定义
├── prisma/                   # Prisma ORM（可选，推荐 Drizzle）
│   ├── schema.prisma
│   └── migrations/
├── drizzle/                   # Drizzle ORM（推荐）
│   ├── schema.ts             # 数据库 Schema 定义
│   ├── migrations/           # 迁移文件
│   └── seeds/               # 种子数据
├── sql/                       # 原生 SQL（用于复杂查询）
│   ├── triggers/             # SQLite 触发器（审计、软删除）
│   ├── views/                # 预计算视图（仪表盘用）
│   └── functions/           # SQLite 用户自定义函数
├── tests/                     # 测试文件
│   ├── api/                  # API Route 测试（Vitest + supertest）
│   ├── components/           # 组件测试（Vitest + @testing-library/react）
│   ├── lib/                  # 工具函数测试
│   └── e2e/                 # E2E 测试（Playwright）
├── scripts/                   # 脚本
│   ├── seed.ts               # 开发种子数据
│   ├── migrate.ts            # 运行数据库迁移
│   └── export-schema.ts     # 导出 Schema 类型
├── public/                    # 静态资源
│   ├── images/
│   └── fonts/
├── types/                     # 全局 TypeScript 类型
│   ├── next-auth.d.ts       # NextAuth 类型扩展
│   └── stripe.d.ts         # Stripe 类型扩展
├── config/                    # 配置文件
│   ├── site.ts               # 站点配置
│   └── menu.ts              # 菜单配置
├── .env.example             # 环境变量示例（不允许提交 .env）
├── .env.local               # 本地环境变量（gitignore）
├── CLAUDE.md                # 本文件
├── next.config.ts            # Next.js 配置
├── tailwind.config.ts        # Tailwind 配置
├── tsconfig.json            # TypeScript 配置
├── drizzle.config.ts         # Drizzle 配置
├── vitest.config.ts         # Vitest 配置
├── playwright.config.ts      # Playwright 配置
└── package.json
```

### 结构决策理由

1. **`app/` 使用路由分组 `(auth)/` 和 `(dashboard)/`**
   - 让 `layout.tsx` 可以针对不同路由组做不同布局
   - 例如：`(dashboard)/layout.tsx` 包含认证检查，`(auth)/layout.tsx` 包含游客检查

2. **`components/ui/` 不允许修改**
   - 这是 shadcn/ui 的原生组件，修改后无法升级
   - 业务定制应通过 `components/forms/` 或 wrapper 组件实现

3. **`lib/` 必须是纯逻辑，不允许引入 React**
   - 防止客户端打包体积膨胀
   - 所有 SSR/SSG 相关的逻辑在 `app/` 中处理

4. **`sql/` 目录存放原生 SQL**
   - Drizzle ORM 无法覆盖所有 SQLite 特性（如触发器、视图）
   - 复杂查询用原生 SQL 性能更好，且可审查

---

## 三、数据库约定（SQLite + Drizzle）

### 3.1 Schema 定义规范

```typescript
// drizzle/schema.ts
import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';

// 用户表
export const users = sqliteTable('users', {
  id: text('id').primaryKey(),  // UUID v7（有序 UUID）
  email: text('email').notNull().unique(),
  name: text('name'),
  avatarUrl: text('avatar_url'),
  role: text('role').notNull().default('user'),  // 'user' | 'admin'
  emailVerified: integer('email_verified', { mode: 'boolean' }).notNull().default(false),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
  deletedAt: integer('deleted_at', { mode: 'timestamp' }),  // 软删除
});

// 账户表（NextAuth 需要）
export const accounts = sqliteTable('accounts', {
  id: text('id').primaryKey(),
  userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  type: text('type').notNull(),
  provider: text('provider').notNull(),
  providerAccountId: text('provider_account_id').notNull(),
  refresh_token: text('refresh_token'),
  access_token: text('access_token'),
  expires_at: integer('expires_at'),
  token_type: text('token_type'),
  scope: text('scope'),
  id_token: text('id_token'),
  session_state: text('session_state'),
});

// 订阅表（SaaS 核心）
export const subscriptions = sqliteTable('subscriptions', {
  id: text('id').primaryKey(),
  userId: text('user_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  stripeCustomerId: text('stripe_customer_id'),
  stripeSubscriptionId: text('stripe_subscription_id'),
  plan: text('plan').notNull(),  // 'free' | 'pro' | 'enterprise'
  status: text('status').notNull(),  // 'active' | 'canceled' | 'past_due'
  currentPeriodStart: integer('current_period_start', { mode: 'timestamp' }).notNull(),
  currentPeriodEnd: integer('current_period_end', { mode: 'timestamp' }).notNull(),
  cancelAtPeriodEnd: integer('cancel_at_period_end', { mode: 'boolean' }).notNull().default(false),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
});

// 审计日志表（合规要求）
export const auditLogs = sqliteTable('audit_logs', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => users.id, { onDelete: 'set null' }),
  action: text('action').notNull(),  // 'login' | 'logout' | 'update_profile' | ...
  resource: text('resource'),  // 'user' | 'subscription' | ...
  resourceId: text('resource_id'),
  metadata: text('metadata', { mode: 'json' }),  // JSON 字符串
  ipAddress: text('ip_address'),
  userAgent: text('user_agent'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().default(sql`(unixepoch())`),
});

// 索引定义
export const usersIndex = sqliteIndex('users_email_idx').on(users.email);
export const subscriptionsIndex = sqliteIndex('subscriptions_user_id_idx').on(subscriptions.userId);
export const auditLogsIndex = sqliteIndex('audit_logs_user_id_idx').on(auditLogs.userId);
export const auditLogsIndex2 = sqliteIndex('audit_logs_created_at_idx').on(auditLogs.createdAt);
```

### 3.2 迁移规范

```bash
# 开发环境：快速原型（不生成迁移文件）
pnpm drizzle-kit push:sqlite

# 生产环境：生成迁移文件（必须审查）
pnpm drizzle-kit generate:sqlite

# 执行迁移
pnpm drizzle-kit migrate:sqlite
```

**规则**：
1. 每次 `generate:sqlite` 后，必须手动检查生成的 SQL 文件
2. SQLite 不支持 `ALTER TABLE DROP COLUMN`，如需删列，必须创建新表并复制数据
3. 迁移文件命名规范：`0001_init.sql`, `0002_add_audit_logs.sql`, ...
4. 禁止在迁移文件中使用 `DROP TABLE`（除非是 revert）

### 3.3 查询规范

```typescript
// ✅ 正确：使用 Drizzle 查询构建器
import { db } from '@/lib/db';
import { users } from '@/drizzle/schema';
import { eq } from 'drizzle-orm';

export async function getUserById(id: string) {
  const [user] = await db.select().from(users).where(eq(users.id, id)).limit(1);
  return user;
}

// ❌ 错误：拼接 SQL 字符串（SQL 注入风险）
export async function getUserByIdBad(id: string) {
  return db.run(`SELECT * FROM users WHERE id = '${id}'`);  // DANGEROUS!
}

// ✅ 正确：复杂查询使用原生 SQL（需参数化）
export async function getUsersWithSubscriptionStats() {
  return db.run({
    sql: `
      SELECT 
        u.id, 
        u.email, 
        u.name,
        s.plan,
        s.status
      FROM users u
      LEFT JOIN subscriptions s ON u.id = s.user_id
      WHERE u.deleted_at IS NULL
      ORDER BY u.created_at DESC
      LIMIT $1 OFFSET $2
    `,
    args: [limit, offset],
  });
}
```

---

## 四、Server Component 与 Client Component 模式

### 4.1 Server Component（默认）

```typescript
// app/(dashboard)/overview/page.tsx
// 默认就是 Server Component（不在 'use client'）

import { Suspense } from 'react';
import { getUsers } from '@/lib/db';  // 直接调用数据库
import { UsersTable } from './UsersTable';  // Client Component
import { UsersTableSkeleton } from './skeleton';

export default async function OverviewPage() {
  // ✅ 直接在 Server Component 中查询数据库
  const users = await getUsers();
  
  return (
    <div>
      <h1>用户管理</h1>
      {/* ✅ Streaming SSR：Suspense 边界 */}
      <Suspense fallback={<UsersTableSkeleton />}>
        <UsersTable users={users} />
      </Suspense>
    </div>
  );
}
```

### 4.2 Client Component（交互必需）

```typescript
// components/forms/LoginForm.tsx
'use client';  // 必须显式声明

import { useState } from 'react';
import { useRouter } from 'next/navigation';  // App Router 的 useRouter
import { signIn } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const result = await signIn('credentials', {
      email,
      password,
      redirect: false,
    });
    if (result?.error) {
      setError('登录失败，请检查邮箱和密码');
    } else {
      router.push('/dashboard/overview');
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <Button type="submit">登录</Button>
      {error && <p className="text-red-500">{error}</p>}
    </form>
  );
}
```

### 4.3 Server Action（表单提交）

```typescript
// app/(dashboard)/settings/actions.ts
'use server';  // 必须显式声明

import { revalidatePath } from 'next/cache';
import { auth } from '@/lib/auth';
import { db } from '@/lib/db';
import { users } from '@/drizzle/schema';
import { eq } from 'drizzle-orm';
import { z } from 'zod';

const UpdateProfileSchema = z.object({
  name: z.string().min(2).max(50),
  email: z.string().email(),
});

export async function updateProfile(formData: FormData) {
  // 1. 认证检查
  const session = await auth();
  if (!session?.user?.id) {
    return { error: '未登录' };
  }

  // 2. 输入验证
  const result = UpdateProfileSchema.safeParse({
    name: formData.get('name'),
    email: formData.get('email'),
  });
  if (!result.success) {
    return { error: result.error.errors[0].message };
  }

  // 3. 数据库更新
  await db.update(users)
    .set({ 
      name: result.data.name, 
      email: result.data.email,
      updatedAt: new Date(),
    })
    .where(eq(users.id, session.user.id));

  // 4. 重新验证缓存
  revalidatePath('/dashboard/settings');

  return { success: true };
}
```

**Server Action 规则**：
1. 必须以 `'use server';` 开头
2. 必须验证用户权限（不能信任客户端传入的 userId）
3. 必须使用 Zod 验证输入
4. 更新数据后必须调用 `revalidatePath()` 清除缓存

---

## 五、API Route 规范

### 5.1 REST API 示例

```typescript
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/lib/auth';
import { db } from '@/lib/db';
import { users } from '@/drizzle/schema';
import { eq } from 'drizzle-orm';
import { z } from 'zod';

// GET /api/users?page=1&limit=10
export async function GET(request: NextRequest) {
  // 1. 认证
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // 2. 参数验证
  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get('page') || '1', 10);
  const limit = parseInt(searchParams.get('limit') || '10', 10);
  if (page < 1 || limit < 1 || limit > 100) {
    return NextResponse.json({ error: 'Invalid parameters' }, { status: 400 });
  }

  // 3. 查询数据库
  const offset = (page - 1) * limit;
  const userList = await db.select().from(users)
    .where(eq(users.deletedAt, null))
    .limit(limit)
    .offset(offset);

  return NextResponse.json({ users: userList });
}

// POST /api/users
export async function POST(request: NextRequest) {
  // 1. 认证（仅管理员）
  const session = await auth();
  if (session?.user?.role !== 'admin') {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  }

  // 2. 请求体验证
  const body = await request.json();
  const result = z.object({
    email: z.string().email(),
    name: z.string().min(2),
    role: z.enum(['user', 'admin']).default('user'),
  }).safeParse(body);
  if (!result.success) {
    return NextResponse.json({ error: result.error.errors }, { status: 400 });
  }

  // 3. 创建用户
  const [newUser] = await db.insert(users).values({
    id: crypto.randomUUID(),
    email: result.data.email,
    name: result.data.name,
    role: result.data.role,
  }).returning();

  return NextResponse.json({ user: newUser }, { status: 201 });
}
```

### 5.2 Webhook 安全（Stripe）

```typescript
// app/api/webhooks/stripe/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { stripe } from '@/lib/stripe';
import { db } from '@/lib/db';
import { subscriptions } from '@/drizzle/schema';
import { eq } from 'drizzle-orm';

export async function POST(request: NextRequest) {
  // 1. 验证 Stripe 签名
  const signature = request.headers.get('stripe-signature');
  if (!signature) {
    return NextResponse.json({ error: 'Missing signature' }, { status: 400 });
  }

  const body = await request.text();  // 必须用 text()，不能 json()
  let event;
  try {
    event = stripe.webhooks.constructEvent(body, signature, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch (err) {
    console.error('Webhook signature verification failed:', err);
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
  }

  // 2. 处理事件
  switch (event.type) {
    case 'invoice.paid':
      const invoice = event.data.object;
      // 更新订阅状态
      await db.update(subscriptions)
        .set({ status: 'active' })
        .where(eq(subscriptions.stripeSubscriptionId, invoice.subscription));
      break;
    case 'invoice.payment_failed':
      // 标记订阅为 past_due
      break;
    default:
      console.log(`Unhandled event type: ${event.type}`);
  }

  return NextResponse.json({ received: true });
}

// 必须禁用 Next.js 的 body parser（Stripe 需要原始 body）
export const config = {
  api: {
    bodyParser: false,
  },
};
```

---

## 六、认证规范（NextAuth.js v5）

```typescript
// lib/auth.ts
import NextAuth from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { db } from './db';
import { users } from '@/drizzle/schema';
import { eq } from 'drizzle-orm';
import bcrypt from 'bcrypt';

export const { handlers, auth, signIn, signOut } = NextAuth({
  secret: process.env.NEXTAUTH_SECRET,
  session: {
    strategy: 'jwt',  // 使用 JWT（无需数据库 session 表）
  },
  providers: [
    CredentialsProvider({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        // 查询用户
        const [user] = await db.select().from(users)
          .where(eq(users.email, credentials.email as string))
          .limit(1);
        
        if (!user || !user.passwordHash) {
          return null;
        }

        // 验证密码
        const isValid = await bcrypt.compare(credentials.password as string, user.passwordHash);
        if (!isValid) {
          return null;
        }

        return {
          id: user.id,
          email: user.email,
          name: user.name,
          role: user.role,
        };
      },
    }),
    // 可选：OAuth 提供商
    // GoogleProvider({ clientId: process.env.GOOGLE_CLIENT_ID!, clientSecret: process.env.GOOGLE_CLIENT_SECRET! }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = user.role;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.role = token.role as string;
      }
      return session;
    },
  },
  pages: {
    signIn: '/login',  // 自定义登录页
  },
});
```

**认证规则**：
1. Server Component 中使用 `auth()` 获取会话
2. API Route 中使用 `auth()` 或 `getServerSession()`
3. Client Component 中使用 `useSession()`（需要从 `next-auth/react` 导入）
4. Middleware 中使用 `getToken()` 验证 JWT

---

## 七、测试策略

### 7.1 单元测试（Vitest）

```typescript
// tests/lib/validators.test.ts
import { describe, it, expect } from 'vitest';
import { UpdateProfileSchema } from '@/lib/validators';

describe('UpdateProfileSchema', () => {
  it('should validate correct input', () => {
    const result = UpdateProfileSchema.safeParse({
      name: 'John Doe',
      email: 'john@example.com',
    });
    expect(result.success).toBe(true);
  });

  it('should reject invalid email', () => {
    const result = UpdateProfileSchema.safeParse({
      name: 'John Doe',
      email: 'invalid-email',
    });
    expect(result.success).toBe(false);
  });
});
```

### 7.2 API 测试（Vitest + supertest）

```typescript
// tests/api/users.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import request from 'supertest';
import { createServer } from '@/tests/utils/createServer';

describe('GET /api/users', () => {
  let server: any;

  beforeAll(async () => {
    server = await createServer();  // 创建测试服务器
  });

  afterAll(async () => {
    await server.close();
  });

  it('should return 401 without auth', async () => {
    const res = await request(server).get('/api/users');
    expect(res.status).toBe(401);
  });

  it('should return users with auth', async () => {
    const agent = request.agent(server);
    await agent.post('/api/auth/signin').send({
      email: 'test@example.com',
      password: 'password',
    });
    const res = await agent.get('/api/users');
    expect(res.status).toBe(200);
    expect(res.body.users).toBeInstanceOf(Array);
  });
});
```

### 7.3 E2E 测试（Playwright）

```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test('login flow', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  
  await page.fill('input[name="email"]', 'test@example.com');
  await page.fill('input[name="password"]', 'password');
  await page.click('button[type="submit"]');
  
  await page.waitForURL('http://localhost:3000/dashboard/overview');
  await expect(page.locator('h1')).toHaveText('用户管理');
});
```

---

## 八、部署指南

### 8.1 Vercel 部署（推荐）

```bash
# 1. 安装 Vercel CLI
pnpm add -g vercel

# 2. 登录
vercel login

# 3. 部署（生产环境）
vercel --prod

# 4. 设置环境变量
vercel env add DATABASE_URL
vercel env add NEXTAUTH_SECRET
vercel env add STRIPE_SECRET_KEY
vercel env add STRIPE_WEBHOOK_SECRET
```

**Vercel 环境变量清单**：
```
DATABASE_URL=libsql://your-database.turso.io
NEXTAUTH_SECRET=your-secret-key-min-32-chars
NEXTAUTH_URL=https://your-app.vercel.app
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 8.2 Docker 部署（VPS）

```dockerfile
# Dockerfile
FROM node:22-alpine AS base

# 安装 pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# 安装依赖
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# 构建
COPY . .
RUN pnpm build

# 生产环境
FROM base AS production
ENV NODE_ENV=production
EXPOSE 3000
CMD ["pnpm", "start"]
```

```bash
# 构建 Docker 镜像
docker build -t my-saas-app .

# 运行容器
docker run -d \
  -p 3000:3000 \
  -e DATABASE_URL=file:/app/data/db.sqlite \
  -e NEXTAUTH_SECRET=your-secret \
  --name my-saas \
  my-saas-app
```

---

## 九、常用命令速查

```bash
# 开发
pnpm dev              # 启动开发服务器（Turbopack）
pnpm build            # 构建生产版本
pnpm start            # 启动生产服务器
pnpm lint             # ESLint 检查
pnpm type-check       # TypeScript 类型检查

# 数据库
pnpm db:push         # 推送 Schema 到数据库（开发）
pnpm db:generate     # 生成迁移文件
pnpm db:migrate      # 执行迁移
pnpm db:seed         # 种子数据
pnpm db:studio       # 打开 Drizzle Studio

# 测试
pnpm test             # 运行单元测试
pnpm test:ui         # 打开 Vitest UI
pnpm test:e2e        # 运行 E2E 测试
pnpm test:e2e:ui     # 打开 Playwright UI

# 组件
pnpm dlx shadcn@latest add button   # 添加 shadcn 组件
pnpm dlx shadcn@latest add input
```

---

## 十、AI 编程助手提示词模板

### 10.1 创建新功能

```
请在 my-saas-app 项目中实现「用户批量导入」功能：

要求：
1. 在 app/api/users/import/route.ts 创建 API Route（POST）
2. 接受 CSV 文件上传（使用 formidable 或 multer）
3. 验证每一行数据（邮箱格式、去重）
4. 批量插入数据库（使用 transaction）
5. 返回成功/失败统计
6. 写单元测试（tests/api/users-import.test.ts）
7. 写 E2E 测试（tests/e2e/users-import.spec.ts）

参考现有代码风格：
- 认证检查：使用 auth()
- 输入验证：使用 Zod
- 数据库操作：使用 Drizzle ORM
- 错误处理：返回 NextResponse.json({ error }, { status })
```

### 10.2 添加认证

```
请为 my-saas-app 添加「OAuth 登录（GitHub）」：

要求：
1. 在 lib/auth.ts 添加 GitHubProvider
2. 在 .env.example 添加 GITHUB_CLIENT_ID 和 GITHUB_CLIENT_SECRET
3. 在 app/api/auth/[...nextauth]/route.ts 更新 handlers
4. 在 components/forms/LoginForm.tsx 添加 GitHub 登录按钮
5. 更新数据库 schema（如需存储 OAuth 信息）

参考现有代码：
- NextAuth 配置在 lib/auth.ts
- 登录表单在 components/forms/LoginForm.tsx
- 环境变量示例在 .env.example
```

### 10.3 创建 API 端点

```
请在 my-saas-app 中创建「导出用户数据为 CSV」的 API：

要求：
1. 在 app/api/users/export/route.ts 创建 GET Route
2. 查询所有用户（分页可选）
3. 生成 CSV 格式（使用 csv-writer 或手动拼接）
4. 设置响应头 Content-Type: text/csv
5. 写单元测试

参考现有 API 模式：
- 认证：const session = await auth()
- 查询：db.select().from(users).where(...)
- 响应：NextResponse.json(...)
```

---

## 十一、反模式（禁止事项）

### ❌ 1. 不在 Client Component 中查询数据库

```typescript
// ❌ 错误
'use client';
import { db } from '@/lib/db';  // 这会在浏览器中报错！

export function Users() {
  const [users, setUsers] = useState([]);
  useEffect(() => {
    db.query();  // DANGEROUS! 浏览器无法连接数据库
  }, []);
}

// ✅ 正确：使用 API Route 或 Server Action
'use client';
export function Users() {
  const [users, setUsers] = useState([]);
  useEffect(() => {
    fetch('/api/users').then(res => res.json()).then(data => setUsers(data.users));
  }, []);
}
```

### ❌ 2. 不使用 `any` 类型

```typescript
// ❌ 错误
function getUser(id: string): any {  // any 丢失类型安全
  return db.query(`SELECT * FROM users WHERE id = '${id}'`);
}

// ✅ 正确
import { InferSelectModel } from 'drizzle-orm';
import { users } from '@/drizzle/schema';

type User = InferSelectModel<typeof users>;

function getUser(id: string): Promise<User | undefined> {
  return db.select().from(users).where(eq(users.id, id)).limit(1);
}
```

### ❌ 3. 不在 `use server` 中信任客户端传入的 userId

```typescript
// ❌ 错误
'use server';
export async function updateProfile(formData: FormData) {
  const userId = formData.get('userId');  // 客户端可以伪造！
  await db.update(users).set(...).where(eq(users.id, userId));
}

// ✅ 正确
'use server';
export async function updateProfile(formData: FormData) {
  const session = await auth();
  if (!session?.user?.id) throw new Error('Unauthorized');
  await db.update(users).set(...).where(eq(users.id, session.user.id));
}
```

### ❌ 4. 不使用 `prisma migrate dev` 在生产环境

```bash
# ❌ 错误（生产环境）
pnpm prisma migrate dev  # 会删除数据库！

# ✅ 正确（生产环境）
pnpm prisma db push  # 或 pnpm drizzle-kit migrate
```

### ❌ 5. 不在 API Route 中验证 Webhook 签名

```typescript
// ❌ 错误
export async function POST(request: NextRequest) {
  const event = await request.json();  // 任何人都可以伪造请求！
  // 处理事件...
}

// ✅ 正确
export async function POST(request: NextRequest) {
  const signature = request.headers.get('stripe-signature');
  const event = stripe.webhooks.constructEvent(await request.text(), signature, process.env.STRIPE_WEBHOOK_SECRET);
  // 处理事件...
}
```

---

## 十二、故障排查

### 问题 1：SQLite 数据库被锁定

**原因**：多个进程同时写入 SQLite。

**解决**：
```typescript
// 使用 better-sqlite3 的连接池
import Database from 'better-sqlite3';
const db = new Database('db.sqlite', { verbose: console.log });
db.pragma('journal_mode = WAL');  // 启用 WAL 模式（支持并发读）
```

### 问题 2：NextAuth 在生产环境无法正常认证

**原因**：`NEXTAUTH_SECRET` 未设置或 `NEXTAUTH_URL` 不正确。

**解决**：
```bash
# 生成 NEXTAUTH_SECRET
openssl rand -base64 32

# 在 .env 中设置
NEXTAUTH_SECRET=your-generated-secret
NEXTAUTH_URL=https://your-domain.com
```

### 问题 3：Server Action 在 production 返回 404

**原因**：Next.js 15 需要显式绑定 Server Action。

**解决**：
```typescript
// 在 form 中直接使用 Server Action
<form action={updateProfile}>
  <input name="name" />
  <button type="submit">保存</button>
</form>

// 如果需要通过 JavaScript 调用，必须使用 bind
const updateProfileBound = updateProfile.bind(null, formData);
await updateProfileBound();
```

---

## 十三、性能优化清单

- [ ] 启用 Next.js 的 `next/future/image` 代替 `next/image`（更好性能）
- [ ] 为数据库查询添加索引（参见 `drizzle/schema.ts` 中的索引定义）
- [ ] 使用 Redis 缓存会话数据（可选，高并发场景）
- [ ] 为静态页面启用 ISR（增量静态再生成）
- [ ] 使用 Turbopack 加速开发（`pnpm dev` 默认启用）
- [ ] 为大型列表添加虚拟滚动（使用 `@tanstack/react-virtual`）
- [ ] 启用 Gzip/Brotli 压缩（Vercel 自动启用）
- [ ] 使用 `next/dynamic` 懒加载大型组件
- [ ] 为 API Route 添加 Rate Limiting（使用 `express-rate-limit` 或 Upstash Rate Limit）

---

## 十四、贡献者注意事项

1. **提交前必须运行**：
   ```bash
   pnpm lint && pnpm type-check && pnpm test
   ```

2. **Commit 规范**（使用 Conventional Commits）：
   ```
   feat: 添加用户批量导入功能
   fix: 修复 NextAuth 在生产环境的认证问题
   docs: 更新 CLAUDE.md 的故障排查章节
   refactor: 将 Prisma 迁移到 Drizzle ORM
   test: 添加 users API 的单元测试
   ```

3. **PR 命名规范**：
   - 必须以 `feat:`、`fix:`、`docs:`、`refactor:`、`test:` 开头
   - 必须关联 Issue（如 `(#123)`）

4. **代码审查清单**：
   - [ ] 是否包含测试？
   - [ ] 是否更新了文档？
   - [ ] 是否有性能回归？
   - [ ] 是否破坏了现有 API？

---

## 十五、许可证

MIT License

---

**最后更新**：2026-06-15  
**维护者**：chrisyangxiaoqi  
**AI 助手注意事项**：修改此文件后，必须通知所有贡献者重新阅读本文档。
