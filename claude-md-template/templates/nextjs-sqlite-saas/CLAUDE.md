# CLAUDE.md — Next.js 15 App Router + SQLite (better-sqlite3 / Turso)

> Paste vào root của greenfield project. Mọi rule đều có `reason:` — đừng sửa
> khi chưa hiểu lý do. Pin: `next@15`, `react@19`, `better-sqlite3@12`, `node@22`.

## 1. Stack & versions

| Layer | Choice | reason: |
|---|---|---|
| Framework | Next.js 15 App Router | Server Components mặc định, ít JS gửi browser |
| DB | better-sqlite3 (local) / Turso libSQL (prod) | cùng dialect, đổi 1 dòng connection string khi scale |
| Validation | zod | 1 schema dùng cho form + API + env |
| Tests | vitest + Playwright | unit nhanh, e2e cho billing/auth flows |
| Package manager | npm | lockfile chuẩn, CI cache được |

## 2. Dev commands

- `npm run dev` — local (port 3000, Turbopack)
- `npm run build && npm start` — verify production trước khi merge,
  reason: nhiều lỗi chỉ lộ ở build (prerender, env thiếu)
- `npm test` — vitest, bắt buộc xanh trước commit
- `npm run db:migrate` — chạy migration (xem §4)

## 3. Folder structure

```
app/                        # route = thư mục, UI = page.tsx
  (marketing)/              # route group, không ảnh hưởng URL
  api/<name>/route.ts       # 1 file/route, chỉ GET/POST/PUT/DELETE
lib/
  db.ts                     # singleton better-sqlite3, WAL mode
  actions.ts                # Server Actions — mọi mutation qua đây, KHÔNG fetch API nội bộ
  env.ts                    # zod parse process.env, fail-fast khi thiếu (xem §7)
components/
  ui/                       # presentational only, không import db
  <Feature>.tsx             # PascalCase, 1 component tối đa 2 files (tsx + test)
migrations/
  001_init.sql              # số thứ tự + tên, KHÔNG sửa file đã merge
```

reason: 1 chỗ cho mỗi loại code — Claude mới không hỏi "db để đâu".

## 4. Naming conventions

- Files: kebab-case (`user-card.tsx`); components: PascalCase; DB tables/columns: snake_case.
- reason: tránh lỗi case-sensitive khi deploy Linux trong khi dev macOS.

## 5. SQL / migration rules

1. Schema đổi = migration mới, số tiếp theo. Không sửa migration đã merge —
   reason: dev/prod drift, mất khả năng rollback.
2. Mọi query qua `lib/db.ts` singleton với `pragma journal_mode = WAL` —
   reason: SQLite default rollback-journal lock cả file khi write.
3. Không `SELECT *` — liệt kê cột — reason: thêm cột không vỡ API response.
4. Seed chỉ trong `migrations/seed.sql`, không hardcode trong code.

Ví dụ migration (`migrations/002_add_plan.sql`):
```sql
ALTER TABLE users ADD COLUMN plan TEXT NOT NULL DEFAULT 'free';
```

## 6. Component patterns

- Server Component mặc định; `'use client'` chỉ khi cần state/event —
  reason: bundle nhỏ, SEO miễn phí.
- Data fetch trong Server Component bằng `lib/actions.ts`, không `useEffect` fetch —
  reason: tránh waterfall + double-fetch.
- Form = Server Action + `useFormStatus`, không API route trung gian —
  reason: 1 roundtrip, type-safe end-to-end.

## 7. Env contract (`lib/env.ts` + `.env.example`)

```ts
// lib/env.ts
import { z } from "zod";
export const env = z.object({
  DATABASE_URL: z.string().default("file:./dev.db"),
  STRIPE_SECRET_KEY: z.string().min(1),
  NEXT_PUBLIC_APP_URL: z.string().url(),
}).parse(process.env);
```
- reason: crash lúc boot với message rõ thay vì `undefined` lúc runtime.
- Không thêm env var mới nếu chưa có trong `.env.example` —
  reason: onboard người mới gãy.

## 8. CI and release gates (merge = phải xanh)

`lint → typecheck → test → migrate (dry-run) → build → playwright (signup-login-billing)`.
reason: billing/auth là 2 flows mất tiền thật khi hỏng — e2e bắt buộc.

## 9. What we DON'T do (and why)

- Không ORM nặng (<10 tables): better-sqlite3 + SQL thẳng —
  reason: ít magic, migrate là file SQL đọc được.
- Không fetch (`/api/...`) từ Server Component tới chính mình —
  reason: gọi action trực tiếp, đỡ 1 network hop.
- Không `any` TypeScript — `unknown` + narrow —
  reason: `any` lan qua props như virus.
- Không `console.log` trong code merge — dùng `lib/logger.ts` —
  reason: log prod phải có level + context.
