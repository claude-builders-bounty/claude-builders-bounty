# Test Notes

Acceptance check for issue #2:

- Created a greenfield Next.js 15 + SQLite SaaS project context in prompt form.
- Pasted `templates/nextjs-sqlite/CLAUDE.md` as the project instruction file.
- Asked Claude Code to explain the architecture and first implementation steps.

Observed result:

- It identified the stack as Next.js 15 App Router, TypeScript, SQLite, Zod, and server-first React.
- It described the expected folder boundaries without asking for clarification.
- It prioritized migrations, auth/tenant boundaries, environment validation, and server-action validation.
- It warned that billing access must wait for verified webhooks instead of trusting checkout redirects.

This confirms the template is specific enough to guide a greenfield project without extra clarification.
