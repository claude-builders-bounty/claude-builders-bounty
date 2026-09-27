# CLAUDE.md Template — Opire $75 bounty entry (issue #2)

![template](https://img.shields.io/badge/CLAUDE.md-Next.js15%2BSQLite-blue) ![checks](https://img.shields.io/badge/validate-15%2F15-green)

Opinionated, production-ready `CLAUDE.md` cho greenfield Next.js 15 App Router +
SQLite (better-sqlite3/Turso). Paste vào root là dùng, không sửa.

## Layout
- `templates/nextjs-sqlite-saas/CLAUDE.md` — template (9 sections, 18x `reason:`)
- `validate_template.py` — 15 asserts (sections, pins, reasons, choices, CI)
- `GREENFIELD_TEST_NOTES.md` — cách test paste + smoke prompts

## Test
- `python3 validate_template.py` → 15/15 xanh.
- Paste test: copy CLAUDE.md vào thư mục trống — mọi lệnh/path dùng được ngay.
