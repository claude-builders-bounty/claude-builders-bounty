# Weekly Dev Summary — n8n Workflow

Automated weekly narrative summary of GitHub repository activity, powered by the Anthropic Messages API.

## What It Does

Every Friday at 5:00 PM UTC, this workflow:

1. Pulls the past week's commits, closed issues, and merged PRs from your GitHub repo
2. Sends the aggregated data to the Anthropic Messages API for narrative summarization
3. Posts the formatted summary to a Discord/Slack webhook

## Setup (5 Steps)

### Step 1: Import the Workflow

Open your n8n instance, go to **Workflows → Import from File**, and select `weekly-dev-summary.json`.

### Step 2: Create Credentials

Create two **HTTP Header Auth** credentials in n8n:

- **GitHub Token**
  - Header Name: `Authorization`
  - Header Value: `token ghp_YOUR_GITHUB_PAT`
  - (Requires `repo` scope)

- **Anthropic API Key**
  - Header Name: `x-api-key`
  - Header Value: `sk-ant-YOUR_API_KEY`
  - The `anthropic-version` header is already set in the workflow node.

### Step 3: Configure Variables

Open the **Configuration** node and set:

| Variable       | Example                          | Description                        |
|----------------|----------------------------------|------------------------------------|
| `repo`         | `facebook/react`                 | GitHub `owner/repo`                |
| `language`     | `en` or `fr`                     | Summary language                   |
| `webhook_url`  | `https://discord.com/api/webhooks/...` | Discord or Slack webhook URL  |
| `api_key`      | *(leave empty, uses credential)* | Override if not using credentials  |

### Step 4: Map Credentials

Ensure each HTTP Request node references the correct credential:

- **Fetch Commits**, **Fetch Closed Issues**, **Fetch Pull Requests** → `GitHub Token`
- **Generate Summary** → `Anthropic API Key`

### Step 5: Activate

Toggle the workflow to **Active**. The first summary will fire on the next Friday at 5 PM UTC.

## Customizing the Schedule

Open the **Every Friday 5PM** node and edit the cron expression:

| Expression       | Schedule            |
|------------------|---------------------|
| `0 17 * * 5`     | Friday 5 PM (default) |
| `0 9 * * 1`      | Monday 9 AM         |
| `0 17 * * 1-5`   | Weekdays 5 PM       |

## Workflow Diagram

```
┌──────────────┐
│  Schedule    │  Friday 5 PM cron
│  Trigger     │
└──────┬───────┘
       │
┌──────▼───────┐
│ Configuration │  repo, language, webhook_url
└──────┬───────┘
       ├──► ┌───────────────┐
       │    │ Fetch Commits │──┐
       │    └───────────────┘  │
       ├──► ┌───────────────┐  │
       │    │Fetch Issues   │──┼──► ┌─────────────────┐
       │    └───────────────┘  │    │ Aggregate       │
       └──► ┌───────────────┐  │    │ Activity        │
            │ Fetch PRs     │──┘    └────────┬────────┘
            └───────────────┘                │
                                    ┌────────▼────────┐
                                    │ Generate        │
                                    │ Summary         │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Format Output   │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Deliver to      │
                                    │ Webhook         │
                                    └─────────────────┘
```

## Notes

- The GitHub API has a rate limit of 60 requests/hour for unauthenticated requests. Use a PAT for higher limits.
- The Anthropic Messages API requires `anthropic-version: 2023-06-01` in the request headers.
- For Slack webhooks, you may need to adjust the payload format in the **Deliver to Webhook** node (use `text` instead of `content`/`embeds`).
- Commits beyond the first 100 per week are not included due to GitHub API pagination defaults.

## License

MIT
