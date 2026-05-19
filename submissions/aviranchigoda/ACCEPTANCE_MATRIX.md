# Acceptance Matrix

This matrix maps the issue #5 requirements to the submitted artifacts and the
current verification evidence.

| Requirement | Artifact | Local evidence | Status |
| --- | --- | --- | --- |
| Importable n8n workflow JSON | `weekly-dev-summary.workflow.json` | `check-acceptance.mjs` validates workflow id, name, nodes, connections, and JSON syntax. | Covered locally |
| Weekly schedule | `Weekly Friday 5pm` node in `weekly-dev-summary.workflow.json` | `check-acceptance.mjs` verifies schedule expression `0 17 * * 5`. | Covered locally |
| Manual reviewer run path | `Manual Test Trigger` node | `check-acceptance.mjs` verifies the manual trigger node exists. | Covered locally |
| GitHub commits | `GitHub Commits` HTTP Request node and `code-nodes/build-github-api-urls.js` | `check-acceptance.mjs` verifies the commits endpoint and preserved full responses. | Covered locally |
| GitHub closed issues | `GitHub Closed Issues` HTTP Request node and `code-nodes/build-github-api-urls.js` | `check-acceptance.mjs` verifies `type:issue is:closed` search coverage. | Covered locally |
| GitHub merged pull requests | `GitHub Merged Pull Requests` HTTP Request node and `code-nodes/build-github-api-urls.js` | `check-acceptance.mjs` verifies `type:pr is:merged` search coverage. | Covered locally |
| Claude summary generation | `Claude Summary` HTTP Request node and `code-nodes/prepare-claude-request.js` | `check-acceptance.mjs` verifies the Anthropic Messages endpoint, headers, and `claude-sonnet-4-20250514`. | Covered locally |
| Slack delivery | `Send Slack Summary` HTTP Request node and `code-nodes/prepare-slack-message.js` | `validate-mock-execution.mjs` records a mocked Slack delivery in `evidence/mock-execution-result.json`. | Covered locally |
| Slack delivery success is not assumed | `code-nodes/execution-result.js` | `check-acceptance.mjs` verifies Slack status/body checks, and the mock Slack failure evidence in `evidence/mock-slack-failure-result.json` proves a failed Slack webhook does not produce `delivered`. | Covered locally |
| Configurable repository | `Configure Summary` node and `code-nodes/configure-summary.js` | `check-acceptance.mjs` verifies `githubOwner` and `githubRepo` configuration fields. | Covered locally |
| Configurable destination | `Configure Summary` node and `README.md` | `check-acceptance.mjs` verifies `slackWebhookUrl`; README documents that the webhook URL selects the Slack channel for modern Slack apps. | Covered locally |
| Configurable language | `Configure Summary` node and `code-nodes/configure-summary.js` | `check-acceptance.mjs` verifies `summaryLanguage` supports `EN` and `FR`. | Covered locally |
| README setup in five steps or fewer | `README.md` | `check-acceptance.mjs` counts setup steps and verifies the total is five or fewer. | Covered locally |
| n8n execution evidence | `validate-mock-execution.mjs`, `evidence/mock-execution-result.json`, `evidence/mock-n8n-execution-ui.png` | Mock execution imports and runs the workflow in n8n 2.20.11 with real public GitHub API and mocked Claude/Slack endpoints. | Covered locally |
| Real Anthropic and Slack execution evidence | `validate-real-execution.mjs`, `REAL_EVIDENCE.md`, future `evidence/real-execution-result.json`, future `evidence/real-n8n-execution-ui.png` | `check-acceptance.mjs --require-real-evidence` enforces this gate after user-supplied credentials and approval. | Approval-gated |
| No committed secrets | `validate-real-execution.mjs` and `check-acceptance.mjs` | The real runner refuses to write evidence if approval-gated secrets appear in the sanitized payload; `check-acceptance.mjs` scans the submission for known secret patterns. | Covered locally |

## Remaining Approval Gates

- Run real Anthropic and Slack validation only after the user supplies
  `ANTHROPIC_API_KEY` and `SLACK_WEBHOOK_URL` and explicitly approves the run.
- Capture `evidence/real-n8n-execution-ui.png` only after the real run.
- Re-run `node submissions/aviranchigoda/check-acceptance.mjs --require-real-evidence`
  before any public PR.
- Do not comment `/opire try`, push, or open the public PR without explicit user
  approval.
