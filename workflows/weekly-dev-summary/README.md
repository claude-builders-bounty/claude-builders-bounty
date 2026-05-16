# n8n + Claude Code — Weekly Dev Summary

A **weekly cron workflow** that generates a narrative summary of GitHub repo activity using Claude API.

**Bounty**: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5 ($200)

## Prerequisites

- [n8n](https://docs.n8n.io) instance (self-hosted or cloud)
- GitHub Personal Access Token with `repo` scope
- Anthropic API key (Claude)

## Installation (5 steps)

1. **Import the workflow**: In n8n, go to **Workflows → Import from File** and select `weekly-dev-summary.json`

2. **Set environment variables** in n8n:
   ```
   GITHUB_OWNER = your-org-or-username
   GITHUB_REPO  = your-repo-name
   SUMMARY_LANGUAGE = EN  # or FR for French
   ```

3. **Add credentials**:
   - **GitHub**: Create a credential with your GitHub token
   - **Claude API**: Create a "Header Auth" credential with `x-api-key` as the Anthropic API key

4. **Configure delivery** (pick one):
   - **Slack**: Replace "Send Summary" webhook node with a Slack node
   - **Discord**: Replace with Discord webhook node
   - **Email**: Replace with email node (SMTP)
   - **Default**: Outputs via webhook — connect your own delivery node

5. **Activate**: Toggle the workflow to **Active**

## Workflow Overview

```
Weekly Cron (Fri 5pm)
  ↓
Broadcast Trigger
  ├── Fetch Commits (GitHub API, past 7 days)
  ├── Fetch Closed Issues (GitHub API, past 7 days)
  ├── Fetch Merged PRs (GitHub API, past 7 days)
  └── Format Date Range (Set node)
         ↓
     Merge Data
         ↓
     Claude API → Generate narrative summary
         ↓
     Send Summary (webhook output)
```

## Output Format

The Claude-generated summary includes:
- 📊 Weekly overview
- 📝 Commits highlights
- ✅ Closed issues
- 🚀 Merged PRs
- 🎯 Key highlights
- ⚠️ Items to watch

## Testing

To test manually, set the cron trigger to "5 minutes from now" and activate the workflow. You should receive a summary within 2 minutes.
