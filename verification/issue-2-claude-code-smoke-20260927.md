# Claude Code 2.1.283 smoke run (2026-09-27)

- Run time: 2026-09-27T02:46:45+08:00 (local time)
- Claude Code: 2.1.283
- Fixture: a fresh `create-next-app@15.5.26` App Router project; no dependencies installed. The bounty's `CLAUDE.md` was copied to the project root and six small project/auth/database stubs were added.
- Mode: `plan`, read-only tools (`Read`, `Glob`, `Grep`), project/local setting sources, no session persistence. API-key and gateway environment variables were removed from this process. No source files were edited, no commands or migrations were run, and no dependencies were installed.
- Prompt: asks for a workspace-scoped `archiveProject` implementation plan, the real files and current package scripts, an append-only migration, tests, and missing evidence; it explicitly forbids editing and clarification questions.
- Result: Claude Code returned JSON with `subtype=success`, `is_error=false`, `stop_reason=end_turn`, 15 turns, and a 78.6-second duration. It read the actual manifest and stubs, identified the missing session/database implementation and scripts, proposed tenant-scoped SQL plus an append-only migration, and did not ask a question.
- Limitation: this verifies instruction comprehension on a greenfield scaffold. It does not verify dependency installation, build/tests, database behavior, or an implemented feature. The wrapper did not capture the CLI process exit code because its post-run zsh variable name was reserved; the successful Claude result fields above come directly from its JSON response.

## Exact prompt

> Read CLAUDE.md, package.json, tsconfig.json, next.config.ts, and the existing project feature/database/auth files. We need to implement an archiveProject server action scoped to the authenticated workspace. Before coding, give a concise plan grounded only in actual files: relevant files, authorization and SQL constraints, a safe append-only migration, tests/commands that exist now versus those that would need adding, and any facts that must be verified before implementation. Do not edit files, run commands, install dependencies, or ask clarifying questions. Be explicit where auth or database behavior is only a stub.

## Raw Claude Code response

# archiveProject 实施计划（只读分析，未改动任何文件）

我读了 `CLAUDE.md`、`package.json`、`tsconfig.json`、`next.config.ts`、`eslint.config.mjs`、`.gitignore`，以及 `src/` 下的全部 feature、db 和 auth 文件。当前会话没有 Write 或 ExitPlanMode 工具，所以计划直接写在这里，没有生成计划文件。

## 1. 现状：认证和数据库都只是占位

| 文件 | 实际内容 | 状态 |
|---|---|---|
| `src/features/projects/server/mutations.ts:1` | `export async function archiveProject() {}` | 空函数：没有参数，没有 `'use server'` 或 `server-only` |
| `src/features/projects/server/queries.ts:1` | `export async function getProject() {}` | 空函数 |
| `src/server/db/client.ts:1` | `getDb()` 直接抛出 `'Database not configured'` | **数据库完全没实现**：没有连接、单例、pragma，也没有 `better-sqlite3` 依赖 |
| `src/server/auth/session.ts:1` | 只有 `type Session = { userId; workspaceId }` | **认证完全没实现**：没有 `getSession()`，也没有 cookie 或 token 校验 |
| `src/server/db/migrations/0001_create_projects.sql` | `projects(id TEXT PK, workspace_id TEXT NOT NULL, name TEXT NOT NULL)` | 没有 workspaces 表和外键，没有迁移运行器，也没有迁移记录表 |
| `src/app/(app)/projects/[projectId]/page.tsx` | 静态 `<main>Project</main>` | 没有 `await params`，没有 runtime 声明，也没有 UI |
| `package.json` | 脚本只有 `dev` / `build` / `start` / `lint`；依赖是 next 15.5.26 和 react 19.1.0 | 没有 `better-sqlite3`、`server-only` 或测试框架 |
| `next.config.ts` | 空配置 | — |
| `tsconfig.json` | 开了 `strict`，别名 `@/* → ./src/*` | — |

另外几处和 CLAUDE.md 不一致的地方：
- **没有 `package-lock.json`**，也没有 `node_modules`，所以无法确认实际安装的 Next 版本。
- 没有 `.nvmrc`、`.node-version`，`package.json` 里也没有 `engines`。
- 没有 `.env.example`。`.gitignore` 的 `.env*` 规则会把它一起忽略，需要加一条 `!.env.example`。
- `src/server`、`src/features`、`src/app/(app)` 都还没提交过 git。

## 2. 要改的文件（按依赖顺序）

1. **`src/server/db/client.ts`**
   - 加 `import 'server-only'`。
   - 创建 `better-sqlite3` 单例，挂在 `globalThis` 上，热重载时不重复连接。
   - 路径从仅服务端可用的环境变量读取。
   - 每个连接都设置 `PRAGMA foreign_keys = ON` 和有上限的 `busy_timeout`。WAL 只在确认存储支持时才开。
2. **`src/server/db/migrate.ts`**（新建）
   - 按文件名顺序执行 `migrations/*.sql`。
   - 已执行的 ID 记在 `schema_migrations` 表里，每个迁移在一个事务里跑。
3. **`src/server/db/migrations/0002_add_project_archive.sql`**（新建，见第 4 节）。
4. **`src/server/auth/session.ts`**
   - 新增 `getSession(): Promise<Session | null>`。
   - **会话怎么签发、怎么校验，仓库里完全没有依据**，只能先定接口，然后确认实现方式（见第 6 节）。
5. **SQL 层**：`src/features/projects/server/projectRepository.ts`（新建，`server-only`，**不加** `'use server'`）
   - 提供 `archiveProjectInWorkspace(db, { workspaceId, projectId, archivedAt })`。
6. **`src/features/projects/server/mutations.ts`**
   - 改成 `'use server'` 文件，导出 `archiveProject` 这个 Server Action。
   - SQL 必须放在别的文件：`'use server'` 文件里导出的每个 async 函数都会变成客户端可调用的接口。如果把一个接收 `workspaceId` 参数的 SQL 函数导出在这里，就等于开了跨租户的口子。
7. **`queries.ts`**：`getProject` 的查询条件加上 `workspace_id`，并且明确已归档项目的读取方式。
8. **`page.tsx`**
   - 加 `export const runtime = 'nodejs'`，并执行 `await params`。
   - 归档按钮只做成最小的表单或 Client 组件，页面其余部分保持 Server Component。

## 3. 授权和 SQL 约束

Action 按固定顺序执行：

1. **校验输入**：`projectId` 必须是非空字符串，并限制最大长度。仓库里没有 zod，CLAUDE.md 也不允许为一次性需求加依赖，所以先手写校验。
2. **认证**：调用 `getSession()`，拿不到就拒绝。
3. **授权**：`workspaceId` **只能从 session 取**。表单里的 `workspace_id`、`user_id` 一律不读。
4. **写入**：

```sql
UPDATE projects
   SET archived_at = ?
 WHERE id = ? AND workspace_id = ? AND archived_at IS NULL
```

   - 所有值用预编译语句绑定。
   - `changes === 0` 时，在同一个同步事务里用 `SELECT 1 ... WHERE id = ? AND workspace_id = ?` 区分"已归档"（按幂等成功处理）和"不存在或属于其他 workspace"。后一种情况统一返回 not found，不暴露项目是否存在。
   - 事务回调里不 `await`，也不做任何外部调用。
5. **提交之后**才调用 `revalidatePath('/projects/[projectId]', 'page')` 或 redirect，写入失败时不能返回成功。
6. **日志**：不记录 session 内容。

## 4. 只追加的迁移

新建 `0002_add_project_archive.sql`，不修改 `0001`：

```sql
ALTER TABLE projects ADD COLUMN archived_at TEXT
  CHECK (archived_at IS NULL OR archived_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T*Z');
CREATE INDEX projects_workspace_id_archived_at_idx ON projects (workspace_id, archived_at);
```

- 时间统一用 ISO-8601 UTC 文本。
- SQLite 的 `ADD COLUMN` 允许带 CHECK 约束。3.37 及以上版本会用它校验已有行，这里已有行都是 NULL，不受影响。
- 暂时不给 `workspace_id` 加外键，因为还没有 workspaces 表。这一点需要确认（见第 6 节）。
- 按规范，迁移要跑两遍，然后执行 `PRAGMA foreign_key_check` 和 `PRAGMA integrity_check`。

## 5. 命令：现在能用的和需要新增的

| 命令 | 状态 |
|---|---|
| `npm run dev` / `build` / `start` / `lint` | ✅ 脚本已存在，但没有 `node_modules`，需要先 install |
| `npm run typecheck`（`tsc --noEmit`） | ❌ 缺失，需要新增 |
| `npm test` | ❌ 缺失，也没有任何测试文件或测试框架 |
| `npm run db:migrate` | ❌ 缺失，也没有迁移运行器 |

需要新增的依赖：`better-sqlite3`、`@types/better-sqlite3`、`server-only`，以及一个测试框架（建议 vitest）。首次 install 会生成 `package-lock.json`，需要一起提交。

测试框架注意：`server-only` 在非 react-server 环境下会直接抛错，vitest 里要做 alias 或 mock。

需要补的测试：
- **数据库**：`foreign_keys` 确实已开启；迁移可以重复执行。
- **仓库层**：
  - 同一 workspace 能归档成功；
  - **其他 workspace 的合法 ID 返回 0 行，状态不变**；
  - 重复归档是幂等的；
  - 不存在的 ID 返回 not found。
- **Action 层**：
  - 没有 session 时拒绝；
  - 表单里伪造的 `workspace_id` 被忽略。

## 6. 动手前必须确认的事

1. **会话机制**：session 用什么签发和校验（cookie、JWT、还是某个库）？目前只有一个类型定义。
2. **权限模型**：workspace 里任何成员都能归档，还是需要特定角色？仓库里没有成员表或角色表。
3. **0001 是否已在任何共享环境执行过**。它还没进 git，大概率没有；但无论是否执行过，都按新增 0002 处理。
4. **Next 版本和 Node 版本**：没有 lockfile 和 `node_modules`，需要确认实际安装的 Next 版本和 Node LTS 版本，然后写进 `engines` 和 `.nvmrc`。
5. **部署目标**：能否保留持久化磁盘、是否支持 WAL、会不会上 serverless。这决定能不能用本地 `better-sqlite3`，还是要换成 Turso/libSQL。
6. **归档的业务语义**：已归档项目在 `getProject` 里是隐藏还是只读？需不需要取消归档？要不要记录 `archived_by_user_id` 做审计？
7. **环境变量**：数据库路径用哪个变量名，开发和测试环境的默认路径放在哪里。
