# Weekly GitHub Digest — n8n + Claude

n8n workflow that pulls a week of GitHub activity and asks Claude to write a
short narrative summary. Posts to Discord every Friday afternoon.

I built this because I got tired of scrolling through commit logs to write
changelogs by hand. It's not perfect but it saves me 30 min every week.

## How it works

```
Cron (Fri 5pm) → read repo config → fetch commits, issues, PRs in parallel
→ merge + trim the data → send to Claude API → format → post to Discord
```

Claude gets the raw commit messages, closed issues, and merged PRs from the
past 7 days. The prompt tells it to group things into categories and keep
it under 400 words. You can switch between English and French with one env var.

## Setup

**1.** Import `workflow.json` into n8n (Workflows → Import from File)

**2.** Create a Header Auth credential called `GitHub Token`:
- Header Name: `Authorization`
- Header Value: `Bearer ghp_YOURTOKEN`

You need a PAT with read access to the repo. Fine-grained tokens work too.

**3.** Set these environment variables in n8n:

```
GITHUB_REPO=owner/repo
CLAUDE_API_KEY=sk-ant-...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SUMMARY_LANGUAGE=EN
```

`SUMMARY_LANGUAGE` is optional, defaults to `EN`. Set it to `FR` for French.

**4.** Toggle the workflow to Active

**5.** Hit "Execute Workflow" to test it right away

That's it. Should take under 5 minutes if you already have the API keys.

## Switching to Slack

The last node just POSTs json to a webhook URL. For Slack, replace the
Discord URL with a Slack incoming webhook and change `content` to `text`
in the "Build discord msg" code node. One line change.

For email, swap the last HTTP node with n8n's Send Email node and pass
the summary text as the body.

## Changing the schedule

Edit the "Friday 5pm" trigger node. You can set any day/time you want,
or change it to a cron expression for more control (e.g. every Monday 9am).

## Notes

- The workflow caps at 100 items per API call (commits, issues, PRs).
  For most repos that's more than enough for a single week.
- Discord has a 2000 char limit per message so the output gets truncated
  if Claude gets really verbose. Haven't hit this in practice though.
- The Claude prompt is in the "Ask Claude" node. Feel free to tweak it —
  I kept it pretty generic on purpose.

## License

MIT
