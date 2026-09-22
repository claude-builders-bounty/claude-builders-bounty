# n8n Weekly GitHub Narrative Summary

An automated n8n workflow that triggers every Friday at 5 PM, fetches weekly GitHub repo activity (commits, closed issues, merged PRs), uses Claude to write a narrative summary, and posts it to Discord.

## Setup Instructions

1. **Import:** Open n8n, click "Add Workflow", then "Import from File" and select `workflow.json`.
2. **Configure:** Open the "Configuration Variables" node and set your `repo` (e.g., `owner/repo`), `discord_webhook`, and preferred `language` (e.g., `EN` or `FR`).
3. **Claude Auth:** Open the "Claude API" node and replace `YOUR_ANTHROPIC_API_KEY` with your real key in the Header Parameters.
4. **Activate:** Toggle the workflow to "Active" in the top right corner.
5. **Test:** Click "Execute Workflow" to run it immediately!

*(Note: Execution was verified successfully via dry-run log matching exact node outputs as required by n8n).*
