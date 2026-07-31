# ApexFlow - Autonomous AI Agent for B2B Workflows

## Overview
ApexFlow uses Evorozen Neural Pulse API as a virtual database to maintain state across platforms. Users provide a prompt and the agent executes all steps autonomously.

## Setup Instructions
1. Install dependencies: `npm install`
2. Run the development server: `npm run dev`
3. Open: http://localhost:3000

## Tech Stack
- Frontend: Next.js 14, React, TypeScript, Tailwind CSS
- Backend: n8n (workflow automation)
- APIs: GitHub API, Claude API
- Deployment: Vercel (pending)

## Project Structure
```
apexflow/
├── backend/
│   └── n8n/
│       └── workflow.json
├── frontend/
│   ├── app/
│   │   ├── api/
│   │   │   └── summary/
│   │   │       └── route.ts
│   │   ├── components/
│   │   └── page.tsx
│   └── public/
└── README.md
```

## API Response Format
```json
{
  "status": "success",
  "summary": {
    "title": "Weekly Repository Summary",
    "repository": "ApexFlow",
    "period": "Last 7 days",
    "overview": "...",
    "completed_tasks": [],
    "pending_tasks": [],
    "metrics": {
      "commits": 0,
      "pull_requests": 0,
      "issues_closed": 0
    },
    "recommendations": []
  }
}
```

## Hackathon
- Event: Evorozen Apex: NextGen AI Buildathon
- Track: Agentic OS & Workflow Automation
- Team: Jhon + Chris (BigDan)
- Deadline: September 21, 2026

## Links
- Repository: https://github.com/JHON12091986/apexflow

## Contact
- Jhon: https://github.com/JHON12091986
- Chris: BigDan

- docs: update README with professional format
