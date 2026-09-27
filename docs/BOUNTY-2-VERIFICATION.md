# Bounty #2 local verification

This evidence records what can be verified locally for the Next.js + SQLite
`CLAUDE.md` template. It is not a claim that Claude Code, a deployment, or a
payment was observed.

## Structural check

```text
python -B -m unittest discover -s tests -v
```

The zero-dependency tests check that the template includes the required stack,
project layout, naming conventions, migration rules, actionable commands,
explicit reasons for every normative list item, anti-pattern reasons, and an
honest greenfield protocol. One test also copies
the exact `CLAUDE.md` into a newly created, empty temporary project directory
and checks the copied file retains the required defaults. This verifies
copyability and the static contract; it does not exercise Claude Code.

The current local candidate passed all 6 tests on Python 3.12, 3.13, and 3.14
on Windows, with zero skips; `git diff --check` also passed. These results are
for the local candidate and do not replace the hosted Actions run for its next
published commit.

## Behavioral smoke test

On 2026-09-27, the template was copied into an otherwise empty temporary
directory and tested with Claude Code CLI 2.1.268. `claude auth status --json`
reported `loggedIn: true`, `authMethod: claude.ai`, and `subscriptionType: pro`;
`ANTHROPIC_API_KEY` was unset. No API key was created or used.

Exact prompt:

> This is a bounded behavioral smoke test of the root CLAUDE.md in this isolated empty temporary directory. Implement a minimal authenticated create/list CRUD slice for a Task entity, following the file's declared stack, project structure, validation, authorization, SQL, naming, error, environment, and testing rules. Work only in the current directory. Do not access the network, install packages, execute shell commands, read files outside this directory, invent external service credentials, or claim any tests/build ran. Create only the smallest coherent set of source, migration, configuration, and hermetic test files needed to demonstrate the conventions. If a requirement cannot be made real without a dependency or unspecified product decision, implement a safe typed boundary and state the limitation instead of guessing. At the end, report the exact files created, how authorization and validation are enforced, and any requirements you could not fully implement.

The first output exposed ambiguity in the authorization guidance. The template
was tightened to separate session/workspace authorization at server/service
entry points from mandatory tenant-scoped SQL in repository operations. A
second completed run with the same prompt generated 31 files using the declared
Next.js 15 / React 19 / TypeScript / Zod / SQLite stack, with migrations,
Server Action/page authorization, workspace-scoped repository queries, and
unit/integration tests including cross-tenant denial cases. This is evidence
that the CLI read and followed the revised conventions; it is not evidence that
the generated application runs correctly.

No dependencies were installed, and no lint, typecheck, unit test, build, or
browser test was run on the generated project. Those results are therefore
unverified. This smoke is not a claim of production readiness, merge, bounty
award, or payment.
