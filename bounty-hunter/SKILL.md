---
name: bounty-hunter
description: Automated bounty hunting skill that monitors GitHub for high-value, low-competition bounties and alerts via Discord. Use when you want to discover new earning opportunities based on specific ROI criteria.
---

# Bounty Hunter Skill

This skill transforms Gemini CLI into a proactive profit-seeking agent. It scans GitHub issues for active bounties, filters them based on reward value and competition levels, and sends real-time alerts to your Discord/Slack workspace.

## ROI Filters
- **Value**: Rewards > $50.
- **Competition**: Issues with fewer than 10 comments (High probability of successful claim).

## Integration
- **Platform**: GitHub (via labels).
- **Alerts**: Discord Webhook (configured via `DISCORD_WEBHOOK_URL`).

## Implementation Details

The skill uses `scripts/hunt_bounties.cjs` to perform the scan and delivery.

## Workflow

1.  **Initialize Hunt**: Run `node scripts/hunt_bounties.cjs`.
2.  **Filter**: The script automatically applies the ROI filters.
3.  **Alert**: If opportunities match, a structured alert is sent to the configured webhook.
