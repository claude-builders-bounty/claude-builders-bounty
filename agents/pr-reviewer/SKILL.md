# Claude Code PR Review Agent

Use this agent when asked to review a GitHub pull request and return a structured Markdown comment.

## Workflow

1. Install the CLI from this directory if `claude-review` is not already available:

```bash
python -m pip install -e agents/pr-reviewer
```

2. Review a PR URL:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

The shorthand `owner/repo#123` is also accepted.

3. If a local checkout is available, include `--repo-root` so changed symbols can be checked against downstream callers outside the PR diff:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --repo-root /path/to/checkout
```

4. If the user wants Claude or another LLM to write the review text, use an external command that accepts the generated prompt on stdin and returns JSON:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --llm-command "claude -p"
```

Use `--prompt-only` when you need to inspect or hand off the exact prompt without calling the model.

Use `--format sarif --output claude-review.sarif` when the caller wants code-scanning style output. Use `--config .claude-review.yml` when a repository has rule suppressions, ignored paths, or severity overrides.

5. If the user wants a GitHub comment posted, use:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --update-comment
```

`--update-comment` adds a hidden marker and edits the prior generated review when one exists, which avoids repeated comments on every PR update.

In GitHub Actions, prefer the more durable form:

```bash
claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --repo-root "$GITHUB_WORKSPACE" \
  --github-annotations \
  --step-summary \
  --allow-comment-failure \
  --update-comment
```

This leaves file/line annotations and a step summary even when fork PR token permissions prevent writing a PR comment.

When this package is committed to a repository, it can also be used as a local composite action with `uses: ./agents/pr-reviewer`.

## Output Contract

The review must keep these sections:

- `### Summary`
- `### Identified Risks`
- `### Improvement Suggestions`
- `### Confidence Score`

The summary should be 2-3 sentences. Confidence must be exactly `Low`, `Medium`, or `High`. Deterministic risk bullets should preserve `[Severity][RULE_CODE] path:line` when a location is available. Dependency and coverage-relevance findings use codes such as `DEPENDENT_USAGE_UNTESTED`, `DEPENDENT_USAGE_CHANGED`, `DEPENDENT_USAGE_OUTSIDE_DIFF`, and `CHANGED_SYMBOL_WITHOUT_RELEVANT_TEST`. GitHub annotations should only be emitted for findings with a concrete file path.

## Notes

This reviewer is deterministic and can run offline with `--diff-file`. The `--llm-command` path is optional and still validates the response schema before output. A human reviewer or a deeper Claude Code session should still inspect high-risk changes before merge.
