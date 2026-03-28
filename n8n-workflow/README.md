# n8n Weekly Dev Summary Workflow

Automated weekly development summary using n8n + Claude API.

## Quick Start (5 Steps)

### Step 1: Install n8n

```bash
npm install n8n -g
n8n start
```

Or use Docker:
```bash
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
```

### Step 2: Import Workflow

1. Open n8n (http://localhost:5678)
2. Click **Settings** → **Import from File**
3. Select `weekly-dev-summary.json`

### Step 3: Configure Credentials

1. **GitHub**: Add your GitHub token
2. **Environment Variables**:
   ```
   GITHUB_OWNER=your-org
   GITHUB_REPO=your-repo
   ANTHROPIC_API_KEY=your-claude-key
   WEBHOOK_URL=https://discord.com/api/webhooks/xxx  (or Slack)
   LANGUAGE=English  (or French, Chinese, etc.)
   ```

### Step 4: Test

Click **Execute Workflow** to test immediately.

### Step 5: Activate

Toggle the workflow to **Active**. It will run every Friday at 5pm.

---

## Features

| Feature | Description |
|---------|-------------|
| **Weekly Trigger** | Every Friday at 5pm (configurable) |
| **GitHub Integration** | Fetches commits, closed issues, merged PRs |
| **Claude AI** | Generates narrative summary using claude-sonnet-4 |
| **Multi-Channel** | Delivers via Discord, Slack, or email |
| **Configurable** | Repo, language, delivery channel |

---

## Workflow Diagram

```
┌─────────────┐
│   Cron      │ Every Friday 5pm
│  Trigger    │
└──────┬──────┘
       │
       ├──────────┬──────────┐
       ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│  Commits │ │  Issues  │ │   PRs    │
│ (7 days) │ │ (closed) │ │ (merged) │
└────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │
     └────────────┴────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  Merge Data    │
         └───────┬────────┘
                 │
                 ▼
         ┌────────────────┐
         │  Claude API    │
         │  (AI Summary)  │
         └───────┬────────┘
                 │
                 ▼
         ┌────────────────┐
         │ Discord/Slack  │
         │    Webhook     │
         └────────────────┘
```

---

## Sample Output

```markdown
## 📊 Weekly Dev Summary (Mar 21-28, 2026)

### Overview
This week saw significant progress on the authentication system with 23 commits, 15 issues resolved, and 8 pull requests merged. The team focused primarily on security improvements and performance optimizations.

### Highlights
- Implemented OAuth2 authentication with JWT tokens
- Added rate limiting to prevent brute force attacks
- Optimized database queries reducing load time by 40%

### Issues Resolved
- #142: Fixed null pointer exception in user profile
- #138: Resolved session timeout issue
- #135: Fixed memory leak in API gateway

### Pull Requests
- #156: Add user authentication (merged)
- #154: Implement caching layer (merged)
- #151: Update dependencies (merged)

### Looking Ahead
Next week we'll focus on completing the 2FA implementation and preparing for the beta release.
```

---

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_OWNER` | (required) | GitHub org/user |
| `GITHUB_REPO` | (required) | Repository name |
| `ANTHROPIC_API_KEY` | (required) | Claude API key |
| `WEBHOOK_URL` | (required) | Discord/Slack webhook |
| `LANGUAGE` | English | Summary language |
| `CRON_SCHEDULE` | Fri 17:00 | Trigger schedule |

---

## Troubleshooting

**Workflow not triggering?**
- Check timezone settings in n8n
- Verify cron expression

**Claude API errors?**
- Verify ANTHROPIC_API_KEY is correct
- Check API quota

**No data in summary?**
- Ensure GITHUB_OWNER and GITHUB_REPO are correct
- Check GitHub token has repo scope

---

## License

MIT
