# Real n8n execution evidence

- Runtime: n8n 2.39.8, Node.js 26.8.1, macOS arm64
- Workflow import: `n8n import:workflow --input=skills/n8n-weekly-summary/n8n-workflow.json`
- Execution: imported workflow ID `B5WeeklySummary20260921` via the manual trigger
- GitHub path: live public GitHub API for `octocat/Hello-World`
- Claude boundary: local deterministic HTTP double implementing the Anthropic messages response shape; production workflow still targets `https://api.anthropic.com/v1/messages` by default
- Delivery boundary: local deterministic Discord HTTP receiver; no real channel was contacted
- Observed final node: `Deliver to Discord`
- n8n execution status: `success`, finished=true, UI execution ID 2
- Workflow SHA-256: `3660461ccda696e7342e7ddccd6070a1655c053810f461593494f6b245be2edc`
- Final empty-week execution readback: `Normalize Issues`, `Normalize Commits`, and `Normalize Merged PRs` produced empty lists; `Prepare Claude Prompt` reported counts `0/0/0`; the real n8n path reached `Generate with Claude` and `Deliver to Discord` successfully using controlled local doubles.
- Final empty-week execution output SHA-256: `70a8beaaee8acfe81ff2cc6b64ca3cedd42cefbf4866dfcc796b4d6cc68f797e`
- Final n8n Executions screenshot SHA-256: `648d255b13843efbd8a9dbb7c00a94d94b3209dc25c41991229405578a03d61d`

The first adversarial empty-week run exposed two failure modes: without `alwaysOutputData`, n8n could stop before Claude/delivery; with the sentinel enabled, an unfiltered normalizer could fabricate one blank commit. The release candidate preserves the empty-week path, filters commit rows to valid GitHub commit objects, and bounds closed issues to `WEEK_START <= closed_at <= WEEK_END`. Final isolated n8n retests proved empty and populated windows, boundary exclusion, prompt counts, Claude invocation, and delivery without fabricated activity.

The screenshot is a headless capture of the real local n8n Executions page after the corrected retest; it shows the corrected workflow's successful execution. It contains no API key, webhook secret, or private repository data.
