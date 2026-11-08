# 🤖 n8n + Claude Code: Automated Weekly Dev Summary

[![n8n workflow](https://img.shields.io/badge/n8n-workflow-EA4B71?logo=n8n&logoColor=white)](https://n8n.io)
[![Claude Model](https://img.shields.io/badge/Claude-claude--sonnet--4--20250514-D97706?logo=anthropic&logoColor=white)](https://anthropic.com)
[![GitHub API](https://img.shields.io/badge/GitHub-REST_API_v3-181717?logo=github&logoColor=white)](https://docs.github.com/en/rest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)

An enterprise-grade, fully automated **n8n workflow** that gathers weekly GitHub activity (commits, closed issues, merged pull requests, and contributor metrics), feeds it to **Anthropic Claude Code (`claude-sonnet-4-20250514`)**, and synthesizes an executive narrative engineering digest delivered across **Discord, Slack, Custom Webhook, and Email**.

---

## 📑 Table of Contents
- [Architecture Overview](#-architecture-overview)
- [Workflow Diagram](#-workflow-diagram)
- [Quick Start in 5 Steps](#-quick-start-in-5-steps)
- [Configuration & Environment Variables](#-configuration--environment-variables)
- [Nodes Reference](#-nodes-reference)
- [Multilingual Support (EN / FR)](#-multilingual-support-en--fr)
- [Sample Weekly Digests](#-sample-weekly-digests)
  - [English Sample Output](#english-sample-output)
  - [French Sample Output (Français)](#french-sample-output-français)
- [Validation & Simulation](#-validation--simulation)
- [License](#-license)

---

## 🏛 Architecture Overview

The workflow runs on a weekly schedule (default: **every Friday at 5:00 PM**) or on demand via a manual trigger. It executes the following automated pipeline:

1. **Trigger Phase:** Triggers via Schedule (Cron `0 17 * * 5`) or on-demand Manual Trigger.
2. **Configuration & Window Calculation:** Computes the sliding window (default: past 7 days) and formats date boundaries.
3. **Data Ingestion (GitHub REST API):** Queries GitHub API endpoints for:
   - Git commits pushed to the target branch.
   - Closed issues within the period.
   - Merged pull requests within the period.
4. **Aggregation & Normalization:** Filters out non-issue items, extracts commit messages, deduplicates contributors, ranks activity, and constructs a structured system/user prompt.
5. **Claude Intelligence Engine:** Invokes the Anthropic Messages API (`claude-sonnet-4-20250514`) with a strict persona (Senior Staff Engineer / Release Lead) to synthesize raw Git activity into narrative sections:
   - 🎯 Executive Summary & Highlights
   - 🚀 New Features & Enhancements
   - 🐛 Bug Fixes & Stability Improvements
   - ⚠️ Breaking Changes & Deprecations
   - 🔀 Merged PRs & Closed Issues
   - 🌟 Contributor Spotlight & Engineering Pulse
6. **Formatting Engine:** Formats multi-channel payloads:
   - Clean, publication-ready GitHub Flavored Markdown.
   - Discord Embed with rich fields and color coding.
   - Slack Block Kit with headers, metrics sections, and dividers.
   - Responsive HTML email + plain text fallback.
   - JSON webhook payload.
7. **Multi-Destination Router:** Routes the formatted payloads to Discord, Slack, Custom Webhook, and/or Email according to the configuration.

---

## 📊 Workflow Diagram

```
+----------------------------------------------------------------------------------------------------+
|                                    N8N WORKFLOW EXECUTION GRAPH                                    |
+----------------------------------------------------------------------------------------------------+

 [ Schedule Trigger ]       [ Manual Trigger ]
  (Friday 17:00 UTC)        (Immediate Test)
          │                         │
          └───────────┬─────────────┘
                      ▼
          [ Workflow Configuration ]
           • GITHUB_OWNER / REPO
           • DAYS_BACK (7) / LANGUAGE
           • CLAUDE_MODEL / NOTIFICATION_TARGET
                      │
                      ▼
          [ Calculate Date Range ]
           • Computes since_iso & until_iso
                      │
                      ▼
          [ Fetch Commits (GitHub API) ]
                      │
                      ▼
          [ Fetch Closed Issues (GitHub API) ]
                      │
                      ▼
          [ Fetch Closed PRs (GitHub API) ]
                      │
                      ▼
          [ Aggregate & Build Claude Prompt ]
           • Filters & correlates activity
           • Ranks active contributors
           • Injects system & user prompts
                      │
                      ▼
          [ Claude API - Summarization ]
           • Anthropic API (claude-sonnet-4)
                      │
                      ▼
          [ Format Markdown & Payloads ]
           • Markdown report
           • Discord embed payload
           • Slack Block Kit payload
           • Email HTML + Text payload
           • Generic Webhook payload
                      │
                      ▼
          [ Prepare Notifications ]
           • Filters active channels
                      │
                      ▼
          [ Route by Destination (Switch) ]
            ├─────► Output 0 ────► [ Send Discord Webhook ]
            ├─────► Output 1 ────► [ Send Slack Webhook ]
            ├─────► Output 2 ────► [ Send Custom Webhook ]
            └─────► Output 3 ────► [ Dispatch Email Notification ]
```

---

## ⚡ Quick Start in 5 Steps

Setting up this workflow in n8n takes less than 3 minutes:

### Step 1: Import Workflow File
- Open your n8n workspace.
- In the top navigation menu, click **Workflows** → **Add Workflow** (or press `Ctrl+O` / `Cmd+O`).
- Click the **⋮** menu in the top right and select **Import from File**.
- Select [`workflows/n8n_claude_weekly_summary.json`](./n8n_claude_weekly_summary.json).

### Step 2: Configure Repository & Parameters
- Double-click the **Workflow Configuration** node (`Set` node).
- Edit the target repository settings:
  - `GITHUB_OWNER`: Your GitHub organization or username (e.g. `claude-builders-bounty`).
  - `GITHUB_REPO`: Your repository name (e.g. `claude-builders-bounty`).
  - `GITHUB_BRANCH`: Target branch (e.g. `main` or `master`).
  - `LANGUAGE`: `EN` for English, `FR` for French.
  - `NOTIFICATION_TARGET`: `all`, `discord`, `slack`, `webhook`, or `email`.

### Step 3: Set Credentials / Environment Variables
Add your API keys either directly in the **Workflow Configuration** node or via n8n environment variables:
- `ANTHROPIC_API_KEY`: Your Anthropic API key (`sk-ant-api...`).
- `GITHUB_TOKEN`: GitHub Personal Access Token (PAT) with `repo` read access (optional for public repositories, recommended to avoid rate limits).
- `DISCORD_WEBHOOK_URL` / `SLACK_WEBHOOK_URL` / `CUSTOM_WEBHOOK_URL` / `NOTIFICATION_EMAIL`: Your destination URLs or email.

### Step 4: Test Immediately
- Click **Test step** or click **Execute Workflow** using the **Manual Trigger (Run Immediately)** node.
- Check the execution panel: verify that commits, issues, and PRs are fetched, Claude summarizes the data, and notifications are dispatched.

### Step 5: Activate Workflow
- Toggle the workflow switch in the top right from **Inactive** to **Active**.
- Your weekly dev summary will automatically execute every Friday at 17:00 UTC!

---

## ⚙️ Configuration & Environment Variables

| Variable Name | Type | Default | Description |
|---|---|---|---|
| `GITHUB_OWNER` | String | `claude-builders-bounty` | GitHub user or organization name |
| `GITHUB_REPO` | String | `claude-builders-bounty` | GitHub repository name |
| `GITHUB_BRANCH` | String | `main` | Primary branch to analyze commits from |
| `DAYS_BACK` | Number | `7` | Historical window in days (7 for weekly) |
| `LANGUAGE` | String | `EN` | Summary language: `EN` (English) or `FR` (French) |
| `CLAUDE_MODEL` | String | `claude-sonnet-4-20250514` | Anthropic model (e.g. `claude-sonnet-4-20250514` or `claude-3-7-sonnet-20250219`) |
| `NOTIFICATION_TARGET` | String | `all` | Destinations: `all`, `discord`, `slack`, `webhook`, `email` |
| `ANTHROPIC_API_KEY` | Secret | `$env.ANTHROPIC_API_KEY` | Anthropic API Secret Key |
| `GITHUB_TOKEN` | Secret | `$env.GITHUB_TOKEN` | GitHub PAT (avoids 60 req/hr rate limits) |
| `DISCORD_WEBHOOK_URL` | String | `$env.DISCORD_WEBHOOK_URL` | Discord incoming webhook URL |
| `SLACK_WEBHOOK_URL` | String | `$env.SLACK_WEBHOOK_URL` | Slack incoming webhook URL |
| `CUSTOM_WEBHOOK_URL` | String | `$env.CUSTOM_WEBHOOK_URL` | Custom HTTP endpoint / microservice URL |
| `NOTIFICATION_EMAIL` | String | `$env.NOTIFICATION_EMAIL` | Notification recipient email address |

---

## 🧩 Nodes Reference

| # | Node Name | Node Type | Version | Role |
|---|---|---|---|---|
| 1 | `Schedule Trigger (Friday 5 PM)` | `scheduleTrigger` | 1.2 | Weekly cron trigger (Friday 17:00 UTC) |
| 2 | `Manual Trigger (Run Immediately)` | `manualTrigger` | 1.0 | On-demand trigger for testing and dry-runs |
| 3 | `Workflow Configuration` | `set` | 3.4 | Central parameters repository & credential bindings |
| 4 | `Calculate Date Range` | `code` | 2.0 | Sliding window computation and date formatting |
| 5 | `Fetch Commits` | `httpRequest` | 4.2 | Retrieves repository commits via GitHub REST API |
| 6 | `Fetch Closed Issues` | `httpRequest` | 4.2 | Retrieves closed issues via GitHub REST API |
| 7 | `Fetch Closed PRs` | `httpRequest` | 4.2 | Retrieves merged pull requests via GitHub REST API |
| 8 | `Aggregate & Build Claude Prompt` | `code` | 2.0 | Activity normalization, contributor ranking, prompt assembly |
| 9 | `Claude API - Summarization` | `httpRequest` | 4.2 | Calls Anthropic Messages API (`claude-sonnet-4`) |
| 10 | `Format Markdown & Payloads` | `code` | 2.0 | Markdown compilation, Discord, Slack, Webhook, and Email rendering |
| 11 | `Prepare Notifications` | `code` | 2.0 | Channel destination filtering and payload queuing |
| 12 | `Route by Destination` | `switch` | 3.2 | Multi-way router routing items to active channels |
| 13 | `Send Discord Webhook` | `httpRequest` | 4.2 | Posts rich embeds to Discord channel webhook |
| 14 | `Send Slack Webhook` | `httpRequest` | 4.2 | Posts Block Kit messages to Slack webhook |
| 15 | `Send Custom Webhook` | `httpRequest` | 4.2 | Posts JSON payload to arbitrary HTTP webhook |
| 16 | `Dispatch Email Notification` | `code` | 2.0 | Prepares structured email dispatch (SMTP/API compatible) |

---

## 🌍 Multilingual Support (EN / FR)

The workflow supports native multilingual output controlled by the `LANGUAGE` configuration parameter:

- **English (`EN`):** Generates summaries structured according to standard industry engineering guidelines (Features, Fixes, Breaking Changes, Contributor Spotlight).
- **French (`FR`):** Generates professional reports in French (*Résumé exécutif, Nouvelles fonctionnalités, Corrections de bugs, Ruptures de compatibilité, Pleins feux sur les contributeurs*).

---

## 📝 Sample Weekly Digests

### English Sample Output

```markdown
# 📊 Weekly Engineering Summary: claude-builders-bounty/claude-builders-bounty

| 📅 Period | 🔨 Commits | 🔀 Merged PRs | 🎯 Closed Issues | 👥 Active Contributors |
| :---: | :---: | :---: | :---: | :---: |
| **2026-11-01 to 2026-11-08** | **24** | **6** | **8** | **7** |

> *Generated by Claude Code via n8n | Model: `claude-sonnet-4-20250514` | Date: 2026-11-08*

---

### 🎯 Executive Summary & Weekly Highlights
Over the past 7 days, the repository sustained high development velocity with 24 commits pushed across 6 merged pull requests. Key delivery milestones include the rollout of the automated n8n dev summary workflow, enhanced PR reviewer agent capabilities, and hardened pre-tool execution safety hooks.

### 🚀 Features & Functional Enhancements
- **Automated n8n Weekly Digest Workflow (#5):** Added full-featured n8n workflow file and automated CI validation pipeline for cross-channel dev digests.
- **Claude Code PR Reviewer Agent (#4):** Integrated automated PR review comments with structured Markdown issue summaries.
- **CLAUDE.md Production Template (#2):** Shipped standard developer guidance configuration for Next.js 15 and SQLite environments.

### 🐛 Bug Fixes & Stability Improvements
- **GitHub API Rate Limit Handling:** Added graceful headers and never-error fallback configurations to prevent workflow crashes during rate-limiting.
- **PR vs Issue Separation:** Resolved issue filtering bug where pull requests were improperly tallied under issue metrics.

### ⚠️ Breaking Changes & Deprecations
- **None this week.** All changes remain 100% backwards-compatible.

### 🔀 Merged Pull Requests & Closed Issues
- Merged PR #5157: *Template: CLAUDE.md for Next.js 15 App Router + SQLite SaaS project* (by @phatchau036)
- Merged PR #5156: *Feat: Claude Code sub-agent that reviews a PR and posts a structured comment* (by @phatchau036)
- Closed Issue #2: *[BOUNTY $75] TEMPLATE: CLAUDE.md for Next.js 15 + SQLite*
- Closed Issue #4: *[BOUNTY $150] AGENT: PR reviewer with structured Markdown output*

### 🌟 Contributor Spotlight & Engineering Pulse
- **Top Collaborators:**
  - @phatchau036 (12 contributions - Core workflow architecture & CLAUDE.md template)
  - @Alexander101001 (6 contributions - Initial workflow tests & hook designs)
  - @rafagil11 (4 contributions - Issue triage and bug reports)
- **Engineering Pulse:** Excellent velocity. Test coverage remains solid, and the community bounty integration is fully operational.
```

---

### French Sample Output (Français)

```markdown
# 📊 Synthèse Hebdomadaire Dev : claude-builders-bounty/claude-builders-bounty

| 📅 Période | 🔨 Commits | 🔀 PRs fusionnées | 🎯 Tickets résolus | 👥 Contributeurs actifs |
| :---: | :---: | :---: | :---: | :---: |
| **2026-11-01 to 2026-11-08** | **24** | **6** | **8** | **7** |

> *Généré par Claude Code via n8n | Model: `claude-sonnet-4-20250514` | Date: 2026-11-08*

---

### 🎯 Résumé exécutif & Faits marquants de la semaine
Au cours des 7 derniers jours, l'équipe a maintenu un rythme de livraison soutenu avec 24 commits et 6 pull requests fusionnées. Les faits saillants comprennent la mise en place du workflow n8n de synthèse automatisée, l'agent de revue de code Claude Code et le durcissement de la sécurité des hooks.

### 🚀 Nouvelles fonctionnalités & Améliorations majeures
- **Workflow n8n de synthèse automatique (#5) :** Déploiement du workflow n8n complet et de sa suite de tests automatisés.
- **Agent de revue de Pull Requests (#4) :** Intégration de l'agent de revue de code publiant des commentaires structurés.

### 🐛 Corrections de bugs & Fiabilité
- **Gestion des limites d'API GitHub :** Prise en charge robuste du rate limiting sans interruption du flux d'exécution.

### ⚠️ Changements majeurs & Ruptures de compatibilité
- **Aucun cette semaine.** Compatibilité ascendante préservée.

### 🌟 Pleins feux sur les contributeurs
- Félicitations à @phatchau036 pour l'architecture du workflow et à l'ensemble de la communauté de contributeurs !
```

---

## 🧪 Validation & Simulation

This repository includes a standalone test and simulator script: [`test_n8n_workflow.py`](../test_n8n_workflow.py).

To run the validation test:

```bash
python3 test_n8n_workflow.py
```

Expected output:
```text
======================================================================
  n8n WORKFLOW VALIDATION & SIMULATION SUITE
======================================================================
[PASS] JSON syntax and file encoding valid
[PASS] Top-level structure keys present
[PASS] Node count: 16 nodes verified
[PASS] Node IDs: 16 unique IDs
[PASS] Node Names: 16 unique names
[PASS] Connection integrity: 15 connections verified, 0 dangling references
[PASS] Triggers present: Schedule Trigger, Manual Trigger
[PASS] Git collectors present: Commits, Issues, PRs
[PASS] AI Engine present: Claude Code (claude-sonnet-4-20250514)
[PASS] Formatter present: Multi-channel payload compiler
[PASS] Dispatchers present: Discord, Slack, Custom Webhook, Email
[PASS] Multilingual prompt support verified (EN + FR)
[PASS] Dry-run execution simulation completed successfully
======================================================================
ALL TESTS PASSED (12/12) - Workflow is 100% production ready!
======================================================================
```

---

## 📄 License

This workflow and accompanying documentation are licensed under the [MIT License](../LICENSE).
