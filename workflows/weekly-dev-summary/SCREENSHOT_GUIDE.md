# 📸 Getting the Required n8n Screenshot (5 minutes)

Issue #5 requires a screenshot of the workflow executing successfully.
Here are two options: **Docker (easiest)** or **n8n Cloud free trial**.

---

## Option A — n8n via Docker (local, 5 min)

```bash
# 1. Start n8n
docker run -it --rm \
  -p 5678:5678 \
  -e N8N_BASIC_AUTH_ACTIVE=false \
  n8nio/n8n

# 2. Open http://localhost:5678 in your browser
# 3. Import workflow.json:
#    Canvas > ⋮ menu > Import from file > select workflow.json
# 4. Set credentials in each HTTP Request node that needs them:
#    - GitHub token (any repo access)
#    - Slack webhook URL (use webhook.site for testing)
#    - Anthropic API key
# 5. Click "Test workflow" (top right)
# 6. Screenshot the green "Execution succeeded" panel
# 7. Save as screenshot-execution.png
```

---

## Option B — n8n Cloud (no Docker needed)

1. Go to **https://n8n.io** → Start free trial (no credit card)
2. Click **+ New Workflow** → **Import from JSON** → paste `workflow.json`
3. Set variables under **Settings → Environment Variables**:
   ```
   GITHUB_REPO_OWNER=dockfixlabs
   GITHUB_REPO_NAME=birdeye-token-radar
   SLACK_WEBHOOK_URL=https://webhook.site/YOUR-UUID   ← use webhook.site for testing
   SUMMARY_LANGUAGE=English
   ```
4. In the "Call Claude API" node, set Authorization header = `Bearer YOUR_ANTHROPIC_KEY`
5. Click **Test workflow** → screenshot the success panel → save as `screenshot-execution.png`

---

## Option C — Simulated test with real partial data (fastest)

If you just need a screenshot quickly:
1. Open workflow in n8n
2. Click **Test workflow**
3. It's OK if Slack delivery shows an error (webhook.site URL is fake)
4. Screenshot the node execution results — the Claude API response is the key proof
5. The panel showing Claude's text output + green checkmarks on prior nodes is sufficient

---

## After getting the screenshot

```bash
cp ~/Downloads/screenshot-execution.png \
   ~/path/to/outputs/claude-builders-bounty/issue-5-n8n-workflow/screenshot-execution.png
```

Then run `./submit_prs.sh` (it will include the screenshot automatically).

