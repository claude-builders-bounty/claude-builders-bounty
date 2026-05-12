# Next.js + SQLite `CLAUDE.md` Template

Submission for bounty issue #2:
https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2

## Contents

- `CLAUDE.md` — opinionated project rules with explicit reasons
- `validate_template.py` — lightweight validator for acceptance-oriented checks
- `greenfield-test-notes.md` — test notes showing greenfield usage flow

## Why this template is opinionated

This template assumes:
- Next.js 15 App Router
- TypeScript strict mode
- Drizzle migrations
- SQLite local-first workflow (with optional Turso deployment)

It intentionally rejects generic “depends” guidance and provides concrete defaults.

## Local verification

Run:

```bash
python3 validate_template.py
```

Expected output:

```text
OK: template includes required sections and rule reasons.
```
