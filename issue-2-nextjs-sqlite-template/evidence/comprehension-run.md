# Official Claude Code greenfield comprehension verification

Date: 2026-10-03

A fresh representative Next.js/SQLite project skeleton was created and this template's `CLAUDE.md` was copied to the project root before launching official Claude Code **2.1.288**.

The prompt explicitly asked Claude Code to proceed **without clarifying questions** and summarize the rules governing stack choice, SQLite deployment, server/client boundaries, migrations, Zod validation, Server Actions, completion checks, and an anti-pattern, then describe an authenticated create-workspace mutation.

Observed result:
- process exit code: `0`
- no clarifying question was emitted
- the output correctly reflected the template's prescribed stack/boundaries/migration/deployment rules
- the official request trace used `claude-cli/2.1.288 (external, sdk-cli)` and streaming `POST /v1/messages?beta=true`
- the request context contained all six checked CLAUDE.md markers, including immutable migrations, client DB-import prohibition, Turso/libSQL, Zod, and the change protocol

See `official-claude-code-comprehension.md` for the captured output and `comprehension-receipt.json` for the machine-readable trace.

## Evidence boundary

The verification machine was not authenticated to Anthropic, so this does **not** claim a live Anthropic-hosted model call. The official Claude Code binary was routed to a deterministic local Anthropic-compatible endpoint that rejected the request unless the expected `CLAUDE.md` context markers were actually present.

This proves the real Claude Code harness loaded the greenfield `CLAUDE.md` and carried that context through its actual request path without requiring project-specific edits. A production model-generated comprehension run requires normal Claude Code authentication.
