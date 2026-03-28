# Weekly Dev Summary - n8n + Claude Workflow

**Bounty:** $200 - [Claude Builders Bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)

An n8n workflow that automatically generates weekly narrative summaries of GitHub repository activity using Claude API.

---

## 📋 Acceptance Criteria Checklist

- [x] Exportable n8n workflow (importable `.json` file)
- [x] Trigger: Weekly cron (Friday at 5pm)
- [x] Fetches from GitHub API: commits, closed issues, merged PRs for the week
- [x] Calls Claude API (`claude-sonnet-4-20250514`) to generate narrative summary
- [x] Delivers summary via: Email OR Discord/Slack webhook (configurable)
- [x] Configurable variables: GitHub repo, destination channel, language (EN/FR)
- [x] Tested on real n8n instance (screenshot included)
- [x] README with setup instructions in 5 steps or fewer

---

## 🚀 Quick Setup (5 Steps)

### 1. Import the Workflow
- Open your n8n instance
- Click **"Add Workflow"**
- Select **"Import from File"**
- Upload `weekly-dev-summary.json`

### 2. Configure Credentials
Set up these credentials in n8n:

| Credential | Type | Purpose |
|------------|------|---------|
| `GITHUB_API_CREDENTIAL` | GitHub API | Access repository data |
| `ANTHROPIC_API_CREDENTIAL` | Anthropic API | Generate summaries with Claude |
| `SLACK_API_CREDENTIAL` | Slack API | Send to Slack (optional) |
| `SMTP_CREDENTIAL` | SMTP | Send via email (optional) |

### 3. Configure Variables
Edit the **"Set Config"** node with your values:

```json
{
  "githubOwner": "your-org",
  "githubRepo": "your-repo",
  "destinationChannel": "#dev-updates",
  "emailRecipients": "team@example.com",
  "language": "EN"
}
```

### 4. Choose Delivery Method
- For **Slack**: Enable the "Slack - Send Summary" node
- For **Email**: Enable the "Email - Send Summary" node
- For **both**: Enable both nodes

### 5. Activate
- Toggle the workflow to **Active**
- It will run every Friday at 5 PM automatically

---

## 📊 Workflow Overview

```
┌─────────────────────┐
│  Weekly Cron        │ Trigger: Every Friday 5pm
│  (Friday 5PM)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Set Config         │ Define repo, channel, language
└──────────┬──────────┘
           │
     ┌─────┼─────┐
     ▼     ▼     ▼
┌────────┐┌────────┐┌────────┐
│GitHub  ││GitHub  ││GitHub  │ Fetch data in parallel
│Commits ││Issues  ││PRs     │
└───┬────┘└───┬────┘└───┬────┘
    └─────────┼─────────┘
              ▼
    ┌─────────────────┐
    │ Code - Aggregate│ Build prompt for Claude
    └────────┬────────┘
             ▼
    ┌─────────────────┐
    │ Claude API      │ Generate narrative summary
    └────────┬────────┘
             │
      ┌──────┴──────┐
      ▼             ▼
┌──────────┐  ┌──────────┐
│  Slack   │  │  Email   │ Deliver summary
│  Send    │  │  Send    │
└──────────┘  └──────────┘
```

---

## 🔧 Configuration Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `githubOwner` | GitHub organization or user | `rohitdash08` |
| `githubRepo` | Repository name | `FinMind` |
| `destinationChannel` | Slack channel for delivery | `#engineering` |
| `emailRecipients` | Email addresses (comma-separated) | `team@company.com` |
| `language` | Summary language (EN or FR) | `EN` |

---

## 🧪 Testing

### Manual Test
1. Open the workflow in n8n
2. Click **"Execute Workflow"**
3. Check output in Slack/Email

### Sample Output

```
📊 Weekly Dev Summary - FinMind (Mar 20-26, 2025)

This week the team merged 12 pull requests and closed 8 issues. 
Key highlights:

• Implemented GDPR PII export & delete workflow (#76)
• Fixed authentication edge cases in JWT middleware
• Added comprehensive test coverage for new features

Contributors: @alice (5 commits), @bob (4 commits), @charlie (3 commits)

Full details: https://github.com/rohitdash08/FinMind/compare/main@{1.week.ago}...main
```

---

## 📸 Screenshot

![n8n Workflow Execution](screenshot.png)

*Screenshot showing successful workflow execution with Claude summary generation*

---

## 🔐 Security Notes

- Store API keys in n8n credentials, **never** in the workflow JSON
- Use n8n's built-in credential encryption
- Set appropriate GitHub token scopes: `repo`, `read:user`
- Rotate API keys periodically

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| GitHub API rate limit | Use authenticated requests (higher limits) |
| Claude API timeout | Increase timeout in node settings |
| No data returned | Check date range and repository visibility |
| Slack not receiving | Verify bot permissions in channel |

---

## 📚 Resources

- [n8n Documentation](https://docs.n8n.io)
- [Claude API Documentation](https://docs.anthropic.com)
- [GitHub API Documentation](https://docs.github.com/en/rest)

---

## ✅ Bounty Submission

This workflow fulfills all acceptance criteria for [Claude Builders Bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5):

- [x] Exportable `.json` workflow file
- [x] Weekly cron trigger configured
- [x] GitHub API integration (commits, issues, PRs)
- [x] Claude API integration for narrative generation
- [x] Delivery via Slack OR Email
- [x] Configurable variables
- [x] Tested and working
- [x] README with 5-step setup

**Claim:** `/opire try` on issue #5
