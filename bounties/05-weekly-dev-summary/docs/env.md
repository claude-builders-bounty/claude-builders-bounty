# Environment Variables

Set these on the n8n host (Docker env, systemd unit, or n8n Cloud → Variables panel).

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `GITHUB_REPO` | yes | `anthropics/claude-code` | `owner/repo` format. Single repo per workflow instance. |
| `ANTHROPIC_API_KEY` | yes | `sk-ant-api03-...` | From console.anthropic.com. The workflow uses `claude-sonnet-4-20250514`. |
| `SLACK_WEBHOOK_URL` | yes (default delivery) | `https://hooks.slack.com/services/T.../B.../...` | Incoming Webhook URL. Swap node for Discord/email if preferred. |
| `SUMMARY_LANGUAGE` | no | `EN` or `FR` | Defaults to `EN`. The Claude prompt switches accordingly. |

## GitHub PAT credential (separate from env)

Stored in n8n Credentials, not env. Create a fine-grained PAT with read access to:
- Contents (commits)
- Pull requests
- Issues

Name the credential `GitHub PAT` so the imported workflow picks it up automatically.

## n8n Docker example

```yaml
services:
  n8n:
    image: n8nio/n8n:latest
    environment:
      - GITHUB_REPO=anthropics/claude-code
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
      - SUMMARY_LANGUAGE=EN
      - GENERIC_TIMEZONE=America/New_York
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
volumes:
  n8n_data:
```
