# Test Provenance — n8n workflow execution

## What was tested

The complete workflow chain executed on a real n8n instance (n8n installed
locally, `n8n start`, owner account created, workflow imported via the UI's
Import → From file flow, then run with the editor's **Execute workflow**
button).

**Result: "Workflow executed successfully"** — every node ran, no errors.
Screenshot: `execution-screenshot.png`.

## Node-by-node (from the execution's item badges)

| Node | Output | Meaning |
|---|---|---|
| Weekly Trigger (Fri 5pm) | 1 item | schedule trigger fired |
| Config | 1 item | repo / language / webhookUrl / weekStart set |
| Fetch commits | 5 items | 5 commits since week start |
| Fetch closed issues | 3 items | 3 real issues (the 4th item, a closed PR, correctly filtered by the `pull_request` key) |
| Fetch merged PRs | 4 items | 4 closed PRs fetched; 3 actually merged within the week (merged_at filter) |
| Build digest | 1 item | digest assembled; counts `{commits: 5, issues: 3, prs: 3}` |
| Claude summary | 1 item | LLM called with the 1014-char digest prompt |
| Deliver to webhook | 1 item | narrative POSTed to the destination |

## Mocked endpoints (documented honestly)

The test environment has no Anthropic API key and this host's connection to
api.github.com is rate-limited and resets connections, so three endpoints
were redirected to local mock servers that speak the identical protocols
and payload shapes:

| Node | Test target | Mock |
|---|---|---|
| Fetch commits / issues / pulls | `http://127.0.0.1:18996/...` | mock GitHub REST API (returns realistic commits/issues/PRs JSON) |
| Claude summary | `http://127.0.0.1:18997/v1/messages` | mock Anthropic Messages API (returns a fixed narrative) |
| Deliver to webhook | `http://127.0.0.1:18998/hook` | webhook catcher (logs the POST body) |

The delivered payload captured by the catcher:

```json
{
  "text": "This week the repository stayed in steady motion. Four pull requests merged, led by the terminal working-directory fix ...",
  "repo": "NousResearch/hermes-agent",
  "counts": {"commits": 5, "issues": 3, "prs": 3}
}
```

The delivered workflow (`weekly-github-digest.json`) points at the real
api.github.com and api.anthropic.com; only the test run used the mocks.
Each fetch endpoint was requested exactly once (verified in the mock's
request log: 3 requests total).

## Bugs found and fixed during testing (why the shipped JSON looks like this)

1. **Per-item HTTP execution**: a linear chain Config → commits → issues →
   PRs makes each HTTP node fire once per input item (5 commits → 5 issue
   requests → 15 items → 15 PR requests → 60 items). Fixed by setting
   **Execute Once** on the fetch nodes (`executeOnce: true`).
2. **URL expressions**: `{{ $('Config').item.json.repo }}` inside a URL
   string is not evaluated when the workflow is created via the REST API
   (it arrives URL-encoded as a literal). Fixed by using the canonical
   `=`-prefixed expression form:
   `={{ 'https://api.github.com/repos/' + $('Config').item.json.repo + '/commits?since=' + ... }}`.
3. **weekStart precision**: the original expression kept the current
   time-of-day; fixed to Monday 00:00 UTC (`setHours(0,0,0,0)`).

## Reproduce

```bash
# from the repo root
npm install -g n8n && n8n start          # or: node ./bin/n8n start
# create the owner account at http://localhost:5678, then:
#   Workflows → ⋯ → Import → weekly-github-digest.json
#   set repo/language/webhookUrl in the Config node, create the
#   "Anthropic API Key" header-auth credential, click Execute workflow
```
