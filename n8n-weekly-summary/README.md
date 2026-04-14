# n8n Weekly GitHub Summary Workflow

🤖 **Automated weekly development summaries powered by Claude AI**

Bounty: [claude-builders-bounty/claude-builders-bounty #5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5)

---

## 💰 Bounty Info

- **Reward**: $200 USD
- **Platform**: Opire (auto-payment on merge)
- **Author**: FanLi (范蠡)

---

## 🚀 Features

- **Weekly Cron Trigger**: Every Friday at 5 PM
- **GitHub Integration**: Fetches commits, issues, and PRs
- **Claude AI Summary**: Generates narrative summary
- **Multi-channel Delivery**: Discord/Slack webhook support
- **Configurable Variables**: Repo, channel, language

---

## ⚡ Setup (5 Steps)

### Step 1: Import Workflow
1. Open n8n dashboard
2. Go to **Workflows** → **Import from File**
3. Select `weekly-summary-workflow.json`

### Step 2: Configure GitHub Token
1. Go to **Credentials** → **Create Credential**
2. Select **HTTP Header Auth**
3. Add your GitHub token: `Authorization: token YOUR_TOKEN`
4. Name it `GitHub Token`

### Step 3: Configure Claude API Key
1. Go to **Credentials** → **Create Credential**
2. Select **Anthropic API**
3. Add your Claude API key
4. Name it `Claude API Key`

### Step 4: Set Workflow Variables
Edit the workflow and set these variables:
- `repo`: Your GitHub repo (e.g., `owner/repo`)
- `webhook_url`: Discord/Slack webhook URL
- `language`: EN or FR

### Step 5: Activate & Test
1. Click **Activate** button
2. Click **Execute Workflow** to test
3. Check your Discord/Slack for the summary!

---

## 📊 Workflow Nodes

| Node | Purpose |
|------|---------|
| Schedule Trigger | Weekly cron (Friday 5 PM) |
| Get Commits | Fetch last 7 days commits |
| Get Issues | Fetch closed issues |
| Get PRs | Fetch merged PRs |
| Merge Data | Combine all activity data |
| Claude API | Generate AI summary |
| Send to Discord/Slack | Deliver summary |

---

## 🔧 Configuration

### Cron Schedule
Default: `0 17 * * 5` (Friday 5 PM)

Customize:
```
0 9 * * 1    # Monday 9 AM
0 12 * * *   # Daily noon
```

### GitHub API Query
- Fetches last 7 days
- 100 items per request
- Requires `repo` scope token

### Claude Model
- Default: `claude-sonnet-4-20250514`
- Configurable in node settings

---

## 📝 Sample Output

```
📊 Weekly Development Summary for owner/repo

This week was incredibly active with 47 commits, 12 closed issues, and 8 merged PRs!

🎯 Key Accomplishments:
- Major refactoring of the authentication module
- Fixed critical bug in payment processing
- Added new user dashboard feature

📈 Notable Changes:
- Performance improvements in API endpoints (30% faster)
- Updated dependencies to latest versions
- Improved test coverage to 85%

👥 Community Activity:
- 5 new contributors joined
- 20 issues resolved by community
- Great collaboration on documentation updates

Keep up the amazing work! 🚀
```

---

## 🧪 Testing

### Manual Test
1. Click **Execute Workflow** in n8n
2. Check execution logs
3. Verify Discord/Slack message received

### Screenshot
![Workflow Execution](test-screenshot.png)

---

## 📁 Files

- `weekly-summary-workflow.json` - n8n workflow (importable)
- `README.md` - This documentation
- `test-screenshot.png` - Test execution proof

---

## 🏷️ Requirements

- **n8n**: Self-hosted or cloud instance
- **GitHub Token**: repo scope
- **Claude API Key**: Anthropic account
- **Webhook**: Discord or Slack channel

---

## 🎯 Acceptance Criteria

✅ Exportable n8n workflow (.json file)  
✅ Weekly cron trigger  
✅ Fetches commits, issues, PRs from GitHub  
✅ Calls Claude API for summary generation  
✅ Delivers via Discord/Slack webhook  
✅ Configurable variables (repo, channel, language)  
✅ Tested on real n8n instance  
✅ README with ≤5 step setup  

---

*Built by FanLi (范蠡) · Autonomous AI Agent*
