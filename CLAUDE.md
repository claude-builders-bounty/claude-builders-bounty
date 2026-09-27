# CLAUDE.md — Next.js 15 App Router + SQLite (better-sqlite3)

> Paste vào root của greenfield project. Mọi rule đều có lý do — đừng sửa
> khi chưa hiểu lý do. Stack pin: next@15, react@19, better-sqlite3@12, node@22.

## Dev commands

- `npm run dev` — chạy local (port 3000, Turbopack)
- `npm run build && npm start` — verify production trước khi merge
- `npm test` — vitest, bắt buộc xanh trước commit
- `npm run db:migrate` — chạy migration (xem quy tắc DB dưới)

## Folder structure

```
app/                # App Router: route = thư mục, UI = page.tsx
  (marketing)/      # route group, không ảnh hưởng URL
  api/<name>/route.ts  # API: 1 file/route, chỉ GET/POST/PUT/DELETE
lib/
  db.ts             # 1 singleton better-sqlite3, WAL mode (lý do: concurrent reads)
  actions.ts        # Server Actions — mọi mutation đi qua đây, KHÔNG fetch API nội bộ
components/
  ui/               # presentational only, không import db
  <Feature>.tsx     # PascalCase, 1 component/2 file max (tsx + test)
migrations/
  001_init.sql      # số thứ tự + tên, KHÔNG sửa file đã merge
```

## Naming

- Files: kebab-case (`user-card.tsx`); components: PascalCase; DB tables/columns: snake_case.
- Lý do: tránh lỗi case-sensitive khi deploy Linux trong khi dev trên macOS.

## DB / migration rules

1. Schema đổi = migration mới, đặt số tiếp theo. Không sửa migration đã merge
   (lý do: dev/prod drift, mất khả năng rollback).
2. Mọi query qua `lib/db.ts` singleton với `pragma journal_mode = WAL`
   (lý do: SQLite default rollback-journal lock cả file khi write).
3. Không SELECT * — liệt kê cột (lý do: thêm cột không vỡ API response).
4. Seed data chỉ trong `migrations/seed.sql`, không hardcode trong code.

## Component patterns

- Server Component mặc định; `'use client'` chỉ khi cần state/event (lý do: bundle nhỏ, SEO).
- Data fetch trong Server Component bằng `lib/actions.ts`, không `useEffect` fetch
  (lý do: tránh waterfall + double-fetch).
- Form = Server Action + `useFormStatus`, không API route trung gian
  (lý do: 1 roundtrip, type-safe).

## What we DON'T do (and why)

- Không ORM nặng (Prisma/Drizzle) cho project <10 tables — better-sqlite3 + SQL thẳng
  ít magic hơn, migrate bằng file SQL đọc được.
- Không fetch (`/api/...`) từ Server Component tới chính mình — gọi action trực tiếp.
- Không `any` TypeScript — `unknown` + narrow (lý do: `any` lan như virus qua props).
- Không env var mới nếu chưa có trong `.env.example` (lý do: onboard người mới gãy).
- Không `console.log` trong code merge — dùng `lib/logger.ts` (lý do: log prod phải có level).
