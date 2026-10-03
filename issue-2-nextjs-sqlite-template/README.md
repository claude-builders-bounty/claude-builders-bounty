# Next.js 15 + SQLite CLAUDE.md template

Copy `CLAUDE.md` to the root of a greenfield Next.js 15 App Router project.

The template is intentionally opinionated: Server Components by default, explicit server-only DB boundaries, immutable migrations, Zod runtime validation, thin Server Actions, and deployment-aware SQLite guidance.

## Verified local checks

1. `python3 verify_template.py` checks required sections and the historical context-transport receipt.
2. `python3 greenfield_smoke.py` creates an App Router/SQLite skeleton and copies `CLAUDE.md` byte-for-byte without placeholders.
3. The historical official Claude Code 2.1.288 run used a deterministic local endpoint. It proves that the CLI loaded the template into its request context. The local endpoint's output and absence of questions do **not** prove real-model comprehension. See the existing evidence files for that explicitly limited result.

## Genuine model verification

```bash
python3 verify_live_claude.py
```

The default run creates a fresh project, records the unchanged template's SHA-256, checks the actual official CLI authentication status, and makes **no model call**. It saves a sanitized receipt with no credentials or account identifiers. The current receipt is `evidence/live-preflight.json`.

Once an eligible contributor is authenticated to an existing included Claude subscription, they can deliberately collect a live result:

```bash
python3 verify_live_claude.py --run-live --receipt evidence/live-comprehension-review.json
```

This command reads the unmodified template from the fresh project. It confines tools to reads, disables external MCP configuration, refuses custom endpoints/API-key routes, and does not install dependencies or claim an application build. It never buys credits or authenticates a user automatically.

A successful CLI exit is only evidence to review. Check the actual response for correct folder and file naming, server/client and DB boundaries, runtime validation and authorization, immutable migration conventions, deployment choice, and test commands. Record any clarifying questions, omissions or incorrect decisions honestly. `live_comprehension_confirmed` stays false until the actual live response has been assessed against the template; the runner cannot declare acceptance.

## Current remaining requirement

Genuine authenticated comprehension evidence and creator acceptance remain pending. Login must be completed through the official Claude Code authentication flow; do not put credentials in this repository or in chat.
