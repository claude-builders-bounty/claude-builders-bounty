# Verification (issue #2 acceptance)

| Criterion | Status |
|-----------|--------|
| Project structure, naming, DB migration rules | Covered in Folder structure + SQL sections |
| Dev commands, patterns, anti-patterns | Dev commands + Component patterns + What we do not do |
| Opinionated with reasons | Every table row and anti-pattern includes Why |
| Usable on greenfield Next.js + SQLite | No project-specific paths; standard App Router layout |
| Claude understands without clarifying | Stack fixed upfront; "When unsure" resolves ambiguity |

Manual check: scaffold `create-next-app@15` with TypeScript, copy `CLAUDE.md` to root, ask
Claude Code to "add an organization invite Server Action" — it should use Drizzle transaction,
`memberships` role enum, and `revalidatePath` without asking which ORM or auth library to use.
