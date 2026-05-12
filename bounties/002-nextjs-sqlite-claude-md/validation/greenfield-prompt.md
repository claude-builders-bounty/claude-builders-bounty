# Validation Prompt

Use this prompt from the root of a new Next.js 15 App Router project after copying in `CLAUDE.md`.

```text
Read CLAUDE.md and answer with:
1. the stack you infer for this project,
2. where you would put a new organization invite feature,
3. how you would add a SQLite migration for an invites table,
4. which commands you would run before finishing,
5. any clarifying questions you need before implementing.

Do not edit files.
```

Passing behavior: Claude should answer using the template rules and should not need clarifying questions for ordinary greenfield implementation details.
