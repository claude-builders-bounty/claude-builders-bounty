# PR Review: Add support for type-safe environment variables in astro:env

> **PR:** [#10925](https://github.com/withastro/astro/pull/10925) | **Author:** florian-lefebvre | **Changes:** +342/-51 in 12 files
> **Reviewed by:** Claude Code PR Review Agent v1.0.0
> **Date:** 2026-05-13T14:35:00Z

---

### Summary

This PR introduces the `astro:env` module, which provides type-safe access to environment variables with schema validation at build time. It adds a new configuration option `env.schema` in `astro.config.mjs` where developers can define expected environment variables with types, defaults, and access context (server/client). The implementation generates a virtual module that validates environment variables against the schema during the build process and exposes typed getters, replacing the need for manual `import.meta.env` access with runtime checks.

### Identified Risks

- **Client-side secret leakage:** Variables marked with `context: "server"` are excluded from client bundles, but the filtering relies on Vite's `define` replacements. If a server variable is referenced indirectly (e.g., via a shared utility module that is accidentally imported client-side), the build-time check may not catch it, potentially leaking secrets into client bundles. This warrants a thorough review of the tree-shaking boundary.
- **Breaking change for existing env usage:** While this is additive, the documentation changes suggest deprecating raw `import.meta.env` access in favor of `astro:env`. Projects upgrading may see new build warnings. The migration path should be clearly documented.
- **Missing runtime validation in dev mode:** The schema validation runs at build time, but in `astro dev` mode, environment variables are read dynamically. If a required variable is missing, the error message should surface at server startup, not on first request. The current implementation defers validation to module import time, which could cause confusing errors in dev.
- **Zod dependency coupling:** The schema uses Zod-like syntax (`z.string()`, `z.number().optional()`), but the PR bundles a lightweight custom validator instead of using Zod directly. If Zod is later added as a dependency for other features, there could be API inconsistencies between the custom validator and the real Zod.
- **No support for dynamic env:** Some deployment platforms inject environment variables at runtime (e.g., Vercel edge functions). The current implementation only reads from `process.env` at build time, which may not cover all deployment scenarios.

### Improvement Suggestions

- Add an integration test that verifies server-only variables are NOT present in the client JavaScript output. This is the most critical safety property of the feature and should have explicit test coverage.
- Consider adding a `--validate-env` CLI flag to `astro check` that validates the current environment against the schema without running a full build, useful in CI pipelines.
- The `getSecret` function in `packages/astro/src/env/validators.ts` should use a constant-time comparison if it is ever used for comparing secret values, even though currently it only checks for existence.
- Add JSDoc comments to the public API exports (`getSecret`, `getPublic`) with usage examples, so IDE tooltips provide helpful guidance.
- The error messages in `packages/astro/src/env/errors.ts` should include the schema definition alongside the actual value to help developers quickly diagnose type mismatches (e.g., "Expected DATABASE_URL to be a string, got: undefined. Schema: { type: 'string', context: 'server' }").
- Consider supporting `.env.local` file validation against the schema during `astro dev` to catch typos early (e.g., `DATABSE_URL` instead of `DATABASE_URL`).

### Confidence Score

**Medium** -- The PR is well-structured and the approach is sound, but the 12 changed files span multiple packages (core, CLI, types), and some security-critical behavior (client/server boundary enforcement) depends on Vite internals that are not fully visible in this diff. A focused security review of the variable filtering logic would increase confidence.
