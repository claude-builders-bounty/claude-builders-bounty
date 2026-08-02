# Submission manifest — Claude PR review candidate

Target: `claude-builders-bounty#4` — `$150` PR-review agent.

## Acceptance mapping

- CLI entry point: `claude_review.py --pr <public GitHub PR URL>`.
- Structured output: `## Summary`, `## Risks`, `## Suggestions`, and
  `## Confidence` with `Low`, `Medium`, or `High` validation.
- Two real public PR examples: `samples/masterazul-keyrot-pr-1.md` and
  `samples/flucasf-task-manager-pr-24.md`.
- Setup and usage: `README.md` and `pyproject.toml`.
- Tests: `tests/test_claude_review.py`.

## Reproducible validation

```text
python -m unittest discover -s tests -v
python -m py_compile claude_review.py
```

The optional model-backed path invokes the local `claude` executable in
`plan` permission mode and reads the PR data through public GitHub endpoints.
The deterministic `--offline` path is used for the captured examples and does
not require an API key, repository credentials, or wallet access.

## Submission state (2026-08-02)

The implementation branch is pushed to the owner fork as
`codex/claude-review-bounty` at commit `fdfd362`. The authorized `/opire try`
comment is posted on issue #4 and pull request
[#3662](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/3662)
is open against `claude-builders-bounty:main`; it has no merge conflicts and
currently has no checks configured. No wallet, payment credential, or private
token was used.
