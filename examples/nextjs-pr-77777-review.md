## Claude PR Review

### Summary of changes

This PR changes 254 files with +825/-815 lines. The main file types are .mdx (253), .tsx (1), with the largest changes in `docs/01-app/02-guides/self-hosting.mdx`, `docs/01-app/03-building-your-application/10-deploying/02-static-exports.mdx`, `docs/01-app/05-api-reference/02-components/image.mdx`.

### Identified risks

- Touches network/API calls; verify timeout, retry, and error handling. (33 files)
- Touches database/schema behavior; verify migration safety and rollback path. (21 files)
- Includes tests or test config; check whether coverage matches changed behavior. (6 files)
- Touches auth/session/permission logic; verify access-control tests. (3 files)
- Contains secret-like terms; confirm no credentials or tokens are committed. (1 file)
- Touches CI/build/dependency files; verify reproducible installs and pipeline impact. (1 file)
- Large diff size; review may miss behavior hidden in broad refactors.

### Improvement suggestions

- Run the language-specific test/lint/typecheck commands before merge and include results in the PR.
- Add migration notes: forward path, rollback/backup plan, and data-shape assumptions.
- Add or confirm negative authorization tests, not only happy-path tests.
- Confirm external calls have timeouts and useful failure messages.
- Consider splitting mechanical refactors from behavior changes to make review safer.

### Confidence score: Low

Reviewed diff: https://github.com/vercel/next.js/pull/77777
