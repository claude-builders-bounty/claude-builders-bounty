## PR Review

**Title:** Add CLAUDE.md template for Next.js 15 + SQLite SaaS

### Summary

Changes **218 additions, 0 deletions** across **2 files**. Primary files: skills/nextjs-sqlite-template/CLAUDE.md, skills/nextjs-sqlite-template/README.md

### Identified Risks

- [CRITICAL] Possible secret exposure in `skills/nextjs-sqlite-template/CLAUDE.md`: Possible credential hardcoded
- [HIGH] Hardcoded localhost address in `skills/nextjs-sqlite-template/CLAUDE.md`
- [MEDIUM] Debug logging left in code in `skills/nextjs-sqlite-template/CLAUDE.md`
- [HIGH] Hardcoded connection string in `skills/nextjs-sqlite-template/CLAUDE.md`
- [MEDIUM] Environment file modification detected in `skills/nextjs-sqlite-template/CLAUDE.md`
- [MEDIUM] HTTP URL detected — use HTTPS in `skills/nextjs-sqlite-template/CLAUDE.md`

### Improvement Suggestions

- Large PR — consider splitting into smaller, focused PRs for easier review
- PR only adds code, no deletions — verify no dead code left behind

### Stats

| Metric | Value |
|--------|-------|
| Files Changed | 2 |
| Additions | 218 |
| Deletions | 0 |
| Confidence | **Low** |
