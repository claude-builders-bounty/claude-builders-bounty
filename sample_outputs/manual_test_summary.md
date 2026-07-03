# Manual test summary sample

**Repo:** `claude-builders-bounty/claude-builders-bounty`  
**Language:** EN  
**Delivery:** Slack/Discord webhook payload with `text` field

## Expected generated shape

*Weekly dev summary for claude-builders-bounty/claude-builders-bounty*

This week the repository focused on expanding the bounty board and reviewing contributor submissions. The main shipped work was a set of small automation and documentation utilities proposed through pull requests.

Closed issues and merged PRs should be listed in narrative form when present. If there are no merged PRs or closed issues in the last seven days, the workflow should explicitly say that the week was mostly proposal/review activity.

Notable risks:
- Contributor submissions may need maintainer review for security and usefulness before merge.
- Workflow/API credentials must stay in n8n credentials or environment variables, never committed to the repo.

Suggested next focus:
- Merge the highest-quality bounty submissions.
- Keep bounty acceptance criteria tight so contributors can ship small verified artifacts.
