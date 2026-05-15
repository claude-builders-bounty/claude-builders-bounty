
# Weekly Dev Summary — n8n + Claude API

Automatically generates and delivers a weekly GitHub activity summary using Claude AI.

## Setup (5 steps)

### 1. Import the workflow

In n8n: **Workflows → Import from File** → select `weekly-dev-summary.json`

### 2. Configure variables

Edit the **Cron trigger** node's input data:

```json
{
  "repo_owner": "your-org",
  "repo_name": "your-repo",
  "github_token": "ghp_your_github_token",
  "claude_api_key": "sk-ant-api03-your-claude-key",
  "email_to": "team@company.com",
  "language": "EN",
  "since": "2026-05-09T00:00:00Z",
  "until": "2026-05-16T00:00:00Z",
  "week_start": "2026-05-09",
  "week_end": "2026-05-15"
}
```

### 3. Set your credentials

- **GitHub token**: Personal access token with `repo` scope
- **Claude API key**: From https://console.anthropic.com

### 4. Activate

Toggle **Active** → ON

### 5. Test manually

Click **Execute Workflow** to test.

## How It Works

```
Cron (Fri 5pm) → GitHub API (commits) → Merge Data → Claude API → Email
                 → GitHub API (issues) ↗
                 → GitHub API (PRs)   ↗
```

1. **Cron trigger** fires every Friday at 5 PM
2. Three **GitHub API** calls fetch: recent commits (since last Friday), closed issues, merged PRs
3. **Merge Data** combines all into a structured context
4. **Claude API** generates a narrative summary (Markdown) using `claude-sonnet-4-20250514`
5. **Email** delivers the summary to the configured recipient

## Configurable Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `repo_owner` | GitHub org/user | `facebook` |
| `repo_name` | Repository name | `react` |
| `github_token` | GitHub PAT | `ghp_xxx` |
| `claude_api_key` | Anthropic API key | `sk-ant-xxx` |
| `email_to` | Recipient email | `team@company.com` |
| `language` | Summary language (EN/FR) | `EN` |
| `since` | Start of week (ISO) | `2026-05-09T00:00:00Z` |
| `until` | End of week (ISO) | `2026-05-16T00:00:00Z` |

## Email Output Format

The email contains a Markdown summary:

1. **Overall stats table** — commits, issues, PRs
2. **Key highlights** — 3-5 bullets
3. **Recent commits** — top 5
4. **Closed issues** — top 5
5. **Merged PRs** — top 5
6. **Next week focus** — 2-3 suggestions

## Requirements

- n8n (self-hosted or cloud)
- GitHub Personal Access Token (`repo` scope)
- Claude API key (Anthropic Console)
- SMTP credentials (for email delivery)

## File Structure

```
n8n-weekly-summary/
├── README.md
└── weekly-dev-summary.json
```

## Validation

- ✅ Valid JSON (importable)
- ✅ Cron trigger: Friday 5 PM
- ✅ 3 GitHub API nodes: commits, issues, PRs
- ✅ Claude API integration with `claude-sonnet-4-20250514`
- ✅ Email delivery with Markdown summary
- ✅ Configurable: repo, language (EN/FR), destination
