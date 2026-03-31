# CLAUDE.md - Next.js 15 + SQLite SaaS 项目指南

> 这是一个经过实战验证的、有明确观点的 CLAUDE.md 模板。
> 适用于 Next.js 15 App Router + SQLite (better-sqlite3) 项目。

---

## 技术栈

| 类别 | 技术 | 版本 | 选择理由 |
|------|------|------|----------|
| 框架 | Next.js | 15.x | App Router, Server Components |
| 数据库 | better-sqlite3 | 最新 | 同步API, 性能优秀, 零配置 |
| ORM | 无 | - | 手写SQL, 完全控制 |
| 样式 | Tailwind CSS | 3.x | 实用优先, 不纠结命名 |
| 语言 | TypeScript | 5.x | 类型安全, 重构友好 |

---

## 项目结构

```
my-app/
├── app/                    # Next.js App Router
│   ├── api/               # API路由
│   ├── (auth)/            # 认证路由组
│   ├── dashboard/         # 仪表盘页面
│   ├── layout.tsx         # 根布局
│   └── page.tsx           # 首页
├── lib/                   # 工具函数
│   ├── db.ts             # 数据库连接
│   ├── schema.sql        # 数据库schema
│   └── utils.ts          # 通用工具
├── components/            # React组件
│   ├── ui/               # 基础UI组件
│   └── features/         # 功能组件
├── hooks/                 # 自定义hooks
├── types/                 # TypeScript类型
└── public/                # 静态资源
```

**规则**:
- 所有数据库操作必须在 `lib/db.ts` 中
- API路由只负责HTTP层, 业务逻辑在lib中
- 组件按功能分组, 不是按类型

---

## 数据库约定

### Schema 管理

```sql
-- lib/schema.sql
-- 版本控制你的schema

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

### 连接模式

```typescript
// lib/db.ts
import Database from 'better-sqlite3';

const db = new Database('app.db');
db.pragma('journal_mode = WAL'); // 必须: 并发支持

export default db;
```

### SQL 规则

| ✅ 做 | ❌ 不做 |
|-------|---------|
| 手写SQL | 使用ORM |
| 参数化查询 | 字符串拼接 |
| 显式事务 | 自动提交 |
| 创建索引 | 全表扫描 |

```typescript
// ✅ 正确
const stmt = db.prepare('SELECT * FROM users WHERE email = ?');
const user = stmt.get(email);

// ❌ 错误
const user = db.prepare(`SELECT * FROM users WHERE email = '${email}'`).get();
```

---

## 开发命令

```bash
# 开发
npm run dev          # 启动开发服务器

# 数据库
npm run db:migrate   # 执行schema迁移
npm run db:seed      # 插入测试数据
npm run db:reset     # 重置数据库 ⚠️ 危险

# 代码质量
npm run lint         # ESLint检查
npm run type-check   # TypeScript检查
npm run build        # 生产构建
```

---

## 代码模式

### API 路由

```typescript
// app/api/users/route.ts
import { NextRequest } from 'next/server';
import db from '@/lib/db';

export async function GET() {
  const users = db.prepare('SELECT * FROM users').all();
  return Response.json({ users });
}

export async function POST(req: NextRequest) {
  const { email } = await req.json();
  
  const stmt = db.prepare('INSERT INTO users (email) VALUES (?)');
  const result = stmt.run(email);
  
  return Response.json({ id: result.lastInsertRowid }, { status: 201 });
}
```

### Server Component

```typescript
// app/dashboard/page.tsx
import db from '@/lib/db';

export default function DashboardPage() {
  // 直接在服务端查询
  const stats = db.prepare('SELECT COUNT(*) as count FROM users').get();
  
  return (
    <div>
      <h1>用户数量: {stats.count}</h1>
    </div>
  );
}
```

### 表单处理

```typescript
// app/(auth)/login/page.tsx
export default function LoginPage() {
  async function login(formData: FormData) {
    'use server';
    const email = formData.get('email');
    // 处理登录...
  }
  
  return (
    <form action={login}>
      <input name="email" type="email" required />
      <button type="submit">登录</button>
    </form>
  );
}
```

---

## 反模式 (不要做)

| 反模式 | 为什么 | 替代方案 |
|--------|--------|----------|
| 在Client Component中直接访问数据库 | 安全问题 | 使用API路由或Server Component |
| 使用Prisma/Drizzle等ORM | 增加复杂度, 隐藏SQL | 手写SQL, 完全控制 |
| 每个表一个文件 | 难以追踪关系 | 统一schema.sql |
| 动态SQL拼接 | SQL注入风险 | 参数化查询 |
| 在组件中写业务逻辑 | 难以测试 | 提取到lib/中 |
| 过度抽象 | 增加认知负担 | 重复优于错误抽象 |

---

## 测试策略

```typescript
// 单元测试: 测试纯函数
// 集成测试: 测试API端点
// 不测试: UI细节 (用TypeScript保证)

// lib/db.test.ts
import db from './db';

test('create user', () => {
  const stmt = db.prepare('INSERT INTO users (email) VALUES (?)');
  const result = stmt.run('test@example.com');
  expect(result.changes).toBe(1);
});
```

---

## 部署检查清单

- [ ] `npm run build` 成功
- [ ] `npm run type-check` 无错误
- [ ] 数据库文件在 `.gitignore` 中
- [ ] 环境变量在 `.env.example` 中记录
- [ ] `better-sqlite3` 在 `dependencies` 中 (不是 devDependencies)

---

## 为什么这样设计?

1. **不用ORM**: ORM隐藏了SQL, 导致性能问题和调试困难。手写SQL让你完全控制。

2. **better-sqlite3**: 同步API更简单, 不需要async/await地狱。WAL模式支持并发。

3. **App Router**: Server Components减少客户端JS, 更快加载。

4. **无复杂抽象**: 每个文件都知道自己在做什么。新人5分钟就能理解项目。

---

## 快速开始

```bash
# 1. 创建项目
npx create-next-app@15 my-app --typescript --tailwind --app

# 2. 安装依赖
npm install better-sqlite3
npm install -D @types/better-sqlite3

# 3. 复制本CLAUDE.md到项目根目录

# 4. 创建 lib/schema.sql 和 lib/db.ts

# 5. 开始开发
npm run dev
```

---

*本CLAUDE.md基于实际项目经验, 每个规则都有踩坑血泪史。*
