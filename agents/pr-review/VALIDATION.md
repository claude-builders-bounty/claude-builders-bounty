# Execution and acceptance audit

Validation date: 2026-09-22. Local interpreter: CPython 3.13.5 on Linux.
Upstream reviewed: `claude-builders-bounty/claude-builders-bounty`, default branch
`main`, commit `1aeae2adc82d33f971fd7731644348dcdd24b5a6`. Its only tracked files
were README.md and LICENSE; no existing build, lint, type-check or test commands
were present. Both original files are unchanged by this submission.

## Local execution record

- `python -m unittest discover -s tests -v`: 117 tests passed.
- `python -m coverage run -m unittest discover -s tests`: 117 tests passed.
- `python -m coverage report`: 99% line/branch-combined coverage; 459 statements,
  3 missed, 166 branches, 3 partial branches. Coverage threshold is 90%.
- `python -m compileall -q claude_review.py tests scripts`: passed.
- All Python files also parsed successfully with the Python 3.11 AST grammar.
  This is a syntax check, not a claimed execution on Python 3.11 or 3.12.
- `python scripts/reproduce_examples.py --check`: both real-PR examples passed
  exact byte-for-byte regeneration through real CLI subprocess executions.
- Workflow YAML parsed successfully and all external action references were
  verified as full commit-SHA pins. Shell blocks passed `bash -n`.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`: 117 passed.
- `python -m pip wheel --no-build-isolation --no-deps . -w dist`: passed using
  locally installed setuptools 82.0.1; no dependency downloads were needed.
- `setuptools.build_meta.build_wheel` and `build_sdist`: both passed; wheel and
  source archive were produced.
- Fresh virtual environment, wheel installed with `pip install --no-index
  --no-deps`: passed. `claude-review --help` and `--version` passed.
- All 117 tests passed again against the installed wheel, using test files from
  a clean exported repository tree outside the development checkout.
- Both installed `claude-review` console-entry-point executions on the real PR
  snapshots reproduced the checked-in outputs exactly.
- `git diff --cached --check`: passed. Only the reviewer, tests, agent, workflow,
  documentation, attributed source fixtures and ignore rules were staged; no
  credentials, bytecode, build directories or unrelated edits were included.

No existing lint or static type-check configuration was present upstream. The
runtime code is annotated; syntax/compilation checks are not advertised as mypy
or another static type checker. No static type checker or dedicated linter was
installed in this environment. The GitHub CI matrix is supplied for Python 3.11,
3.12 and 3.13 but was not executed here on GitHub Actions.

## Acceptance criteria

| Criterion from issue #4 | Implementation and validation |
| --- | --- |
| `claude-review --pr URL` CLI, or GitHub Action | Installable console entry point; native Claude Code backend and optional Messages API backend; a manually dispatched Action template is included. CLI parsing and backend adapters pass offline tests. Live provider execution remains unverified. |
| Summary in 2–3 sentences | JSON schema requires 2–3 items; local validation requires one complete sentence per item; Python renders one paragraph. Covered by positive and invalid-output tests. |
| Risks list | Fixed `## Risks` section; all findings are escaped list items; explicit placeholder when empty. |
| Improvement suggestions list | Fixed `## Improvement Suggestions` section; all suggestions are escaped list items; explicit placeholder when empty. |
| Confidence Low / Medium / High | Strict normalization, invalid-value rejection, and forced Low for truncated input. |
| Two real PRs and their review outputs | Requests #6731 and #6710, exact metadata/diffs and recorded ChatGPT-generated response JSON; actual CLI replay creates `examples/pr-review-1.md` and `examples/pr-review-2.md`. These are not live Claude executions. |
| README setup and usage | Prerequisites, installation, environment/authentication, examples, output, tests, limits, security and exit codes are documented. |
| Agent returns/posts a structured comment | Native `.claude/agents/pr-reviewer.md`; dynamic tool-less sub-agent in the CLI; explicit `--post` with revision recheck and no automatic POST retry. Mock tests cover success, stale revisions, missing credentials and denied permissions. No comment was actually posted. |

## Real-PR provenance and remaining live gate

See `examples/README.md` and the fixtures for both source PR URLs, head/base SHAs,
full diffs, metadata, model identity and request digests. GitHub data came from
the connected GitHub tool. The shell could not resolve GitHub, so a shell HTTP
fetch is not claimed. The ChatGPT model generated the structured review responses
from those inputs. The finished program rendered them without hand-edited output.

The environment contained neither an Anthropic API key nor a Claude executable.
Both provider interfaces were exercised with mocks, not paid inference. A live
Claude run on the two PRs remains an external acceptance gate; this submission
does not disguise the recorded responses as vendor-generated output or mark
that live gate as passed. Snapshot/recorded-response modes cannot publish comments.

## Repository and submission integrity

The local repository uses the exact verified upstream main commit as a shallow
base. Public README/LICENSE blobs, tree and commit were reconstructed from the
GitHub API and checked against their original Git object IDs because shell clone
was unavailable. This preserves a real upstream parent for the submission patch.
Older history is intentionally outside that shallow checkout.

Claim commenting and upstream branch creation returned HTTP 403. A separate
staging branch in the user's writable repository is used only to preserve the
submission; it is not represented as an upstream fork or accepted bounty PR.
Payment eligibility and acceptance remain decisions of the bounty maintainer.
