# Test Notes

## Greenfield Smoke Test

Created a new Next.js App Router project skeleton with:

```bash
npx create-next-app@15 next-sqlite-claude-smoke --ts --eslint --app --src-dir --import-alias "@/*" --use-npm --yes
```

The generated project used `next: 15.5.18`. Copied `CLAUDE.md` into the project root and checked it against the issue acceptance criteria:

- Covers stack and versions.
- Covers folder structure.
- Covers naming conventions.
- Covers SQL and migration rules.
- Includes dev commands.
- Includes patterns to follow and anti-patterns to avoid.
- Every rule is paired with a concrete reason.
- Does not require project-specific names or existing code to be usable in a greenfield Next.js + SQLite SaaS project.

## Claude Code Confirmation

Installed and checked Claude Code CLI:

```bash
claude --version
# 2.1.145 (Claude Code)
```

The prompt-level confirmation could not be completed on this machine because Claude Code was not logged in:

```text
Not logged in - Please run /login
```

The template was still validated as the exact project-root `CLAUDE.md` file Claude Code reads for repository context, and it avoids placeholders that would force a clarifying question before first use.
