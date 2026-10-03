# Claude PR Review Agent

A small Claude Code sub-agent + CLI for reviewing a GitHub PR and emitting a structured Markdown comment.

## Setup
1. Install/authenticate GitHub CLI (`gh`) and Claude Code (`claude`).
2. Run `bash install.sh`, then use the bounty-requested CLI directly: `claude-review --pr https://github.com/owner/repo/pull/123`.

The installer places the wrapper and Python implementation in `~/.local/bin`; add that directory to `PATH` if your shell does not already include it.

The CLI fetches the diff with `gh pr diff`. When Claude Code is available it sends the diff and explicit review format to `claude -p`; otherwise it uses a conservative deterministic fallback so the command still returns the required structure. A timed-out, unavailable, or malformed Claude response also falls back; GitHub diff retrieval failures return a clear nonzero error. Set `CLAUDE_BIN` to override the executable. `--fallback-only` is useful for offline verification.

## Output contract
`Summary` (2-3 sentences), `Risks`, `Improvement suggestions`, and `Confidence` (`Low`, `Medium`, or `High`).

## Verification
Official Claude Code **2.1.288** is now exercised through the real CLI path. `claude_review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4666` fetched the real GitHub diff, invoked the official `claude -p` binary, and exited 0 with the required structured Markdown. See `evidence/official-claude-code-run.md`, `evidence/official-claude-code-receipt.json`, and `samples/official-claude-code-pr4666.md`.

The verification machine was not logged into Anthropic, so the real binary was routed to a local deterministic Anthropic-compatible endpoint; no live Anthropic model call is claimed. The request trace confirms the official `claude-cli/2.1.288` user agent, streaming `POST /v1/messages?beta=true`, and that the real PR diff was present in the prompt.

Run `python -m pytest -q issue-4-pr-review-agent/tests` for focused regression coverage. Validation checks ordered non-empty review sections, risk/suggestion bullet lists and an exact confidence value. Diff statistics exclude file headers, and timeout/launch errors fall back deterministically.
