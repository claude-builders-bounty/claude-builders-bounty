# Next.js + SQLite SaaS CLAUDE.md Template

Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2

## What This Provides

An opinionated `CLAUDE.md` for a greenfield SaaS project using Next.js 15 App Router and SQLite.

It covers:

- stack and versions
- folder structure
- SQL and migration conventions
- component patterns
- auth, billing, errors, tests, and PR checklist
- explicit anti-patterns with reasons

## Usage

Copy `CLAUDE.md` into the root of a new Next.js + SQLite SaaS repository before starting Claude Code.

## Verification

The template is plain Markdown and has no runtime dependencies. Validate by checking that required sections exist:

```powershell
python .\templates\nextjs-sqlite-saas\validate_template.py
```
