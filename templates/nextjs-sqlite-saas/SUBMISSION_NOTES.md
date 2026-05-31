# Submission Notes

Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2

## Summary

This package provides an opinionated `CLAUDE.md` for a greenfield Next.js 15 App Router + SQLite SaaS project.

It includes:

- stack and version expectations
- folder structure
- SQLite/Drizzle schema rules
- migration rules
- query and Server Action patterns
- component boundaries
- auth, billing, logging, and testing guidance
- explicit anti-patterns and reasons

## Verification

```powershell
python .\templates\nextjs-sqlite-saas\validate_template.py
```

The validator checks that the required sections and key invariants are present.

## Files

- `templates/nextjs-sqlite-saas/CLAUDE.md`
- `templates/nextjs-sqlite-saas/README.md`
- `templates/nextjs-sqlite-saas/validate_template.py`
