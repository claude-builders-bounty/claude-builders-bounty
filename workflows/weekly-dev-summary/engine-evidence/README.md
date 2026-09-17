# Real-engine verification evidence

`verification-summary.json` records five completed n8n 2.39.6 CLI executions.
The workflow was imported into a private test database and executed by n8n's
normal JavaScript task runner. GitHub, Claude, and Discord responses came from
local HTTP fixtures. This is not live-provider or payout evidence.

Normal English and French runs each made six fixture requests and one delivery.
The empty-week run made five requests and one delivery. Incomplete-search and
truncated-model runs made zero deliveries and exited with errors as expected.
The test harness verifies the expected collected counts, not just exit status.

The initial real-engine run exposed use of a missing browser `URL` global.
That was corrected with compatible exact webhook validation, and the code-level
test sandbox no longer supplies the unavailable global. All five scenarios then
passed. Original failure evidence and detailed execution logs are retained in
the local workspace; the compact results here contain no actual credentials.

No n8n UI screenshot is included. A separate private UI startup attempt timed
out and was stopped. Do not interpret the CLI results as a captured UI run.
