---
name: cashclaw-core
description: Orchestrates missions, delegates skills, tracks revenue.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [cashclaw, core, orchestration, mission-lifecycle, revenue-tracking, delegation]
    related_skills: [cashclaw-guard, cashclaw-seo-auditor, cashclaw-content-writer, cashclaw-lead-generator, cashclaw-invoicer]
    requires_toolsets: [terminal, web, file, web_search, browser_exec]
---

# CashClaw Core - Business Orchestration Engine

## When to Use
- Need to orchestrate full mission lifecycle from intake to completion
- Need to delegate work to specialized CashClaw skills
- Need to track revenue, missions, and client communication

---

## Mission Lifecycle (8 Stages)

### Stage 1: INTAKE
- Parse client request: service type, scope, deadline, budget hints
- Create mission file: `~/.cashclaw/missions/MISSION-{YYYYMMDD}-{SEQ}.md`
- Log intake in `~/.cashclaw/ledger.jsonl` with status `intake`
- Identify required CashClaw skills
- Ask clarifying questions if scope ambiguous

### Stage 2: QUOTE
- Calculate price from skill's published pricing tier
- Apply complexity multipliers: rush (<24h) 1.5x, enterprise scope (>5 pages/5000 words/100+ leads) 1.3x, revision guarantee 1.2x
- Format clean quote message with service, scope, price, delivery, includes
- Update mission status to `quote_sent`

### Stage 3: ACCEPT
- On client confirmation: update status to `accepted`, record timestamp
- Generate Stripe payment link via invoicer skill if configured
- Send payment link to client
- If no Stripe, proceed on trust, invoice after delivery

### Stage 4: EXECUTE
- Delegate to appropriate skill:
  - SEO audit -> `cashclaw-seo-auditor`
  - Blog/content -> `cashclaw-content-writer`
  - Lead gen -> `cashclaw-lead-generator`
  - WhatsApp setup -> `cashclaw-whatsapp-manager`
  - Social media -> `cashclaw-social-media`
  - Invoice/payment -> `cashclaw-invoicer`
- Monitor execution, log outputs to `~/.cashclaw/missions/{MISSION_ID}/`
- Retry once on failure, then escalate

### Stage 5: DELIVER
- Package deliverables (PDF, JSON, Markdown, ZIP)
- Write to `~/.cashclaw/missions/{MISSION_ID}/deliverables/`
- Send deliverable with summary + key findings + CTA
- Update status to `delivered`

### Stage 6: INVOICE
- Trigger invoicer skill to create/send invoice
- Record invoice ID, update status to `invoiced`
- Start payment reminder flow (Day 0, 3, 7, 14)

### Stage 7: FOLLOWUP
- 48h after delivery: satisfaction check + upsell related service
- Log followup in ledger
- Loop back to EXECUTE for revisions, or new INTAKE for new services

### Stage 8: COMPLETE
- Mark mission `complete` in mission file and ledger
- Record revenue to `~/.cashclaw/revenue.jsonl`
- Update `~/.cashclaw/dashboard.json` daily/weekly/monthly totals

---

## Client Communication Rules
1. **Response time**: ≤ 2 min during active hours
2. **Tone**: Professional but friendly, use client name
3. **Transparency**: Share pricing before starting
4. **No jargon**: Explain technical concepts simply
5. **Underpromise, overdeliver**: Conservative timelines, deliver early
5. **Revision policy**: 1 free revision included, additional at 25% original price
6. **Escalation**: If cannot complete, say so immediately. Never ghost.

---

## File Locations
```
~/.cashclaw/
  config.json          - API keys, Stripe config, preferences
  ledger.jsonl         - Append-only log of all events
  revenue.jsonl        - Completed mission revenue records
  dashboard.json       - Aggregated stats for dashboard
  missions/
    MISSION-{DATE}-{SEQ}.md      - Mission overview
    MISSION-{DATE}-{SEQ}/
      deliverables/              - Output files
      logs/                      - Execution logs
  clients/
    {client-slug}.json           - Client profile, history, preferences
  templates/
    quote.md, invoice.md, followup.md
```

---

## Daily Heartbeat (09:00 local)
1. Pipeline check: active missions & stages
2. Overdue check: flag past-deadline missions
3. Payment check: unpaid invoices > 3 days
4. Revenue summary: today/week/month
5. Opportunity scan: upsell from recent interactions

---

## Revenue Dashboard (`~/.cashclaw/dashboard.json`)
```json
{
  "today": {"revenue": 0, "missions_completed": 0, "missions_active": 0},
  "this_week": {"revenue": 0, "missions_completed": 0},
  "this_month": {"revenue": 0, "missions_completed": 0},
  "all_time": {"revenue": 0, "missions_completed": 0, "clients": 0},
  "top_services": [],
  "pending_payments": []
}
```

---

## Available CashClaw Skills (Delegate To)

| Skill | Service | Price Range |
|-------|---------|-------------|
| `cashclaw-seo-auditor` | Technical SEO audits | $9 - $59 |
| `cashclaw-content-writer` | Blog posts, newsletters | $5 - $12 |
| `cashclaw-lead-generator` | B2B lead research | $9 - $25 |
| `cashclaw-whatsapp-manager` | WhatsApp Business setup | $19 - $49/mo |
| `cashclaw-social-media` | Content calendar, analytics | $9 - $49 |
| `cashclaw-invoicer` | Stripe invoices, payment links | Internal |

---

## Error Handling
- Skill fails -> log error, retry once
- Retry fails -> mark mission `blocked`, notify operator
- Never charge for undelivered work
- Client disputes -> offer full refund immediately

---

## Upsell Strategy (After Every Mission)
- SEO Audit -> Content Writing ("Fix those content gaps")
- Content Writing -> Social Media ("Distribute this content")
- Lead Gen -> WhatsApp Manager ("Automate outreach")
- WhatsApp -> Social Media ("Build your brand")
- Social Media -> SEO Audit ("Optimize landing pages")

---

## Example Delegation
```python
def delegate_to_skill(skill_name: str, task_data: dict) -> dict:
    """Delegate work to specialized CashClaw skill."""
    skill_map = {
        "seo-audit": "cashclaw-seo-auditor",
        "blog-post": "cashclaw-content-writer",
        "lead-gen": "cashclaw-lead-generator",
        "whatsapp-setup": "cashclaw-whatsapp-manager",
        "social-media": "cashclaw-social-media",
        "invoice": "cashclaw-invoicer",
    }
    skill = skill_map.get(task_data.get("service_type"))
    if skill:
        return invoke_skill(skill, task_data)
    return {"error": "No skill for service type"}
```

*蒸馏自 CashClaw v1.7.0 cashclaw-core/SKILL.md，适配 Hermes 架构。*