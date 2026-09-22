# Claude PR review agent

A dependency-free Python CLI that fetches a GitHub PR, invokes a read-only
Claude Code sub-agent or the Anthropic Messages API, validates a structured
response, and renders a predictable Markdown review. Posting is explicit.

## Setup

Requirements: Python 3.11 or newer, an Anthropic API key with model access, and
outbound HTTPS to `api.github.com` and `api.anthropic.com`. The default
`claude-code` backend additionally needs a recent Claude Code CLI supporting
`--bare`, `--agents`, and `--json-schema`. The `anthropic` backend does not need
the Claude CLI. The Python application has no third-party runtime dependencies.

From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install ./agents/pr-review
```

On Windows, activate with `.venv\Scripts\Activate.ps1` instead. Supply secrets
through your shell's environment or secret manager, not command-line arguments
or committed files. Required for both live backends: `ANTHROPIC_API_KEY`.
Optional: `GITHUB_TOKEN`, falling back to `GH_TOKEN`, for authenticated GitHub
reads. A GitHub token is required for `--post`; grant access to the target
repository and the relevant pull-request/comment write permission. Private PRs
also need repository read access. Public reads can run without a GitHub token,
subject to GitHub's unauthenticated rate limit.

The Claude Code backend deliberately uses `--bare`: it does **not** consume
subscription-login credentials, local hooks, plugins, or discovered project
configuration. An Anthropic API key is required even when `claude` is otherwise
logged into a subscription. Normal usage makes billable model requests.

## Usage

```sh
claude-review --pr https://github.com/psf/requests/pull/6731
claude-review --backend anthropic --pr https://github.com/psf/requests/pull/6710
claude-review --backend anthropic --pr https://github.com/OWNER/REPO/pull/123 --output review.md
claude-review --backend anthropic --pr https://github.com/OWNER/REPO/pull/123 --output review.md --post
```

Without `--output`, Markdown goes to stdout. Errors and the posted-comment URL
go to stderr. Output files are replaced atomically with restrictive permissions.
If posting fails, the generated review remains available; the process exits
nonzero. Posting creates a top-level conversation comment, not an approval or
inline review. A second successful `--post` invocation creates another comment;
there is no implicit overwrite or automatic POST retry.

`--model` overrides `CLAUDE_REVIEW_MODEL`; defaults are `sonnet` for Claude Code
and `claude-sonnet-4-6` for the Messages API. Use a model available to your account
that supports tool use. `--timeout` accepts 1–600 seconds per request/process.
GET requests retry a maximum of twice for selected transient errors; the whole
operation can therefore take longer than one timeout. The diff limit defaults
to 150,000 UTF-8 bytes; `--max-diff-bytes` accepts 1,024–1,000,000. Larger diffs
fail unless `--allow-truncation` is supplied, in which case omission is disclosed
and the rendered confidence is always Low. Responses above 2 MB are rejected.

Only HTTPS `github.com/OWNER/REPO/pull/NUMBER` URLs are accepted. Query strings
and anchors are discarded. Enterprise hosts, credentials in URLs, encoded paths,
ports, `/files` suffixes, and unsupported hosts are rejected. A renamed repository
may redirect: use its new canonical URL rather than forwarding credentials.

## Output contract

The output includes the PR URL, exact head/base SHAs, diff digest, and backend
identity, followed by these four sections:

```markdown
## Summary

This changes the connection-selection hook. The public adapter API is updated.

## Risks

- A downstream override may no longer intercept the connection selection.

## Improvement Suggestions

- Add a subclass-dispatch regression test.

## Confidence

Medium
```

The model supplies JSON; Python owns the headings, list rendering, normalized
confidence, and Markdown escaping. Summary items are validated as two or three
complete sentences. Findings may be empty; an explicit non-guarantee placeholder
is then rendered. HTML, Markdown images, additional headings and mention syntax
from model text are neutralized. Confidence is review confidence, not proof that
the PR is safe.

## Native Claude Code agent and GitHub Actions

The repository includes `.claude/agents/pr-reviewer.md`. Open the trusted
repository in Claude Code and ask for `pr-reviewer` with the diff already provided
in the prompt. It has no tools. The standalone CLI dynamically installs the same
review role with a JSON contract and local output validation; it does not rely
on discovering agent files in the repository being reviewed. Direct use of the
Markdown agent alone does not add the CLI's validation or publishing logic.

`workflows/claude-review.yml` is an optional, manually dispatched review workflow.
Copy it to `.github/workflows/claude-review.yml` after the reviewer is installed
on the trusted default branch, and configure the repository secret
`ANTHROPIC_API_KEY`. It restricts reviews to the workflow's own repository and
checks out only the default branch, never the PR head. The default is output-only;
posting requires the explicit dispatch checkbox. Fork PRs are read as data, not
checked out or executed. The separate root CI workflow needs no model secrets.

## Tests and builds

From `agents/pr-review`:

```sh
python -m unittest discover -s tests -v
python -m compileall -q claude_review.py tests scripts
python scripts/reproduce_examples.py --check
python -m pip wheel --no-deps . -w dist
```

For an offline build with setuptools 77+ already installed, add
`--no-build-isolation` to the wheel command.

Optional coverage (development dependency only):

```sh
python -m pip install coverage
python -m coverage run -m unittest discover -s tests
python -m coverage report
```

The suite covers URL/argument validation, hunk accounting and incomplete diffs,
metadata consistency, HTTP failures and retries, schema validation, confidence,
Markdown injection, truncation, both backend adapters, subprocess isolation,
secret redaction, atomic output, stale PRs and posting errors. All automated
tests are offline and use synthetic credentials. No personal credentials or
paid model calls are required. See `VALIDATION.md` for the actual run record.

## Real-PR examples and execution provenance

`examples/pr-review-1.md` reviews Requests #6731 and `examples/pr-review-2.md`
reviews Requests #6710. The complete real diffs and normalized metadata were
retrieved through the connected GitHub tools and are committed with exact SHAs.
The reviews were generated as structured responses by the ChatGPT model after
reading those inputs, then passed through genuine executions of the finished
CLI's recorded-response path. They are **not live Claude responses**. Their
backend labels say so. A matching request SHA-256 binds each response to the
exact prompt, schema, metadata and diff used by the program.

The execution environment had neither an Anthropic API key nor a Claude binary;
its shell could not resolve GitHub. Consequently the Claude backend adapters
and direct HTTP fetch path were validated with mocks, not live API calls. No
paid service run or live comment publication is claimed. A maintainer can use
the normal commands above to perform a live Claude acceptance run; the recorded
examples do not establish that this live acceptance gate passed.

To inspect or reproduce the recorded executions, see `examples/README.md`.
`--export-request request.json` exports a request without invoking a model.
`--snapshot` loads captured metadata/diff; `--response-file` loads an attributed,
request-bound response. All three modes are forbidden with `--post` to prevent
publishing stale or misattributed fixture results.

## Security and limitations

This is diff-only assistance, not a substitute for running project tests or a
human review. No checked-out PR code, tests, links, shell instructions or MCP
servers are executed. The Claude process runs in a temporary directory with
bare configuration, no built-in tools, blocked MCP tools, an empty strict MCP
configuration, no session persistence, and an allowlisted environment that does
not contain the GitHub token. Prompt instructions treat all PR content as
untrusted; this reduces prompt-injection exposure but does not guarantee sound
findings. Metadata is fetched before and after the diff and checked again before
posting. A small race between the final check and the comment POST remains; the
comment records exact reviewed SHAs.

PR title, description and diff are sent to Anthropic during a live review.
Review only repositories you may share with that service. This is not a complete
secret scanner: the configured API key and GitHub token are redacted from rendered
model text, but source secrets already present in a PR may be sent to the model.
Do not use it on sensitive content without appropriate authorization. API error
bodies and raw Claude stderr are suppressed to avoid credential disclosure.
HTTPS proxy and CA environment settings remain trusted operator configuration.

The full diff is checked against GitHub's file/addition/deletion counts. Unsupported
or incomplete diff representations fail closed rather than producing a false
complete review. Binary files have no source content to review. Missing surrounding
files, dependencies, runtime behavior and tests can limit findings. Truncation
limits cost and exposure but can omit the most important changes. The sentence
validator is intentionally conservative; unusual punctuation or abbreviations
may require a fresh model response rather than silently accepting malformed output.

Exit codes: 0 success; 2 usage/input; 3 GitHub or diff failure; 4 credentials/model
transport or process failure; 5 invalid model response; 6 local file I/O; 130
interrupted. A closed stdout pipe exits quietly with 0, as conventional CLI piping
requires. GitHub and model POSTs are not retried automatically because they may
have succeeded despite a lost response.

## References

- Claude Code CLI: https://code.claude.com/docs/en/cli-reference
- Headless/bare mode: https://code.claude.com/docs/en/headless
- Anthropic tool use: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- GitHub pull requests API: https://docs.github.com/en/rest/pulls/pulls
- GitHub issue comments API: https://docs.github.com/en/rest/issues/comments

MIT for this implementation. Requests source fixtures retain their Apache 2.0
license and attribution in `examples/fixtures/`.
