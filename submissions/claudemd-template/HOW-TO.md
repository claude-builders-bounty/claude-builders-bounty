# How-To Guide: CLAUDE.md for Next.js 15 + SQLite SaaS

## Quick Start

```bash
# In your Next.js project root
cp CLAUDE.md ./CLAUDE.md
```

Claude Code automatically reads CLAUDE.md when you open the project folder.

## Customizing for Your Project

### Change the tech stack

If you use Prisma instead of Drizzle, update the Database section:

```markdown
## Database
- **ORM:** Prisma (replace Drizzle references)
```

### Add your own anti-patterns

Add to the Anti-Patterns section:

```markdown
### 13. Don't use X
\`\`\`typescript
// BAD
...
// GOOD
...
\`\`\`
**Why:** Your reasoning here.
```

### Add team-specific conventions

Add a Team section at the bottom:

```markdown
## Team Conventions
- PR reviews required from 2 team members
- Feature branches: `feature/description`
- Commit messages: Conventional Commits
```

## Testing Your CLAUDE.md

After customizing, verify Claude understands your project:

1. Open the project in Claude Code
2. Ask: *"What tech stack does this project use?"*
3. Ask: *"How should I create a new database table?"*
4. Ask: *"What are the anti-patterns I should avoid?"*

Claude should answer all three correctly from the CLAUDE.md.

## Using with Other Frameworks

This template is designed for Next.js 15 + SQLite, but the structure works for any stack. Swap out:

| Section | Next.js → Express | Next.js → Remix |
|---------|-------------------|-----------------|
| Stack | Change framework/runtime | Change framework |
| Structure | `src/routes/` instead of `app/` | `app/routes/` |
| Components | Remove RSC patterns | Keep RSC patterns |
| Anti-patterns | Add Express-specific | Add Remix-specific |
