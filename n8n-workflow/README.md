# n8n Weekly Dev Summary Workflow

An [n8n](https://n8n.io) workflow that generates a weekly narrative summary
of a GitHub repo's activity using the Claude API.

## Features

- **Weekly cron** — runs every Friday at 5pm
- **GitHub data** — fetches commits, closed issues, and merged PRs for the week
- **Claude summary** — generates a 2–3 paragraph narrative summary in English or French
- **Slack delivery** — posts the summary to a configurable channel
- **Configurable** — set repo, destination, language via workflow variables

## Setup (5 steps)

### 1. Import the workflow

1. Open n8n (cloud or self-hosted)
2. Go to **Workflows → Import from File**
3. Select `weekly-dev-summary.json`

### 2. Configure GitHub credentials

1. Create a [GitHub Personal Access Token](https://github.com/settings/tokens) with `repo` scope
2. In n8n, go to **Credentials → Add → Generic Credential**
3. Paste the token as the password
4. Name it `githubApi` (or update the node's credential reference)
5. Set the 3 GitHub HTTP Request nodes to use this credential

### 3. Configure Claude API credentials

1. Get an [Anthropic API key](https://console.anthropic.com)
2. In n8n, go to **Credentials → Add → Generic Credential**
3. Paste the API key
4. Name it `claudeApi`
5. Set the "Claude API" HTTP Request node to use this credential

### 4. Set the workflow config

Open the **Combine & Format** Code node and update defaults:

```javascript
const owner = "your-org";      // GitHub org or user
const repo  = "your-repo";     // Repository name
const lang  = "EN";            // "EN" or "FR"
```

### 5. Connect Slack

1. Go to **Credentials → Add → Slack**
2. Authenticate with your Slack workspace
3. Update the Slack node's channel (default: `#dev-updates`)

## Testing

1. Click **Execute Workflow** in the n8n editor
2. Check the output of each node for errors
3. Verify the Slack message appears in the configured channel

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `owner` | `octocat` | GitHub org/user |
| `repo` | `hello-world` | Repository name |
| `language` | `EN` | Summary language (`EN` or `FR`) |
| `channel` | `#dev-updates` | Slack channel |

## License

MIT
