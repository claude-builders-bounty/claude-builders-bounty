# Test log — CLAUDE.md template fixture

Every command documented in CLAUDE.md, executed against the fixture project.

$ node --version
v24.19.0

$ npm install
up to date in 541ms

$ npm run db:migrate
applied 0001_init_items.sql
applied 0002_add_items_archived_at.sql
migrate: 2 applied, 2 total (./data/app.db)

$ npm run db:seed
seed: inserted 3 rows

$ npm run db:reset
reset: removed ./data/app.db
migrate: 2 applied, 2 total (./data/app.db)
seed: inserted 3 rows

$ npm run test
✔ migrations apply, are ordered and are idempotent (122.695956ms)
✔ seed inserts rows once and refuses in production (174.349831ms)
✔ timestamps are epoch milliseconds, not text or seconds (106.208405ms)
✔ WAL is enabled and the documented pragmas live in lib/db.ts (116.531328ms)

$ npm run typecheck

(sin salida = sin errores de tipos)

$ npm run lint

(sin salida = sin avisos)

$ npm run check
ℹ tests 4
ℹ pass 4
ℹ fail 0

$ npm run build
 ✓ Compiled successfully in 2.8s
Route (app)                                 Size  First Load JS
┌ ƒ /                                      134 B         103 kB
├ ○ /_not-found                            993 B         104 kB
└ ƒ /api/items                             134 B         103 kB
○  (Static)   prerendered as static content

$ node check.mjs CLAUDE.md fixture
  ok    seccion presente: stack y versiones
  ok    seccion presente: estructura de carpetas
  ...
  ok    npm run check existe en package.json
  ok    existe: lib/db.ts
  ok    DATABASE_PATH esta en .env.example

RESULTADO: 23 comprobaciones ok, 0 fallos
