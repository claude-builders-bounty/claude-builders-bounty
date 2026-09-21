# n8n + Claude — Weekly GitHub Narrative

Importable n8n workflow for Issue #5. Every Friday at 5:00 PM (`America/New_York`) it reads the preceding seven-day window from GitHub, keeps actual closed issues and actually merged PRs distinct, asks `claude-sonnet-4-20250514` for an EN/FR narrative, verifies that Claude returned text, and delivers it to Discord.

## Setup (5 steps)

1. Set n8n environment variables: `GITHUB_OWNER`, `GITHUB_REPO`, `LANGUAGE` (`EN` or `FR`), `ANTHROPIC_API_KEY`, and `DESTINATION_WEBHOOK_URL` (a Discord incoming webhook). Optional test overrides are `GITHUB_API_BASE` and `ANTHROPIC_BASE_URL`.
2. Allow workflow expressions to read those variables (self-hosted n8n: `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`), then restart n8n.
3. Import `n8n-workflow.json` with **Import from File**.
4. Run **Manual Test Trigger** once; confirm all three GitHub branches, **Generate with Claude**, **Verify Claude Response**, and **Deliver to Discord** are green, then inspect the delivered message.
5. Activate the workflow. The independent **Friday 5 PM** trigger now runs weekly.

## Behavior and safety

- GitHub calls request commits with `since`/`until`, closed issues updated since the window start, and closed PRs sorted by update time. Normalizers keep issue and commit timestamps inside the same seven-day window, exclude issue API rows that are really PRs, and retain only PRs whose `merged_at` is inside the window.
- Empty GitHub arrays and n8n's `alwaysOutputData` sentinel items are normalized to empty lists; a no-activity week is never represented by a fabricated blank commit.
- The prompt contains normalized JSON, asks Claude not to invent activity, and supports English or French.
- Missing Claude text throws an error instead of reporting success. An empty destination also ends in an explicit failed execution; generated-but-undelivered is not success.
- API keys are environment references only; no secret is embedded in the export or evidence.
- GitHub's unauthenticated API limit and the 100-row weekly cap are deliberate bounded defaults. For a repository exceeding 100 weekly rows, add authenticated GitHub pagination before activation rather than silently treating a partial week as complete.

## Real-runtime evidence

`evidence/REAL_N8N_EXECUTION.md` records the exact n8n version, execution command, test boundaries, and artifact hashes. `evidence/n8n-successful-execution.png` is the corresponding successful execution screenshot. The run uses the real imported n8n workflow, live public GitHub API data, and local deterministic Claude/Discord test doubles so no production key or external channel is exposed.

## Local regression validation

```bash
python3 tests/validate_workflow.py
```

This validates import structure, graph wiring, schedule/model/configuration, weekly filters, and fail-closed delivery/Claude checks. It is regression coverage, not a substitute for the real n8n execution evidence above.
