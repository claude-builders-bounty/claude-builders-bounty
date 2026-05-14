# Test notes — n8n + Claude weekly dev summary

## Local validation

```bash
python3 scripts/validate_workflow.py workflows/weekly-dev-summary-claude.json
```

Expected:

```text
workflow ok: workflows/weekly-dev-summary-claude.json (12 nodes)
```

## Manual n8n test plan

1. Import `workflows/weekly-dev-summary-claude.json` into n8n.
2. Configure environment variables:
   - `GITHUB_REPO`
   - `GITHUB_TOKEN`
   - `ANTHROPIC_API_KEY`
   - `DISCORD_WEBHOOK_URL`
   - `SUMMARY_LANGUAGE`
3. Run the workflow manually.
4. Confirm nodes execute in order:
   - Weekly Friday 5pm
   - Config
   - GitHub Commits
   - GitHub Closed Issues
   - GitHub Merged PRs
   - Merge Commits + Issues
   - Merge With PRs
   - Build Claude Prompt
   - Claude Summary
   - Format Discord Message
   - Send Discord Webhook
5. Capture screenshot of successful execution and place it in `screenshots/n8n-successful-execution.png`.

## Notes

The workflow is designed to be credential-light for import:

- GitHub and Anthropic calls use environment variables in HTTP headers.
- Discord uses a webhook URL environment variable.
- Language can be switched with `SUMMARY_LANGUAGE=EN` or `SUMMARY_LANGUAGE=FR` without editing nodes.
