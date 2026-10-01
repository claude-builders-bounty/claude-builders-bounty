# claude-review

Review a GitHub pull request with Claude Code and optionally post structured Markdown.

## Setup
1. Install Python 3.9+, GitHub CLI and Claude Code v2.1.248+ with support for restricted mode. Authenticate gh and Claude Code with your own account; do not commit tokens.
2. Run `chmod +x claude-review/claude_review.py`, then add a symlink named `claude-review` in a user-owned directory on PATH pointing to this script. Alternatively use `python3 claude-review/claude_review.py` directly.
3. Run `claude-review --pr https://github.com/owner/repo/pull/123`. Add `--output review.md` to save or `--post` to publish.

Generation sends the PR title and diff to the configured Claude provider and may incur its normal charges. Ensure you are authorized to share the target repository content with that provider.

## Output and safety
The output has Summary (2-3 sentences), Identified Risks (bullets), Improvement Suggestions (bullets), and Confidence Score (Low/Medium/High with a justification). Missing, empty, reordered or invalid sections cause failure before posting. Sentence detection is intentionally simple; unusual punctuation may require another generation.

PR URLs must be exact HTTPS GitHub PR URLs. The tool checks the head commit before/after fetching the diff and again before publishing. A changed head requires rerunning. Empty diffs and diffs larger than 200 KB fail explicitly; they are not silently truncated.

The model receives the diff as untrusted JSON via stdin. It runs with restricted mode, no built-in tools, no MCP tools and no session persistence. Permission bypass flags are never used. Unsupported Claude versions fail; there is no less-restricted fallback. See the [official CLI reference](https://code.claude.com/docs/en/cli-reference).

Publication uses gh --body-file - with validated text on stdin. No comment is posted without --post. Each explicit successful --post run creates one comment; avoid repeating it merely to check delivery. Inspect the PR before retrying after a timeout, since a network response can be lost after a successful post.

## Tests
```bash
python3 -m unittest discover -s claude-review -p test_claude_review.py -v
```
Nine regression tests passed: exact URLs, required output structure, stdin transport/tool restrictions, oversized input rejection, default no-post, explicit posting, malformed-output rejection, stale-head rejection and validation at the posting boundary. External calls are mocked; this does not claim a live Claude/gh integration run.

## Two existing real-PR samples
- samples/sample-output-1.md: PR #4464 at d347e4e9ee00a0695ad50b14840239aa71c416f1.
- samples/sample-output-2.md: PR #4547 at 17fca49bdc99d1e30de4dbb3b730950895cf2115.

These are historical outputs already present before this repair, attributed to NEXORA's Claude Code runtime. They are not newly generated runs of this revised CLI. They describe the old diffs (including the formerly unrelated Family Guard files) and must not be presented as a review of the corrected heads. The sample's workflow-deployment claim is model commentary, not independently verified workflow behavior.

To complete integration acceptance, run this CLI on two real PRs without --post, save their URL/head SHA, CLI version, exact command, date and output, then inspect the results. A public comment test needs authorization for its destination. This environment had no authenticated local Claude CLI and denied child-process creation, so the updated CLI's live integration check remains pending.
