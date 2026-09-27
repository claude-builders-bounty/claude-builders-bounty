# Historical n8n execution with Claude Code — September 25

This receipt and its generated summary describe the earlier CLI-based workflow. The current workflow uses a direct Anthropic Messages API request instead; neither this receipt nor its screenshot verifies that new API path. The earlier one-page counts below are preserved as captured and are not complete weekly totals. Current pagination and API mapping are covered separately by the synthetic local verification receipt.

- Runtime: n8n 2.40.7, Node.js 26.9.0 (self-hosted, local CLI).
- Test workflow: `bounty5realtest04`; source workflow imported through n8n CLI into an isolated local data folder.
- Repository: `n8n-io/n8n` (public).
- Window: `2026-09-18T18:39:38.935Z` to `2026-09-25T18:39:38.935Z` UTC.
- Started: `2026-09-25T18:39:38.596Z`; stopped: `2026-09-25T18:39:54.741Z`.
- Workflow result: **SUCCESS**.
- Activity: commits `100` fetched (100-record endpoint cap; summary says 100+), closed issues `3`, merged PRs `78`.
- Claude Code exit code: `0`.
- Delivery branch: POSTed the rendered summary to a local loopback receiver; response `{"ok": true}`. No Discord/Slack webhook was called.
- The image `output/playwright/n8n-cli-execution.png` is a browser screenshot of this captured CLI execution receipt, not the n8n editor UI. No n8n owner account was created.

## Generated summary

## n8n Weekly Development Summary
**Period:** 2026-09-18T18:39Z → 2026-09-25T18:39Z

---

### Activity Counts
| Category | Count |
|---|---|
| Commits | 100+ *(API cap reached; exact total unknown)* |
| Merged PRs | 78 |
| Closed Issues | 3 |

---

### Highlights

**Agent / AI (most active area)**
- Shared Agent context access added (#38930)
- Agent skills modal revamped (#39545)
- Invalid tool call IDs in agent history repaired (#39640)
- Assistant mentions rolled out in editor (#39370)
- Telemetry added for agent channel setup (#39604)
- Execution waiting status now stored in engine (#39093)
- Publishing user attached to triggered executions (#39466)

**Nodes**
- Anthropic Node: prompt caching added to Message operation (#35804)
- Google Cloud Storage: request headers preserved on object create (#35218)
- Microsoft Teams v2 resource-locator copy corrected (#39443)
- Zoho CRM logo updated to current branding (#39305)

**API / Core**
- Public API path parameters now validated before scope middlewares (#39512)
- Nested folders accepted during promotion apply (#39630)
- Promotion CLI gains pinned `Apply` and `Apply Continue` commands (#39597)

---

### Closed Issues
- MCP access-token scope error on self-hosted (#39563)
- Credential-type question for per-call billing (#39546)
- Recurring ETIMEDOUT cluster at :00–:02 and :30–:32 (#39428)
