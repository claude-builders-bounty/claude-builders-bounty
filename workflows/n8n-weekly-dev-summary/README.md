# Weekly Dev Summary — n8n + Claude

An importable **n8n workflow** that, every Friday at 17:00, pulls a GitHub repo's
week of activity (commits, closed issues, merged PRs), asks Claude for a narrative
summary, and posts it to Slack/Discord (or email).

## Setup (5 steps)
1. In n8n: **Import from File** → `workflow.json`.
2. Set the environment variable **`ANTHROPIC_API_KEY`** (n8n → Settings → Variables/Env).
3. Open the **⚙️ Config** node and set: `githubRepo` (`owner/repo`), `language` (`EN`/`FR`), `destination` (your Slack or Discord webhook URL).
4. *(Private repos)* add an `Authorization: Bearer <token>` header to the three GitHub nodes.
5. **Activate** the workflow. Default trigger: **cron `0 17 * * 5`** (Friday 17:00).

## What it does
| Node | Purpose |
|---|---|
| Weekly Trigger | cron `0 17 * * 5` |
| ⚙️ Config | repo, language (EN/FR), destination, `since` (7 days ago) |
| GitHub ×3 | commits, closed issues, merged PRs (`since={7d}`) |
| Merge activity | combine the three streams |
| Build Claude prompt | format activity into one prompt |
| Claude API | `claude-sonnet-4-20250514`, returns the narrative |
| Deliver | POSTs the summary to your webhook |

## Delivery format
- **Slack** expects `{ "text": "..." }` (default).
- **Discord** expects `{ "content": "..." }` — change the body key in the Deliver node.

## Validate without n8n
```bash
python3 validate_workflow.py      # checks structure + connection integrity
# OK: 9 nodes, 8 connections, trigger present
```

## Sample output
See [`examples/SAMPLE_SUMMARY.md`](examples/SAMPLE_SUMMARY.md).

## Notes
- Only core n8n nodes — no community packages to install.
- The workflow is language-configurable (`EN`/`FR`) and repo-agnostic.
