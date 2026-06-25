# CLAUDE.md - Next.js 15 + SQLite SaaS 项目指南

## 项目结构
```
src/
├── app/              # Next.js 15 App Router
│   ├── (auth)/       # 认证相关路由
│   ├── (dashboard)/  # 仪表盘路由
│   └── api/          # API 路由
├── components/       # 共享组件
│   ├── ui/           # UI原语 (shadcn/ui)
│   └── features/     # 功能组件
├── lib/              # 工具函数
│   ├── db/           # 数据库操作 (SQLite)
│   ├── auth/         # 认证逻辑
│   └── utils.ts      # 通用工具
├── hooks/            # 自定义hooks
└── types/            # TypeScript类型
```

## 命名规范
- 组件: PascalCase (UserProfile.tsx)
- 工具函数: camelCase (formatDate.ts)
- 路由: kebab-case (user-settings/)
- API路由: 动词+资源 (POST /api/users)

## 数据库规范 (SQLite)
- 使用 Drizzle ORM + Turso/better-sqlite3
- 迁移文件: `drizzle/migrations/`
- Schema: `src/lib/db/schema.ts`
- 所有表必须有 `id`, `created_at`, `updated_at`
- 软删除: `deleted_at` 字段

## 开发命令
```bash
npm run dev        # 开发服务器
npm run build      # 构建
npm run test       # 测试
npm run lint       # 代码检查
npm run db:push    # 数据库迁移
npm run db:studio  # Drizzle Studio
```

## 代码规范
- TypeScript strict 模式
- 使用 `zod` 做运行时验证
- API路由使用 `next-safe-action` 或 Route Handler
- 错误处理: 统一 try-catch + 错误边界
- 状态管理: React Query + URL state

## 反模式 (避免)
- ❌ 在客户端组件直接查询数据库
- ❌ 不使用事务的批量写入
- ❌ 硬编码密钥/配置
- ❌ 忽略 TypeScript 错误
- ❌ 大型 useEffect 替代服务端数据获取
