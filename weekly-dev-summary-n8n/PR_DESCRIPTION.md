## Summary

- add an importable n8n workflow that runs every Friday at 5pm
- fetch weekly GitHub commits, closed issues, and merged PRs
- call Claude Sonnet 4 through the Anthropic Messages API
- post the generated narrative summary to Discord
- document setup in three steps with environment variables

## Tests

- `node -e "JSON.parse(require('fs').readFileSync('weekly-dev-summary-n8n/weekly-dev-summary.workflow.json','utf8')); console.log('workflow json ok')"`
- Imported into n8n and executed successfully: TODO before final PR screenshot

## Notes

The workflow avoids exported credentials by using environment variables for `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, optional `GITHUB_TOKEN`, and repo configuration.
