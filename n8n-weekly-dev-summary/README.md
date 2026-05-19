# n8n Weekly GitHub Dev Summary with Claude

An n8n workflow that automatically generates a weekly narrative summary of GitHub repository activity using Claude API and delivers it via Discord webhook.

## Setup (5 steps)

1. **Import the workflow into n8n:**
   - Open your n8n instance (e.g., `http://localhost:5678`)
   - Click **Workflows** → **Import from File**
   - Select `workflow.json`

2. **Set environment variables in n8n:**
   - Go to **Settings** → **Environments**
   - Add these variables:
     ```
     GITHUB_TOKEN=ghp_your_github_token
     GITHUB_REPO=owner/repo
     ANTHROPIC_API_KEY=sk-ant-your_anthropic_key
     DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
     SUMMARY_LANGUAGE=EN
     ```

3. **Activate the workflow:**
   - Click **Active** toggle in the workflow editor

4. **Test manually:**
   - Click **Execute Workflow** to run immediately
   - Check Discord for the summary message

5. **Verify weekly schedule:**
   - The workflow runs every Friday at 5pm (configurable in the Cron node)

## What It Does

1. **Trigger:** Runs every Friday at 5pm (weekly cron)
2. **Config:** Loads environment variables (repo, language, webhook URL)
3. **Fetch GitHub data:**
   - Commits from the past 7 days
   - Closed issues from the past 7 days
   - Merged PRs from the past 7 days
4. **Build digest:** Aggregates activity into a structured text
5. **Call Claude API:** Generates a narrative summary using `claude-sonnet-4-20250514`
6. **Format message:** Prepares Discord-compatible markdown
7. **Send to Discord:** Posts the summary via webhook

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | `ghp_...` |
| `GITHUB_REPO` | Repository in `owner/repo` format | `facebook/react` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-...` |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |
| `SUMMARY_LANGUAGE` | Summary language (`EN` or `FR`) | `EN` |

### Cron Schedule

Default: **Friday at 5pm**

To change:
1. Open the workflow
2. Click the **Weekly Friday 5pm** node
3. Modify the schedule in the node settings

## Output Example

```markdown
## Weekly Dev Summary — facebook/react

This week saw significant progress on the React 19 release candidate. The team merged 12 PRs focused on performance optimizations and bug fixes. Notable changes include improved hydration error messages and a fix for Suspense boundary edge cases.

Key highlights:
- Performance: Reduced bundle size by 3% through tree-shaking improvements
- DX: New dev-only warnings for common mistakes
- Stability: Fixed 8 reported issues from the RC feedback

Next steps: Final RC review and documentation updates before stable release.

---
Commits: 47 | Closed issues: 8 | Merged PRs: 12
```

## Testing

### Manual Test Run

1. Click **Execute Workflow** in n8n
2. Check the execution log for each node
3. Verify Discord received the message

### Dry Run (without Discord)

1. Disable the **Send to Discord** node
2. Run the workflow
3. Check the **Format Discord Message** node output

## Troubleshooting

### GitHub API Rate Limit

If you hit rate limits, reduce the `per_page` parameter in the HTTP Request nodes or use a GitHub App token instead of a Personal Access Token.

### Claude API Errors

- Verify `ANTHROPIC_API_KEY` is correct
- Check Claude API status: https://status.anthropic.com
- Ensure you have API credits

### Discord Webhook Fails

- Test the webhook URL with `curl`:
  ```bash
  curl -X POST "YOUR_WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d '{"content": "Test message"}'
  ```

## Requirements

- n8n instance (self-hosted or cloud)
- GitHub Personal Access Token with `repo` scope
- Anthropic API key with Claude access
- Discord webhook URL

## Notes

- The workflow fetches up to 100 commits, issues, and PRs per category
- Claude is prompted to write a narrative summary, not a bullet list
- Language can be switched between English (`EN`) and French (`FR`)
- The workflow uses Claude Sonnet 4 (`claude-sonnet-4-20250514`)
