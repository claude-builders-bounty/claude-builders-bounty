# n8n Weekly Dev Summary — Opire Bounty #5

Automated weekly narrative summary of a GitHub repo's activity, powered by n8n + Claude API.

## Setup (5 steps)

### 1. Install n8n
```bash
npm install -g n8n
n8n start
```

### 2. Import the workflow
- Open n8n UI (http://localhost:5678)
- Click **Workflows → Import from File**
- Select `workflow.json` from this directory

### 3. Configure GitHub credentials
- Go to **Credentials → New → GitHub API**
- Add a Personal Access Token with `repo` scope
- Token is used in HTTP Request nodes for GitHub API calls

### 4. Configure Claude API credentials
- Go to **Credentials → New → Open AI API** (Claude compatible endpoint)
- Set Base URL: `https://api.anthropic.com`
- Add your Anthropic API key

### 5. Set workflow variables
In the n8n workflow variables (`$vars`), set:
| Variable | Example |
|---|---|
| `githubRepo` | `owner/repo-name` |
| `discordWebhook` | `https://discord.com/api/webhooks/...` |
| `language` | `EN` or `FR` |

## How it works

```
┌─────────────┐    ┌──────────────┐
│ Cron (Fri 5pm)│───▶│ Set Variables│
└─────────────┘    └───────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       ┌───────────┐ ┌───────────┐ ┌───────────┐
       │ Commits   │ │ Closed    │ │ Merged    │
       │ (7 days)  │ │ Issues    │ │ PRs       │
       └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                  ┌────────────────┐
                  │ Claude API     │
                  │ (claude-sonnet-4)│
                  │ Generate Summary│
                  └────────┬───────┘
                           ▼
                  ┌────────────────┐
                  │ Discord/Slack  │
                  │ Webhook        │
                  └────────────────┘
```

## Output example

> **Weekly Dev Summary** — `owner/repo` (May 6–13, 2026)
>
> This week the team merged **12 pull requests**, closed **8 issues**, and pushed **34 commits** across 8 contributors. Notable work included a major refactor of the authentication module, performance improvements to the search API, and the addition of dark mode support. The most active day was Tuesday with 9 merged PRs.

## Delivery options

- **Discord**: Set `discordWebhook` variable to your Discord channel webhook URL
- **Slack**: Replace Discord node with Slack Webhook node
- **Email**: Add n8n's Gmail node after Claude summarization

## Resources
- n8n docs: https://docs.n8n.io
- Claude API: https://docs.anthropic.com
- GitHub API: https://docs.github.com/rest
