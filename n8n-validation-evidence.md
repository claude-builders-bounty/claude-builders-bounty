# Local n8n validation evidence

- n8n version: 1.123.0
- execution ID: 18
- final execution status: SUCCESS
- execution path: schedule trigger -> configuration -> date range -> GitHub commits -> GitHub closed issues -> GitHub merged pull requests (GraphQL) -> Claude Sonnet 4.6 -> Discord delivery
- GitHub data: authenticated read-only retrieval completed for 25 commits, 175 closed issues, and 24 merged pull requests in the weekly window
- Claude API: one successful request using the current replacement model `claude-sonnet-4-6`; the API response did not expose usage or price data in the captured execution record
- generated summary: present and non-empty; no secret markers detected
- Discord delivery: two messages returned successful empty HTTP responses (Discord webhook success response)
- provider writes: none; no GitHub comment, claim, branch, PR, push, or Opire action was performed
- owner funding: USD 5.00 prepaid Anthropic credit plus USD 1.00 tax, USD 6.00 total cash outflow; not revenue, not converted to EUR, and not double-counted as API usage
- API usage cost: UNKNOWN because the successful response did not expose defensible usage/pricing data

The original bounty names `claude-sonnet-4-20250514`. Anthropic has retired that
model, so the workflow uses the documented current replacement `claude-sonnet-4-6`.
Owner-confirmed screenshot evidence: two screenshots were captured from the
local n8n instance without rerunning the workflow. The workflow-editor
screenshot shows the complete 10-node workflow with no credentials visible.
The execution screenshot shows execution `18`, `Succeeded in 38.54s`, and
the `Post to Discord` node completed successfully with 2 items. These are
owner-provided evidence references; no screenshot bytes or secrets are
embedded in this artifact. The copied package files are
`evidence/n8n-bounty-200/01-workflow-complet.png` and
`evidence/n8n-bounty-200/02-execution-18-success.png`.

Public submission status: not submitted. No `/opire try`, GitHub comment,
branch, pull request, push, or other provider write was performed.
