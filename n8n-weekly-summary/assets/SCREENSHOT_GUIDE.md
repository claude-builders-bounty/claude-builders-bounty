# Screenshot in 2 minutes (real n8n, no creds needed for the shot)

The bounty asks for a screenshot on a real n8n instance. This repo validates everything offline (`python test_workflow.py`), so the screenshot is the only manual step.

1. Open your n8n (cloud trial or `docker run -p 5678:5678 n8nio/n8n`) → Workflows → Import from file → choose `workflow.json` (30s).
2. Zoom out so all nodes + the `Sticky Note - Setup Guide` are visible; press Execute Workflow (it will fail on fake webhook — that is fine, green/grey nodes still show) and screenshot the canvas (30s).
3. Save as `assets/screenshot.png` and keep this file — reviewers see the exact reproduce path (60s).

What the shot must show: `Weekly Schedule - Fri 5pm` → `Config (Edit Me)` → `Compute Week Window` → 3 fetch nodes → merges → `Build Claude Prompt (EN/FR)` → `Claude Summary (sonnet-4)` → `Has Activity?` → `Discord Notify`.
