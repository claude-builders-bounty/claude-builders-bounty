# n8n Weekly Dev Summary — GitHub + Claude

An n8n workflow that runs every Friday at 5pm, pulls the week's GitHub activity (commits, closed issues, merged PRs), sends it to the Claude API for a narrative summary, then delivers it to Slack and/or email.

![Workflow overview](./workflow-screenshot.png)

> **Bounty:** [Issue #5 — $200](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)

---

## What it does

1. **Cron trigger** fires every Friday at 17:00 (local server time)
2. **Date range** is computed as the past 7 days
3. Three parallel GitHub API calls fetch:
   - Recent commits (`/repos/{owner}/{repo}/commits`)
   - Closed issues (`/repos/{owner}/{repo}/issues?state=closed`)
   - Merged pull requests (`/repos/{owner}/{repo}/pulls?state=closed`)
4. A **Claude prompt** is assembled from the collected data
5. `claude-sonnet-4-20250514` generates a warm, readable narrative summary
6. The summary is delivered to **Slack** (via incoming webhook) **and/or email** (via SMTP)

---

## Setup in 5 steps

### Step 1 — Import the workflow

1. Open your n8n instance
2. Go to **Workflows → Import from file**
3. Select `weekly-dev-summary.json`

### Step 2 — Set environment variables

In n8n go to **Settings → Variables** and add:

| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO` | Target repository (`owner/repo`) | `torvalds/linux` |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | `sk-ant-...` |
| `SLACK_WEBHOOK_URL` | Incoming webhook URL for your channel | `https://hooks.slack.com/...` |
| `EMAIL_FROM` | Sender address (if using email) | `devbot@example.com` |
| `EMAIL_TO` | Recipient address | `team@example.com` |
| `SUMMARY_LANGUAGE` | `EN` or `FR` | `EN` |

### Step 3 — Add credentials

- **GitHub Token** — create a fine-grained token with `Contents: Read` and `Issues: Read` on the target repo. Add as **HTTP Header Auth** credential with header `Authorization: token <your_token>`.
- **SMTP** (optional, if you want email delivery) — add SMTP credentials in n8n under **Credentials → SMTP**.

### Step 4 — Adjust the cron schedule (optional)

The default is **Friday at 17:00**. To change it, open the "Every Friday 5pm" node and adjust the day/hour.

### Step 5 — Activate and test

1. Click **Activate** (toggle in the top-right)
2. To test immediately: open the workflow and click **Execute Workflow** — it will run for the past 7 days right now

---

## Example output

> **📊 Weekly Dev Summary — acme/backend (Mon May 5 – Mon May 12)**
>
> It was a productive week on the backend! The team shipped **12 commits** and merged **4 pull requests**, with a clear focus on the authentication refactor that's been in progress since last sprint.
>
> Alice opened and closed #312, which tackled the long-standing session timeout bug — several users had reported this and the fix was clean. Bob's PR #309 landed the new JWT refresh flow, complementing Alice's work perfectly.
>
> On the infrastructure side, Carlos knocked out 3 dependency upgrades and updated the CI pipeline to use the new runner image. No flaky tests this week, which is always worth celebrating.
>
> 📌 12 commits · 4 merged PRs · 3 issues closed

---

## Customization

- **Change delivery channel** — disable the Slack node or the Email node depending on your preference; both are wired in parallel
- **More repos** — duplicate the three GitHub fetch nodes and feed additional repos into the prompt
- **Digest format** — edit the "Build Claude Prompt" Code node to change tone, length, or structure
- **Language** — set `SUMMARY_LANGUAGE=FR` for French output

---

## Requirements

- n8n `>= 1.0.0`
- Anthropic API key (model: `claude-sonnet-4-20250514`)
- GitHub Personal Access Token (read-only)
- Slack incoming webhook **or** SMTP credentials
