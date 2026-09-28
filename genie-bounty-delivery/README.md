# PR Review Agent

CLI: `python genie-bounty-delivery/pr_review_agent.py --repo owner/name --pr N`
Alias shape: `claude-review --pr https://github.com/owner/repo/pull/123` → extract repo/PR and call the CLI.

GitHub Action: copy `pr-review-agent.workflow.yml` to `.github/workflows/pr-review-agent.yml` (requires a token with `workflow` scope to push the Action file itself).

Output JSON fields: `summary`, `risks`, `suggestions`, `confidence` (map Low/Medium/High from score).
Sample runs against two real PRs: `sample_review_pr_4574.json` and `sample_review_pr_4576.json`.
