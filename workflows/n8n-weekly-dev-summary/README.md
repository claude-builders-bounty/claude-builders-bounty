# n8n Weekly Dev Summary

This workflow creates a weekly narrative summary for a GitHub repository. It
collects commits, merged pull requests, and closed issues from the previous
seven days, asks Claude Sonnet 4 to write a concise update, and posts the result
to Discord.

## Setup

1. Import `weekly-dev-summary.json` into n8n.
2. Open the `Configure Report` node and set `repoOwner`, `repoName`,
   `language`, and `discordWebhookUrl`.
3. Add environment variables to n8n: `GITHUB_TOKEN` and `ANTHROPIC_API_KEY`.
4. Adjust the `Weekly Friday 5pm` trigger if you want a different schedule.
5. Run the workflow once manually, then activate it.

## Configuration

| Variable | Where | Description |
| --- | --- | --- |
| `repoOwner` | `Configure Report` node | GitHub owner or organization |
| `repoName` | `Configure Report` node | Repository name |
| `language` | `Configure Report` node | `EN` or `FR` |
| `discordWebhookUrl` | `Configure Report` node | Discord incoming webhook URL |
| `GITHUB_TOKEN` | n8n environment | Token with public repo read access |
| `ANTHROPIC_API_KEY` | n8n environment | Claude API key |

## Delivery

The final node posts to Discord. To use Slack instead, replace the final
`Send Discord Summary` node URL with a Slack incoming webhook and change the
payload field from `content` to `text`.

## Execution Screenshot

The bounty asks for a screenshot from a real n8n instance. This repository does
not include secrets, so run the workflow in your n8n instance and attach the
successful execution screenshot to the pull request before final review.
