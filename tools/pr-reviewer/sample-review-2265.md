## Summary

This PR, **Add Next.js SQLite CLAUDE template**, changes 2 file(s) with 544 additions and 0 deletions. The main review focus should be the changed file set, risk-bearing paths, and whether the submitted verification covers the behavior.

## Identified Risks

- `templates/nextjs-sqlite-saas/CLAUDE.md` changes persistence/database behavior; verify migration and rollback paths.
- `templates/nextjs-sqlite-saas/CLAUDE.md` touches network calls; check timeout, retry, and error handling behavior.
- `templates/nextjs-sqlite-saas/CLAUDE.md` is a large change (500 lines), raising review risk.
- `templates/nextjs-sqlite-saas/VALIDATION.md` changes persistence/database behavior; verify migration and rollback paths.

## Improvement Suggestions

- Run the narrowest test command that exercises the changed paths and paste the output into the PR.
- Document any manual verification steps that reviewers cannot reproduce from CI alone.
- Add at least one regression test or fixture that proves the new behavior.
- Preview rendered documentation to catch broken links, heading hierarchy issues, and stale examples.

## Confidence

Medium
