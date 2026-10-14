# Claude Code PR Reviewer Sub-Agent

Autonomous Pull Request reviewer sub-agent that analyzes PR diffs and outputs structured review comments.

## Acceptance Criteria Verified
- [x] CLI execution: `python claude_review.py --pr https://github.com/owner/repo/pull/123`
- [x] GitHub Action composite definition (`action.yml`).
- [x] Structured Markdown output:
  - Summary of changes (2–3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Verdict (APPROVE / REQUEST_CHANGES / COMMENT)
- [x] Tested on live Pull Requests (`sample_review.md` included).
- [x] Quick setup in 3 steps or fewer.

## Quick Setup (3 Steps)

1. **Install Dependencies**:
   ```bash
   # Standard library only (no external dependencies required)
   python --version
   ```

2. **Run PR Review**:
   ```bash
   python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
   ```

3. **Use in GitHub Actions (Optional)**:
   Add to your workflow:
   ```yaml
   - uses: ./agents/pr-reviewer
     with:
       pr-url: ${{ github.event.pull_request.html_url }}
       github-token: ${{ secrets.GITHUB_TOKEN }}
   ```
