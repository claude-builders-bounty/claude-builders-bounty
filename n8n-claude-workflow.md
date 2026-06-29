# n8n + Claude Workflow for "100 Nocode SaaS Ideas"

This document describes a production-ready n8n workflow that combines Claude AI with web scraping to research SaaS ideas and generate structured product requirement documents.

## Prerequisites

- **n8n** (self-hosted or cloud): `https://n8n.io/`
- **Anthropic API key**: Get from https://console.anthropic.com
- **Target URL**: A page listing SaaS ideas (e.g., a blog post, GitHub repo, or curated list)

## Workflow Architecture

```
+------------+     +-------------+     +-------------+     +-------------+
| Schedule   | --> | HTTP Request| --> | Claude AI   | --> | Spreadsheet |
| Trigger    |     | (Scrape)    |     | (Generate   |     | (Save)      |
| (Daily)    |     |             |     |  PRD)       |     |             |
+------------+     +-------------+     +-------------+     +-------------+
                          |                   |
                          v                   v
                    +-------------+     +-------------+
                    | HTML Parse  |     | Slack/Email |
                    | (Extract)   |     | (Notify)    |
                    +-------------+     +-------------+
```

## Step-by-Step Setup

### Step 1: Create the Workflow

1. Open your n8n instance
2. Click **"Add Workflow"**
3. Name it: `100-Nocode-SaaS-Ideas`

### Step 2: Schedule Trigger Node

```
Node: Schedule Trigger
Settings:
  - Trigger Interval: Every Day
  - Time: 09:00 (your timezone)
```

This runs the workflow daily at 9 AM.

### Step 3: HTTP Request Node (Scrape)

```
Node: HTTP Request
Settings:
  - Method: GET
  - URL: https://example.com/saas-ideas-list
  - Options:
    - Response Format: String
    - Headers:
      User-Agent: Mozilla/5.0 (compatible; N8N-Scraper/1.0)
```

**Node JSON** (import via n8n UI):
```json
{
  "nodes": [
    {
      "parameters": {
        "method": "GET",
        "url": "https://example.com/saas-ideas-list",
        "options": {
          "response": {
            "response": {
              "responseFormat": "string"
            }
          }
        }
      },
      "name": "Scrape Ideas Page",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1
    }
  ]
}
```

### Step 4: HTML Extract Node (Parse)

Extract individual idea titles and descriptions from the HTML:

```
Node: HTML
Settings:
  - Operation: Extract HTML Content
  - Data Property Name: data
  - Extraction Values:
    - Key: ideas
    - CSS Selector: article.idea, div.idea-card, li.idea (adjust to target site)
    - Return Value: HTML
    - Get Multiple Results: true
```

### Step 5: Claude AI Node (Generate PRD)

```
Node: Anthropic Chat Model
Settings:
  - Model: claude-sonnet-4-20250514
  - Credentials: Your Anthropic API key
  - Options:
    - Max Tokens: 4096
    - Temperature: 0.7
```

**System Prompt:**
```
You are an expert product manager and technical architect. Your task is to take a raw SaaS idea and generate a comprehensive Product Requirements Document (PRD) in structured Markdown format.

For each idea, generate:
1. **Product Name** - A catchy, marketable name
2. **One-liner** - The core value proposition in one sentence
3. **Target Audience** - Who this product serves
4. **Core Features** (5-7 bullet points)
5. **Tech Stack Recommendation** - Frontend, backend, database, hosting
6. **Monetization Strategy** - Pricing model suggestions
7. **MVP Scope** - What to build first (2-week sprint)
8. **Competitive Advantage** - What makes this unique

Keep responses structured and actionable. No fluff.
```

**User Message Template:**
```
Generate a PRD for this SaaS idea:

Idea Title: {{ $json.title }}
Description: {{ $json.description }}

Output the PRD in Markdown format.
```

### Step 6: Spreadsheet Save (Google Sheets)

```
Node: Google Sheets
Settings:
  - Operation: Append
  - Document: "100-Nocode-SaaS-PRDs"
  - Sheet: "Generated PRDs"
  - Columns Mapping:
    - A: Date ({{ $now.format('YYYY-MM-DD') }})
    - B: Idea Title ({{ $json.title }})
    - C: PRD Content ({{ $json.content }})
    - D: Product Name (extracted from PRD)
    - E: Tech Stack (extracted from PRD)
```

### Step 7: Notification (Slack/Email)

```
Node: Slack
Settings:
  - Operation: Post
  - Channel: #product-ideas
  - Message: "New SaaS PRD generated: {{ $json.productName }}"
  - Attachments: Link to Google Sheet row
```

## Full Workflow JSON (Importable)

Save this as `workflow.json` and import into n8n:

```json
{
  "name": "100-Nocode-SaaS-Ideas",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [{ "triggerAtHour": 9 }]
        }
      },
      "id": "trigger",
      "name": "Daily Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1.1,
      "position": [200, 300]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "https://example.com/saas-ideas",
        "options": { "response": { "responseFormat": "string" } }
      },
      "id": "scrape",
      "name": "Scrape Ideas",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [400, 300]
    },
    {
      "parameters": {
        "operation": "extractHtmlContent",
        "dataPropertyName": "data",
        "extractionValues": {
          "values": [
            {
              "key": "title",
              "cssSelector": "h2, h3",
              "returnValue": "text"
            },
            {
              "key": "description",
              "cssSelector": "p",
              "returnValue": "text"
            }
          ]
        }
      },
      "id": "parse",
      "name": "Parse HTML",
      "type": "n8n-nodes-base.html",
      "typeVersion": 1,
      "position": [600, 300]
    },
    {
      "parameters": {
        "model": "claude-sonnet-4-20250514",
        "options": { "maxTokens": 4096, "temperature": 0.7 }
      },
      "id": "claude",
      "name": "Claude PRD Generator",
      "type": "@n8n/n8n-nodes-langchain.lmChatAnthropic",
      "typeVersion": 1,
      "position": [800, 300]
    },
    {
      "parameters": {
        "operation": "append",
        "documentId": { "__rl": true, "value": "YOUR_SHEET_ID", "mode": "id" },
        "sheetName": { "__rl": true, "value": "={{ $now.format('YYYY-MM') }}", "mode": "name" }
      },
      "id": "sheets",
      "name": "Save to Sheets",
      "type": "n8n-nodes-base.googleSheets",
      "typeVersion": 4.2,
      "position": [1000, 300]
    }
  ],
  "connections": {
    "Daily Trigger": { "main": [[{ "node": "Scrape Ideas", "type": "main", "index": 0 }]] },
    "Scrape Ideas": { "main": [[{ "node": "Parse HTML", "type": "main", "index": 0 }]] },
    "Parse HTML": { "main": [[{ "node": "Claude PRD Generator", "type": "main", "index": 0 }]] },
    "Claude PRD Generator": { "main": [[{ "node": "Save to Sheets", "type": "main", "index": 0 }]] }
  }
}
```

## Configuration Checklist

- [ ] Replace `https://example.com/saas-ideas` with your actual target URL
- [ ] Add Anthropic API credentials in n8n
- [ ] Connect Google Sheets account and set document ID
- [ ] Adjust CSS selectors in HTML node to match target page structure
- [ ] Configure Slack webhook (optional)
- [ ] Test with "Execute Workflow" before enabling schedule

## Cost Estimation

| Component | Cost |
|-----------|------|
| n8n (self-hosted) | Free (server cost only) |
| Claude API | ~$0.008 per PRD (Sonnet 4-20250514) |
| Google Sheets | Free |
| **Total per 100 ideas** | **~$0.80** |

## Output Example

For each run, the workflow appends to Google Sheets:

| Date | Idea Title | PRD Content | Product Name | Tech Stack |
|------|-----------|-------------|--------------|------------|
| 2026-06-29 | AI Meal Planner | [Full PRD markdown] | NutriGenius | Next.js, OpenAI, PostgreSQL |
