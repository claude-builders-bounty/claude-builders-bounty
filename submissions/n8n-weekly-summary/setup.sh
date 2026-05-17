#!/bin/bash
# Quick setup script for n8n Weekly Summary Workflow

echo "🚀 n8n Weekly Dev Summary - Quick Setup"
echo ""

# Check if n8n is installed
if ! command -v n8n &> /dev/null; then
    echo "⚠️  n8n CLI not found. Install options:"
    echo "   npm install -g n8n"
    echo "   docker run -it --rm n8nio/n8n"
    echo ""
fi

echo "📋 Setup Checklist:"
echo ""
echo "1. Import Workflow"
echo "   - Open n8n UI (http://localhost:5678)"
echo "   - Workflows → Import from File"
echo "   - Select: weekly-dev-summary.json"
echo ""
echo "2. Configure Credentials"
echo "   - Anthropic (Claude API): https://console.anthropic.com"
echo "   - GitHub Token (optional): https://github.com/settings/tokens"
echo "   - Slack Webhook: https://api.slack.com/messaging/webhooks"
echo "   - OR SMTP for email"
echo ""
echo "3. Set Environment Variables in n8n:"
echo "   GITHUB_OWNER=your-username"
echo "   GITHUB_REPO=your-repo"
echo "   LANGUAGE=EN"
echo "   DESTINATION_CHANNEL=#your-channel"
echo "   EMAIL_RECIPIENTS=team@example.com"
echo ""
echo "4. Activate Workflow"
echo "   - Click 'Active' toggle"
echo "   - Test with 'Execute Workflow'"
echo ""
echo "📖 Full documentation: README.md"
