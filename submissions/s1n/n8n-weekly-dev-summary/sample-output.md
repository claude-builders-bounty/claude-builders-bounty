# Sample weekly summary output (from live public GitHub dry-run)

**Source repo:** `n8n-io/n8n`  
**Window:** 2026-07-23 → 2026-07-30  
**Fetched:** 100 commits · 78 merged PRs · 14 closed issues  
**Note:** Narrative below is structured from **real public API data**. Final bounty submission should use Claude (`claude-sonnet-4-20250514`) output + n8n screenshot.

---

**Weekly Dev Summary — n8n-io/n8n**  
_Window: 2026-07-23 → 2026-07-30 · 100 commits · 78 merged PRs · 14 closed issues · lang EN_

### Highlights
The last 7 days on `n8n-io/n8n` show **100 commits**, **78 merged PRs**, and **14 closed issues**.

### Shipped
Recent commits (sample):
- `1aed5e6` feat(Slack Node): Show user real names and handles in user pickers (#35279)
- `bcf7502` feat(core): Complete v1-to-v2 workflow converter (no-changelog) (#35189)
- `0932806` feat: Support inbound binary attachments for agents (no-changelog) (#34869)
- `d0d0b7a` fix(core): Default AI-created workflows to v1 execution order (#35277)
- `0d4c3a7` fix(core): Preserve `cause` on execution errors (#35216)
- `83b1f15` ci: Fix Wrangler install in API schema publish workflow (#35188)
- `256478f` refactor(core): Break credentials-overwrites and frontend service cycle (#35226)
- `062ce87` docs: Rewrite public-api agent skill and split reference (no-changelog) (#35187)

Merged PRs (sample):
- #35279 feat(Slack Node): Show user real names and handles in user pickers (@Joffcom)
- #35239 fix(MCP Server Trigger Node): Save execution data only after tool call completes (@elsmr)
- #35189 feat(core): Complete v1-to-v2 workflow converter (no-changelog) (@ivov)
- #34869 feat: Support inbound binary attachments for agents (no-changelog) (@burivuhster)
- #35277 fix(core): Default AI-created workflows to v1 execution order (@OlegIvaniv)
- #35216 fix(core): Preserve `cause` on execution errors (@tomi)
- #35275 fix(core): Import security audit risk reporters with a file extension (backport to release-candidate/2.33.x) (@n8n-assistant[bot])
- #35188 ci: Fix Wrangler install in API schema publish workflow (@MarcL)

### Fixes & Closed Issues
- #35280 Wokflow not trigerring and not displaying any error
- #35269 Form node never stops running
- #35251 Polling triggers fire duplicate executions (stale registration survives) after n8n import:workflow on a running instance + re-activation — schedule triggers are
- #35234 Built-in Audit node returns HTTP 500 on n8n Cloud 2.32.6
- #27238 Custom crons with ranged Days of Month fails the Day of Week constraint and run every day
- #32739 Buggy unused Respond to Webhook node validation
- #35213 Grist API Credentials Server URL changed after Update (2.32.5) leading to Failed Executions
- #35219 Webhooks with response mode

### Follow-ups
- Add GitHub PAT for private repos / higher rate limits.
- Keep Claude model pinned to `claude-sonnet-4-20250514`.
- Capture n8n success screenshot after Discord delivery.

Dry-run artifact: `evidence/dryrun-github-activity.json`
