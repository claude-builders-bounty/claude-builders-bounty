# Claude PR Review Agent

Implementation for bounty #4 with both a Claude Code sub-agent and a dependency-free CLI entry point.

## Requirements

- Python 3.9+
- GitHub CLI (`gh`) installed and authenticated
- Claude Code if you want to use the `.claude/agents/pr-reviewer.md` sub-agent directly

## CLI usage

```bash
python claude_review.py --pr https://github.com/owner/repo/pull/123
```

## Claude Code sub-agent

The repository also includes `.claude/agents/pr-reviewer.md`. It instructs Claude Code to inspect PR metadata/diff with `gh` and return the required structured Markdown review.

Both paths use the required output structure:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score (Low / Medium / High)

## Validation

The CLI was syntax-checked with:

```bash
python -m py_compile claude_review.py
```

Deterministic review behavior is covered by unit tests for the required Markdown sections, credential-sensitive changes, execution-surface changes, and large-diff risk detection:

```bash
python test_claude_review.py
```

The CLI was also executed against two real GitHub PRs. Non-empty captured outputs are included in `samples/`:

- `psf/requests#7603`
- `pallets/flask#6133`

No GitHub token is stored or printed; GitHub authentication is delegated to the local `gh` CLI.
