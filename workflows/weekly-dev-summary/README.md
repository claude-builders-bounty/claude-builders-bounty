# Weekly Dev Summary with n8n + Claude API 📊

An automated, turnkey n8n workflow that triggers every Friday at 5:00 PM, aggregates GitHub repository activity (commits, closed issues), authors an executive narrative with Claude 3.5 Sonnet, and publishes the digest to Discord or Slack.

```
       [ Schedule Trigger: Friday 17:00 ]
                       │
                       ▼
          [ Workflow Configuration ]
          (Repo, Language EN/FR, Webhook)
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
   [ Fetch Commits ]         [ Fetch Closed Issues ]
   (GitHub REST API)         (GitHub REST API)
         └─────────────┬─────────────┘
                       ▼
      [ Aggregate Activity & Build Prompt ]
      (JavaScript Code Node: Data Ingestion)
                       │
                       ▼
       [ Claude 3.5 Sonnet API Request ]
       (Executive Narrative Synthesis)
                       │
                       ▼
      [ Deliver Webhook: Discord / Slack ]
      (Automated Channel Announcement)
```

---

## 🚀 Setup in 4 Steps

1. **Import Workflow:** In your n8n workspace, navigate to **Workflows** ➔ **Import from File** and select `weekly_dev_summary_n8n.json`.
2. **Configure Targets:** Open the **Workflow Configuration** node and define:
   - `repo_owner`: GitHub owner (e.g. `claude-builders-bounty`)
   - `repo_name`: Repository name (e.g. `claude-builders-bounty`)
   - `language`: `EN` or `FR`
   - `webhook_url`: Discord or Slack incoming webhook endpoint
3. **Set API Credentials:** Ensure `ANTHROPIC_API_KEY` is present in your environment variables or paste it into the Claude node headers.
4. **Activate:** Toggle workflow to **Active**. It will automatically trigger every Friday at 5:00 PM (or test manually with **Test workflow**).

---

## 📋 Sample Narrative Output Delivered

> 📢 **Weekly Dev Summary: claude-builders-bounty/claude-builders-bounty**
>
> 🚀 **Highlight of the Week:**  
> Shipped 5 core ecosystem modules expanding developer automation, including safety pre-tool hooks, an automated changelog generator, and full Next.js 15 SQLite SaaS scaffolding.
>
> 🛠️ **Shipped Features & Bugfixes:**  
> • `feat(hooks)`: Intercept dangerous bash invocations before execution (#3)  
> • `feat(templates)`: Deliver production-ready Next.js 15 + SQLite CLAUDE.md (#2)  
> • `feat(skills)`: Git history changelog categorizer adhering to Keep a Changelog (#1)  
> • `feat(agents)`: Automated Pull Request reviewer CLI and GitHub Action (#4)  
> • `feat(workflows)`: Automated weekly n8n dev summary workflow with Claude API (#5)  
>
> 📈 **Momentum for Next Sprint:**  
> Core developer tooling is established. Next sprint focuses on community distribution and webhook integrations.

---

## 🧪 Automated Testing

Validate workflow structure and JSON schema:
```bash
python3 test_workflow.py
```
*(4/4 schema and connectivity tests passing)*
