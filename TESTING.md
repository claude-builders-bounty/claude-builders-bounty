# Testing Notes

## Goal
Verify that the attached `CLAUDE.md` is specific enough for a greenfield Next.js 15 + SQLite SaaS project and reduces clarifying questions.

## Manual validation checklist

- The file states a concrete stack and runtime split.
- The file defines a folder layout, not just vague guidance.
- The file gives migration and SQL rules that are SQLite-aware.
- The file lists anti-patterns with reasons.
- The file is reusable on a greenfield project without requiring repo-specific edits.

## Expected outcome
A coding agent should be able to:
- place business logic in `services/`
- avoid inline SQL in UI files
- prefer Server Components by default
- know where migrations belong
- avoid inventing broad architecture before it is needed
