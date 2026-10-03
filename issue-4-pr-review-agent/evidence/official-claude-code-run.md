# Official Claude Code end-to-end verification

Date: 2026-10-03

The actual `claude_review.py` CLI was exercised against this real public PR:

`https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4666`

Verification facts:

- GitHub CLI fetched the real PR diff; 305 diff lines were observed.
- Official Claude Code package version: `2.1.288`.
- The complete `claude_review.py --pr ...` command exited `0`.
- The official binary made `POST /v1/messages?beta=true` with user agent `claude-cli/2.1.288 (external, sdk-cli)`.
- The request contained the real PR diff (`diff --git` was present in the Claude prompt).
- Claude Code used streaming mode and the review returned all required Markdown sections.
- The committed output is `samples/official-claude-code-pr4666.md`.

## Evidence boundary

`claude auth status` reported `loggedIn: false` on the verification machine, so this does not claim a live Anthropic model call.

To verify the real Claude Code binary path without using a secret or incurring API spend, `ANTHROPIC_BASE_URL` was pointed to a local deterministic Anthropic-compatible endpoint. The official Claude Code binary still performed the real `-p` request and streaming-response path.

This proves the implementation invokes the official Claude Code binary end-to-end with a real GitHub PR diff. A production model-generated review requires normal Claude Code authentication or an Anthropic API key.
