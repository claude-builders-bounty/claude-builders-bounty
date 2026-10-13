# Claude Code PR Review Subagent

A **read-only** PR-review CLI and a dedicated Claude Code subagent (`.claude/agents/pr-reviewer.md`). Implements the GitHub Bounty [#4: PR Review Agent — $150](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4).

## Requirements

- Python 3.10 or newer (standard library only).
- GitHub CLI [`gh`](https://cli.github.com/) installed and authenticated (`gh auth login`) for PR diff retrieval. Public PRs may work without an authenticated session depending on the CLI setup.
- Claude Code CLI installed and authenticated; model invocation may incur usage charges under your own subscription/provider plan.

## Install

From this folder, run:

```bash
python3 -m pip install -e .
```

The editable install keeps the project-local `.claude/agents/pr-reviewer.md` available to Claude Code. It exposes the required `claude-review` command.

## Run

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

Save a review:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

Analyze a previously saved GitHub PR diff:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --diff-file ./changes.diff
```

The CLI prints a Markdown review containing a 2–3 sentence **Summary**, bullet-listed **Risks**, bullet-listed **Suggestions**, and **Confidence: Low/Medium/High**. It refuses malformed output instead of presenting it as a completed review. It does **not** post comments without explicit permission.

## Test

```bash
python3 -m unittest discover -s tests -v
```

The tests mock the external `gh` and `claude` commands and do not establish that Claude was contacted or that real GitHub PRs were reviewed. To meet the bounty's final acceptance criterion, run the CLI on **two real public GitHub PR URLs**, save the two Markdown outputs, then include them in the actual submitted PR. These outputs are **not yet included**.

## Security

- Validates the exact GitHub PR URL format to reduce accidental or malicious URL handling.
- Calls `gh` and `claude` with argument arrays, never `shell=True`.
- Makes no write requests to GitHub and performs no checkout/build/execution of PR code.
- Restricts the model toolset and explicitly labels the diff as untrusted data.
- Caps diff size to 125,000 UTF-8 bytes, rejects invalid/empty results, and sets subprocess timeouts.
- A malicious diff may still influence a model's text output; review generated recommendations before acting on them.

## Submission note

Bounty status on GitHub may differ from payment status on Opire. The source issue describes automatic payment on merge, but [Opire's current documentation](https://docs.opire.dev/rewards/pricing) says the sponsor must arrange payment after acceptance. Seek sponsor confirmation of available funds and payout conditions **before relying on an award**. No payout or real model invocation is claimed in this package. A draft pull request can be opened before the required two live reviews are added.
