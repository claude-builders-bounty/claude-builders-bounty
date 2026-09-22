# Add a validated Claude Code PR-review agent and reproducible examples

Addresses claude-builders-bounty/claude-builders-bounty#4.

## Implementation

Adds an isolated Python package under `agents/pr-review`, the native
`.claude/agents/pr-reviewer.md` agent, an installable `claude-review --pr URL`
entry point, and an optional manually dispatched GitHub Action. The CLI supports
an isolated Claude Code sub-agent and the Anthropic Messages API. It validates
GitHub URLs, verifies diff completeness and revision consistency, obtains a
schema-constrained model response, and renders fixed Markdown sections.
Explicit `--post` publishes a top-level PR comment after rechecking revisions.

The runtime has no third-party Python dependencies. Transport limits, finite
timeouts, read-only retries, safe error messages, environment isolation,
Markdown escaping, output redaction and atomic file writes are covered by tests.
No PR code is executed. Existing upstream README.md and LICENSE remain unchanged.

## Run

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install ./agents/pr-review
# Supply ANTHROPIC_API_KEY through the environment/secret manager.
claude-review --backend anthropic --pr https://github.com/psf/requests/pull/6731
```

The default backend uses a recent Claude Code CLI in `--bare` mode; this also
requires `ANTHROPIC_API_KEY` rather than subscription-login credentials. A GitHub
token is optional for public reads and required for `--post`. Setup, native-agent
usage, workflow installation, output structure, security and limits are covered
in `agents/pr-review/README.md`.

## Validation performed

From `agents/pr-review`:

- `python -m unittest discover -s tests -v`: 117 passed.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`: 117 passed.
- `python -m coverage run -m unittest discover -s tests` and
  `python -m coverage report`: passed, 99% coverage.
- `python -m compileall -q claude_review.py tests scripts`: passed.
- `python scripts/reproduce_examples.py --check`: two exact reproductions.
- `python -m pip wheel --no-build-isolation --no-deps . -w dist`: passed.
- Wheel and source distribution built; wheel installed into a fresh virtual
  environment; all 117 tests and both installed-console examples passed again.
- Workflow YAML parsing, shell syntax and Python 3.11 grammar checks: passed.
- `git diff --cached --check`: passed; final source/secret/unrelated-file audit completed.

Local execution used Python 3.13.5. The supplied GitHub Actions matrix has not
been run, and no uninstalled static type checker or linter is claimed.

## Two real pull requests and outputs

1. https://github.com/psf/requests/pull/6731 — head
   `da96a92e2eb6dfe7c74704267bcb8f9fd6fb92b0`; output
   `agents/pr-review/examples/pr-review-1.md`.
2. https://github.com/psf/requests/pull/6710 — head
   `92075b330a30b9883f466a43d3f7566ab849f91b`; output
   `agents/pr-review/examples/pr-review-2.md`.

Important execution boundary: complete real metadata and diffs were fetched
through the GitHub connector. ChatGPT generated attributed structured responses
from those inputs; actual executions of the finished CLI's recorded-response
path validated and rendered the committed Markdown. Neither output is presented
as a live Claude response. Both files prominently identify the recorded backend.
Exact source snapshots, request-bound response JSON and reproduction commands
are included. No review was posted to the Requests repository.

This environment had no Anthropic credentials or Claude executable and no shell
DNS access to GitHub. Live provider inference and direct HTTP fetching were
therefore tested with mocks, not a paid live end-to-end run. A live Claude run
on the two PRs remains an acceptance gate, not a completed claim.

## Bounty acceptance mapping

- CLI or Action: console command implemented and exercised; manual Action YAML
  included; native Claude Code agent supplied. Live provider run remains unverified.
- Summary: two or three complete sentences, schema and local validation tested.
- Risks: deterministic Markdown list with safe rendering.
- Improvements: deterministic Markdown list with safe rendering.
- Confidence: strict Low/Medium/High, normalized case, Low forced for partial input.
- Two real PRs: source snapshots and genuinely executed recorded-response outputs
  included, with the live-Claude limitation stated above.
- README: prerequisites, installation, authentication, usage, examples, output,
  tests, security, limitations and exit codes included.
- Posting: opt-in implementation with mocked success/failure/revision tests;
  no live posting permission or publication is claimed.

The required `/opire try` claim comment could not be posted by the connected
integration (HTTP 403) and remains a manual claim step. Payment is not assumed;
acceptance and payout depend on the maintainer's review and merge.
