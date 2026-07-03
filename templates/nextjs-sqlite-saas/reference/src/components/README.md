# `src/components/` — UI components

| Subfolder | Purpose |
|-----------|---------|
| `ui/` | Stateless primitives (Button, Input) — no domain logic |
| `features/` | Domain UI wired to server actions or query data |

Default to Server Components. Add `"use client"` only for state, effects, or browser APIs — keep client islands small and leaf-level.
