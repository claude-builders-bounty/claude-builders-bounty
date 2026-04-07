# Weekly GitHub Development Summary with Claude AI

Automatically generate weekly development summaries for your GitHub repositories using n8n, GitHub API, and Claude AI.

## 🎯 Features

- **Multi-repository support**: Monitor multiple GitHub repositories in a single workflow
- **Smart summaries**: Claude AI generates professional, narrative summaries
- **Flexible delivery**: Send to Discord, Slack, or Email
- **Configurable**: Set language (EN/FR), schedule, and output format
- **Error handling**: Automatic retries, fallback strategies, and alerts
- **Monitoring**: Built-in execution tracking and status dashboard

## 🚀 5-Step Setup Guide

### Step 1: Install n8n
```bash
# Using npm
npm install n8n -g

# Using Docker
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

### Step 2: Import the Workflow
1. Open n8n at `http://localhost:5678`
2. Click **Import from File**
3. Select `n8n_weekly_summary_workflow.json`
4. Click **Import**

### Step 3: Configure Environment Variables
Create a `.env` file in your n8n directory:
```env
# GitHub Configuration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPOS=owner1/repo1,owner2/repo2

# Claude AI Configuration
CLAUDE_API_KEY=your_claude_api_key
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Output Configuration
OUTPUT_CHANNEL=discord  # discord, slack, or email
LANGUAGE=en  # en or fr

# Discord (if using discord)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Slack (if using slack)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Email (if using email)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
EMAIL_RECIPIENT=recipient@example.com
```

### Step 4: Configure the Workflow
1. In n8n, open the imported workflow
2. Update the **Schedule Trigger** node:
   - Set to run every Friday at 5 PM UTC
   - Or customize to your preferred schedule
3. Verify all nodes are correctly connected

### Step 5: Activate and Test
1. Click **Execute Workflow** to test immediately
2. Check the execution log for errors
3. Once successful, **Activate** the workflow
4. Verify the summary arrives in your chosen channel

## 📊 Configuration Options

### GitHub Repositories
- Single repository: `owner/repo`
- Multiple repositories: `owner1/repo1,owner2/repo2,owner3/repo3`
- Organization-wide: Set to monitor all organization repositories (advanced)

### Schedule Options
- Weekly (default): Every Friday at 5 PM UTC
- Custom: Configure in the Schedule Trigger node
- Manual: Run on-demand for ad-hoc summaries

### Output Channels
- **Discord**: Rich formatted messages with stats and summary
- **Slack**: Block-based messages with interactive elements
- **Email**: Plain text or HTML formatted emails
- **Multiple**: Send to all channels simultaneously

### Language Support
- **English (en)**: Professional technical summaries
- **French (fr)**: Summaries in French with appropriate tone

## 🔧 Advanced Features

### Error Handling & Retry
- Automatic retry for failed API calls (3 attempts)
- Fallback to template-based summaries if Claude API fails
- Alert notifications for critical failures

### Monitoring Dashboard
Access the built-in monitoring dashboard at `http://localhost:3000/status` (if enabled) to view:
- Last execution time and status
- Success/failure statistics
- Repository coverage
- Performance metrics

### Multi-Repository Aggregation
When monitoring multiple repositories:
- Individual summaries for each repository
- Aggregated organization-wide summary
- Comparative statistics across projects

## 🐛 Troubleshooting

### Common Issues

**GitHub API Rate Limiting**
```bash
# Check your rate limit
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
```
Solution: Use a GitHub Personal Access Token with appropriate scope.

**Claude API Errors**
- Verify your API key has sufficient credits
- Check the model name matches your subscription
- Ensure prompt length is within limits

**n8n Connection Issues**
- Verify n8n is running: `n8n --version`
- Check port 5678 is accessible
- Review n8n logs for errors

**Webhook Delivery Failures**
- Verify webhook URLs are correct
- Check channel permissions
- Test webhooks with simple messages first

### Debug Mode
Enable debug logging in n8n:
```bash
export N8N_LOG_LEVEL=debug
n8n start
```

## 📝 Example Output

### Discord/Slack Example
```
📊 Weekly Development Summary - openclaw/openclaw
Period: 2026-03-31 to 2026-04-07

Stats: 42 commits, 18 issues closed, 9 PRs merged

This week, the team focused on improving the agent memory system with 42 commits...
```

### Email Example
```
Subject: 📊 Weekly Development Summary - openclaw/openclaw

Period: 2026-03-31 to 2026-04-07

Stats:
- Commits: 42
- Issues Closed: 18  
- PRs Merged: 9

Summary:
This week, the team focused on improving the agent memory system...
```

## 🔒 Security Notes

- All API keys are stored as environment variables
- No sensitive data in the workflow JSON
- GitHub token requires `repo` scope for private repositories
- Claude API key should have usage limits set
- Webhook URLs should be kept confidential

## 📈 Monitoring & Analytics

The workflow includes built-in monitoring:
- Execution success/failure tracking
- Performance timing for each step
- Repository activity metrics
- Error rate and retry statistics

Access metrics via:
1. n8n execution history
2. Built-in status dashboard (if enabled)
3. Output channel success messages

## 🤝 Contributing

Found an issue or have an improvement?
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with detailed description

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgements

- [n8n](https://n8n.io) for the workflow automation platform
- [Anthropic](https://anthropic.com) for the Claude AI API
- [GitHub](https://github.com) for the API and platform

---

**Next Steps**: After successful setup, consider:
1. Adding custom metrics tracking
2. Integrating with project management tools
3. Setting up alert rules for critical changes
4. Creating custom summary templates

**Need Help?** Open an issue or check the troubleshooting section above.