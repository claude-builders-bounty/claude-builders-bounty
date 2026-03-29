# PR Review: docs: Add Common Issues and Troubleshooting section to Getting Started guide

**PR:** [vitejs/vite#22070](https://github.com/vitejs/vite/pull/22070)
**Reviewed:** 2026-03-29T18:46:00Z
**Model:** claude-haiku-4-5-20251001

---

## Summary
This PR adds a new "Common Issues & Troubleshooting" section to Vite's Getting Started documentation, covering 6 common setup problems: port conflicts, ENOENT errors, environment variable exposure, Docker HMR configuration, TypeScript type errors, and cache issues.

## Risk Assessment: Low
Documentation-only change with no impact on runtime behavior.

## Identified Risks
- The `VITE_` prefix requirement for env var exposure is correct but could use a stronger warning about accidentally exposing secrets

## Improvement Suggestions
- Add a troubleshooting entry for `Cannot find module` errors (very common for new users)
- The Docker HMR fix should mention `server.host: '0.0.0.0'` as an alternative
- Consider linking to the official Vite env variables documentation for the env var section

## Code Quality Notes
- Well-structured with clear problem/solution format
- Examples use current Vite 5+ syntax
- All code blocks specify language for syntax highlighting

## Confidence Score: High
High — documentation addition with no code changes; examples are accurate.

## Verdict
APPROVE — Solid troubleshooting guide that addresses the most common Vite setup issues. Minor suggestions above are optional improvements, not blockers.
