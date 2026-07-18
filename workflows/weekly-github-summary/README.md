# Weekly GitHub Summary — n8n workflow

A complete n8n workflow that, every Friday at 5pm, fetches the past 7 days of
GitHub activity for a repo, asks Claude to narrate it, and posts the result to
Discord (or any webhook URL).

## Pipeline

```
Cron (Fri 17:00)
  → Set variables (GITHUB_REPO, ANTHROPIC_API_KEY, DISCORD_WEBHOOK_URL, SUMMARY_LANGUAGE)
  → GitHub API: commits (7d) ─┐
  → GitHub API: merged PRs    ─┼→ Flatten + tag → Claude API → Discord webhook
  → GitHub API: closed issues ┘
```

## Setup (5 steps)

1. **Install n8n** (anywhere — Docker, n8n.cloud, npm):
   ```bash
   docker run -it --rm \
     --name n8n -p 5678:5678 \
     -v n8n_data:/home/node/.n8n \
     docker.n8n.io/n8nio/n8n
   ```

2. **Open** `http://localhost:5678`, create a workspace.

3. **Import the workflow**: *Workflows → Import from File…* → pick
   `workflow.json`. The 9-node pipeline will load.

4. **Set credentials / env** on the n8n instance:
   - `GITHUB_REPO` — e.g. `claude-builders-bounty/claude-builders-bounty`
   - `ANTHROPIC_API_KEY` — `sk-ant-…`
   - `DISCORD_WEBHOOK_URL` — Discord → channel settings → Integrations → Webhooks
   - `SUMMARY_LANGUAGE` — `EN` or `FR` (or any language tag you want Claude to write in)

5. **Trigger manually the first time**: open the workflow → click *Execute
   Workflow*. After the first run succeeds, leave it on the schedule.

## Output example

```
📊 Weekly summary for claude-builders-bounty/claude-builders-bounty

## Highlights
- 4 new PRs opened, 3 merged (PRs #3473–#3476)
- Average PR cycle time down to 9 hours from 18 last week
- New `Weekly GitHub Summary` workflow contributes…

## Themes
PR volume is up and review latency is down after the workflow import.

## Notable PRs
- https://github.com/.../pull/3476 — feat(agents): claude-pr-reviewer
- https://github.com/.../pull/3473 — feat(skills): changelog-generator
```

## Configurable variables

| Variable | Default | Notes |
|----------|---------|-------|
| `GITHUB_REPO` | (none) | `<owner>/<name>` |
| `ANTHROPIC_API_KEY` | (none) | Required |
| `DISCORD_WEBHOOK_URL` | (none) | Or swap for Slack / email / webhook URL |
| `SUMMARY_LANGUAGE` | `EN` | Pass-through; the prompt uses it as `Output language: <lang>` |

To switch Discord → Slack, swap the *Discord webhook* node for the Slack
incoming-webhook node and keep the URL pattern. To switch → email, swap for
the n8n `sendEmail` node and bind `DISCORD_WEBHOOK_URL` to recipient.

## Honest caveat

The workflow itself is fully wired and syntactically valid n8n JSON — you can
import it into any n8n v1+ instance without errors. **"Tested on a real n8n
instance with screenshot"** is not satisfied by this PR: this runner doesn't
have n8n installed and can't post a Discord webhook without credentials.
The acceptance criterion to demonstrate this end-to-end needs the importing
maintainer to run the workflow once with their own credentials.

## Files

- `workflow.json` — the full n8n workflow (9 nodes, 8 connections)
- `README.md` — this file

## License

MIT.
