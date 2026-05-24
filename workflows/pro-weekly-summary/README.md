# J.A.R.V.I.S. Pro: Automated Weekly Dev Summary

This n8n workflow provides a production-grade automated summary of GitHub repository activity using the Claude 3.5 Sonnet API.

## 🌟 Key Features
- **Multi-Persona:** Choose between "Executive Summary" (high-level) or "Technical Deep-Dive" (detailed).
- **Multi-Channel:** Native support for **Telegram**, Slack, and Discord.
- **Multi-Language:** Fully configurable for EN, FR, ES, DE, and ZH.
- **Resilient:** Built-in error handling for API rate limits and connection timeouts.

## 🚀 Setup in 5 Steps
1. **Import:** Download `workflow.json` and import it into your n8n instance.
2. **Credentials:** Add your GitHub, Anthropic (Claude), and Telegram/Slack credentials.
3. **Variables:** Set the following variables in the "Config" node:
   - `GITHUB_OWNER` & `GITHUB_REPO`
   - `LANGUAGE` (e.g., EN)
   - `STYLE` (e.g., Executive)
4. **Trigger:** The workflow is preset to trigger every **Friday at 5:00 PM**.
5. **Activate:** Toggle the "Active" switch in n8n.

## 📊 Example Output
> ### 📝 Weekly Summary: [Repo Name]
> **Key Achievement:** Successfully migrated core database to PostgreSQL.
> **Fixed:** Resolved 12 critical bugs in the authentication layer.
> **Insight:** Development velocity has increased by 15% due to new CI/CD optimizations.

---
*Created by the J.A.R.V.I.S. Engineering Lab*
