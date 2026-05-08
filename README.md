# Weekly Dev Summary Workflow

n8n automation that generates AI-powered weekly summaries of GitHub activity.

## Setup (5 Steps)

1. **Import workflow**
   - In n8n, go to Workflows → Import → From File
   - Select `workflow.json`

2. **Configure credentials**
   - GitHub: Create Personal Access Token with `repo` scope
   - Anthropic: Create API key with Claude access

3. **Set variables**
   - `repo`: GitHub repo in format `owner/repo`
   - `webhookUrl`: Discord webhook URL
   - `language`: `EN` or `FR`

4. **Test manually**
   - Click "Execute Workflow" to test
   - Check Discord for the summary

5. **Activate**
   - Toggle workflow to active
   - Runs every Friday at 5PM

## Workflow Structure

```
Cron (Fri 5PM) → Set Date Range → GitHub API (commits/issues/PRs) 
      → Claude API (summary) → Discord Webhook
```

## Example Output

```
## Weekly Dev Summary for claude-builders-bounty/claude-builders-bounty

This week saw significant progress across 4 pull requests, with a focus on 
automation tooling and documentation. The community contributed three new 
CLAUDE.md templates and a comprehensive changelog generator.

Key highlights include the addition of a pre-tool-use hook for blocking 
destructive commands, improving project safety. Two major documentation 
updates were merged, adding structured guidance for Next.js and SQLite 
projects.

The team closed 7 issues, primarily focused on improving developer 
experience and tooling reliability. Overall velocity remains strong with 
contributors actively engaging across multiple repositories.
```

## Credentials Needed

| Service | Scope |
|---------|-------|
| GitHub | `repo` (read) |
| Anthropic | Claude API access |
| Discord/Slack | Webhook URL |