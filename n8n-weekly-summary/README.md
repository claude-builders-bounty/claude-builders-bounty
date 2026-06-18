# n8n Weekly Dev Summary Workflow

An n8n workflow that fetches weekly git activity (commits, issues, PRs), generates a structured summary using OpenRouter's free `gpt-oss-120b` model, and delivers it to Discord.

## Why this approach

Unlike competitors that require Anthropic Claude API keys (geo-restricted in China), this workflow uses **OpenRouter's free `gpt-oss-120b:free` model** — zero cost, works globally.

## Features

- ✅ **Weekly cron trigger** (Friday 17:00 Asia/Shanghai)
- ✅ **Fetches 3 data sources in parallel**: Commits, Issues, PRs
- ✅ **Structured prompt** builds a narrative summary
- ✅ **Free LLM**: OpenRouter `gpt-oss-120b:free` (no API cost)
- ✅ **Discord delivery**: Posts summary to configured channel
- ✅ **Configurable**: Change repo, channel, schedule in settings

## Setup

### 1. Import the workflow

1. Open n8n → Workflows → Import from File
2. Select `weekly-dev-summary.json`
3. Configure credentials (see below)

### 2. Required credentials

| Credential | Type | Purpose |
|---|---|---|
| GitHub Token | GitHub | Fetch commits/issues/PRs |
| Discord Bot | Discord | Post summary messages |

### 3. Configuration

Edit these values in the workflow:

- **Set Date Range** node:
  - `repo`: `owner/repo` (your GitHub repo)
  - `deliveryChannel`: `discord`
  - `language`: `EN` or `ZH`

- **Call OpenRouter API** node:
  - `OPENROUTER_API_KEY`: Your OpenRouter API key (set as workflow secret)

- **Send Summary** (Discord) node:
  - Connect to your Discord webhook/bot

### 4. Schedule

The workflow runs every Friday at 17:00 (Asia/Shanghai timezone). Adjust in the Cron Trigger node.

## Workflow diagram

```
Weekly Cron Trigger → Set Date Range
                    ↘ Fetch Commits ─┐
                    ↘ Fetch Issues ──┼→ Merge Data → Build Prompt → OpenRouter API → Extract Summary → Discord
                    ↘ Fetch PRs ────┘
```

## Output format

```markdown
### Weekly Dev Summary — owner/repo | 6/18/2026

#### This Week in Review

Key accomplishments this week included [summary of themes]...

#### Notable Changes

[Patterns and observations]...

#### Areas Needing Attention

[Warnings or concerns]...
```

## Comparison with competitors

| Feature | Weekly Dev Summary (this PR) | PR #2851 | PR #2861 | PR #2870 |
|---|---|---|---|---|
| Parallel fetch (commits/issues/PRs) | ✅ | ✅ | ✅ | ❌ |
| Free LLM (no API cost) | ✅ (gpt-oss-120b) | ❌ (Claude API) | ❌ (Claude API) | ❌ (Claude API) |
| Discord delivery | ✅ | ❌ (Slack only) | ❌ (Slack only) | ❌ (JSON only) |
| Configurable schedule | ✅ | ✅ | ✅ | ✅ |
| Asia timezone | ✅ | ❌ (ET) | ❌ (ET) | ❌ (ET) |
| README documentation | ✅ | ✅ | ✅ | ❌ |

## Files

```
n8n-weekly-summary/
├── weekly-dev-summary.json          # n8n workflow export
├── README.md                        # this file
└── examples/
    ├── sample_summary.md            # Example output
    └── workflow-diagram.png         # Visual diagram
```

## License

MIT
