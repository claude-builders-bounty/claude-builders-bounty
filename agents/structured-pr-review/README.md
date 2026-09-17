# Evidence-grounded Claude Code PR reviewer

Fetch a real GitHub pull request, pin its head revision, review all supplied
textual hunks, and print a Markdown comment with Summary, Identified risks,
Improvement suggestions and Confidence. Nothing is posted automatically and no
code from the reviewed repository is checked out or executed.

## Setup and run

1. Install Python 3.10+, GitHub CLI and Claude Code. Authenticate `gh` and Claude
   with accounts permitted to access the chosen repository/provider.
2. Put this directory on PATH and make `claude-review` executable, or invoke its
   absolute path with Bash.
3. Run:

```sh
claude-review --pr https://github.com/OWNER/REPO/pull/123 \
  --evidence-dir ./new-review
```

The default profile is native Claude Code with `--model opus`, the profile used
for current quality validation. The model is configurable, not pinned forever
to a vendor alias. The recorded validation provider resolved it to Claude Opus 5.
Use `--timeout`, `--max-diff-bytes`, and `--max-budget-usd` for explicit limits.
The $1 default budget is divided among possible model calls; raising that limit
is not a purchase. Actual account billing/plan rules are controlled by the provider.
`--collect-only` fetches evidence without calling a model.

For optional local experimentation:

```sh
claude-review --pr https://github.com/OWNER/REPO/pull/123 \
  --backend ollama --model qwen3.5:4b --evidence-dir ./local-experiment
```

That uses the real local Ollama API, **not** Claude Code or Anthropic inference.
The tested small local models did not meet the review-quality bar. Their successful
HTTP/JSON responses must not be mistaken for accurate reviews. The local endpoint
is loopback-only in this implementation; it does not load or modify account keys.

## What prevents the observed false findings

- Each candidate cites exact, full source lines with stable before/after reference
  IDs. A quote fragment that hides part of an expression is rejected.
- A separate audit checks the description, concrete scenario, proposed fix and
  whether the failure was introduced. All four must pass, not just the general idea.
- Complete Python functions visible in the diff are parsed with `ast`, never
  executed. Syntactic return facts distinguish a tuple from its individual members.
  A narrowly defined whole-return claim quoting only a tuple member is rejected.
- Removed guards can cause faults on unchanged lines. Such candidates are kept for
  a causal audit rather than automatically discarded for citing an unchanged line.
- Documented intentional changes, invented compatibility promises, unsupported
  missing-test claims, praise and cosmetic preferences are not actionable defects.
- Confidence is capped at Medium (Low when source/context is incomplete). Neither
  source matching nor agreement between model passes is a calibrated accuracy score.

This addresses observed failure modes. It cannot prove arbitrary model prose true.
A person should review the resulting comment before posting or relying on it.

## Coverage, limits and retained evidence

All changed-file pages are fetched. An incomplete count, duplicate file, changed
head, oversized total diff or malformed response stops the run with an explicit
error. Missing binary/text patches are recorded as limitations. Hunk partitioning
retains every source line; oversized hunks are split into labelled context-limited
fragments rather than silently truncated. `PR_REVIEW_CHUNK_CHARS` controls the
per-group source-record size. No whole-repository reasoning is claimed.

A requested evidence directory must be new. It contains the pinned input, raw
candidates, exact source quotes, independent audit decisions, excluded claims,
rendered review, hashes and provider metadata. Failure saves input and diagnostics
rather than manufacturing an empty successful review. Diagnostics may identify an
account or include private diff text: review them before publishing.

Native Claude runs in an empty temporary directory with no tools, MCP servers,
project/user settings or hooks and no persisted review session. Normal account
credentials are not rewritten by the review command. For a private PR, its diff
is sent to the chosen provider; use only an authorized provider for that material.

## Verification

```sh
python3 -B -m unittest discover -s tests -v
```

Current deterministic tests cover parsing, pagination, stable revisions, quote
matching, atomic audit decisions, AST facts, actual hook-free subprocess flags,
positive defect retention, failure evidence, and the default native model profile.

`validation/current/` contains the dated live native CLI runs and quality report.
`SAMPLE-QUALITY.md` retains the earlier inaccurate local-model samples and records
which changes address them. Earlier samples are historical failures, not current
recommended comments. No generated review was posted to the sample upstream PRs.

Official interfaces: https://code.claude.com/docs/en/cli-reference and
https://code.claude.com/docs/en/sub-agents .
