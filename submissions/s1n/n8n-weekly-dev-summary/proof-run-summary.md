**Weekly Dev Summary — n8n-io/n8n**
_Window: 2026-07-23 → 2026-07-30 · 100 commits · 79 merged PRs · 15 closed issues · lang EN_

# n8n Weekly Development Narrative
**2026-07-23 → 2026-07-30** | 100 commits · 79 merged PRs · 15 closed issues

## Highlights
The week focused heavily on the AI Builder and agent capabilities. A new workflow SDK validation framework for Instance AI landed (#35045), alongside approval-loop branch verification with scripted gate decisions (#34822). n8n Connect was enabled for the Agent Builder (#34298), and the editor now supports changing the target workflow of an agent workflow tool (#35276). Inbound binary attachments are now supported for agents (#34869). On the core scheduling side, a misfire policy was added to the durable scheduler (#35075), and the v1-to-v2 workflow converter was completed (#35189).

## Shipped
- **Slack Node**: User pickers now show real names and handles (#35279)
- **Embeddings AWS Bedrock Node**: Inference profile models and node options added (#34991)
- **Brandfetch Node**: Explicit route types and simplified operations (#28846)
- **Editor**: Require Workflow Execute Permission toggle for n8n User Auth webhooks (#35195); auto-select credentials for pasted and imported nodes (#34687)
- **Core**: Import workflow tags from packages matched by source id (#35133); support reference-only sub-workflow dependencies in package export (#35051)

## Fixes & Closed Issues
- Webhook responses relayed through the queue are now size-limited (#35032), closing webhook-response-mode issues (#35219).
- MCP Server Trigger Node now saves execution data only after a tool call completes (#35239, #35284), resolving instance-level MCP OAuth failures (#34713).
- Grist Node restores stored base URLs for legacy credentials (#35229), closing #35213.
- Respond to Webhook nodes owned by Wait nodes are no longer flagged as unused (#33911), closi
