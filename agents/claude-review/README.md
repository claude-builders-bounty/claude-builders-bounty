# claude-review

Dependency-free Python CLI that reads GitHub PR patches and produces a structured Markdown review draft. The default engine uses **offline heuristics**, not Claude or another LLM. It never posts comments or writes to GitHub.

## Setup

Requires Python 3.9+; no pip or npm installation is needed. Keep `claude-review` alongside `reviewer/`:

```bash
chmod +x claude-review
./claude-review --help
# Optional, while in this directory:
export PATH="$PWD:$PATH"
claude-review --pr https://github.com/psf/requests/pull/7128
```

The equivalent module command is `python3 -m reviewer --pr URL` from the project directory. Moving only the executable is insufficient; it imports the neighboring package.

## Usage

```bash
./claude-review --pr https://github.com/psf/requests/pull/7128
./claude-review --pr https://github.com/psf/requests/pull/7128 --out review.md
python3 -m unittest discover -s tests -v
```

`--out` writes UTF-8 Markdown and stdout still receives the full review. The output parent directory must exist. Errors go to stderr and exit with status 1; argument errors exit with status 2.

Public PRs work without a token where GitHub API/network access is available. An optional `GITHUB_TOKEN` environment variable is read only at runtime and attached only to requests to `api.github.com`; it can increase the API quota and enable authorized repository access. The application does not read credential files, log the token, or follow API redirects. Set the variable in your own shell or CI secret configuration. No token was inspected or used for the local CLI verification in this delivery.

Live fetching reads PR metadata and paginated `/files` patches (up to GitHub's 3,000-file cap). A second metadata read rejects a changed head/base SHA during fetching. The tool limits each response and replay snapshot to 8 MiB. Omitted patches, metadata count mismatches, and large diffs produce Low confidence rather than being presented as complete reviews.

## Real PR samples and repeatable commands

Python's outbound network access is blocked in the delivery sandbox. The two public PRs below were retrieved through the read-only GitHub connector (`fetch` metadata and `fetch_pr_patch` patches), saved with base/head SHAs, and **actually run through this CLI** using `--snapshot`. These are real per-file unified patches, not invented fixtures. The live Python HTTP path was unit-tested with mocked responses, but was not successfully exercised against GitHub here.

```bash
./claude-review --pr https://github.com/psf/requests/pull/6767 --snapshot sample-outputs/evidence/pr-1.json
./claude-review --pr https://github.com/psf/requests/pull/7128 --snapshot sample-outputs/evidence/pr-2.json
```

- [PR 6767](https://github.com/psf/requests/pull/6767): Revert caching a default SSLContext; [full output](sample-outputs/pr-1.md), [source snapshot](sample-outputs/evidence/pr-1.json). One changed file, +16/-39.
- [PR 7128](https://github.com/psf/requests/pull/7128): empty cookie value fix and regression test; [full output](sample-outputs/pr-2.md), [source snapshot](sample-outputs/evidence/pr-2.json). Two changed files, +9/-1.

Each output starts with its PR URL and exact command in an HTML comment. Replays require the snapshot PR identity to match `--pr`. The snapshot JSON contains `pr_url`, `files` entries (`filename`, `patch`), and optional title, SHAs, source, metadata counts. Snapshots describe the captured revision; future live PR revisions may differ.

## Output format

A shortened example (the sample directory contains complete outputs):

```markdown
## Summary of changes

The supplied patches change 2 files: src/requests/cookies.py, tests/test_requests.py. Observed textual changes contain 9 additions and 1 deletions, including 8 added test lines; this draft uses offline heuristics and does not execute the target code.

## Identified risks

- Security/session-related path changed: src/requests/cookies.py (path signal, not a confirmed defect).

## Improvement suggestions

- Exercise boundary cases and existing security/session tests: src/requests/cookies.py.
- Run the changed tests; test presence does not establish coverage or passing status.

## Confidence

**Med** (Medium abbreviated Med).
```

Every output includes a two-sentence summary, risk list, improvement list, and Low/Med/High confidence. `Med` is the brief's spelling of the issue's `Medium`. Low means no textual evidence, incomplete coverage, more than 2,000 changed lines, or more than 50 files. Med means ordinary concrete diff/path signals. High means a concrete credential pattern was observed in an otherwise bounded complete diff; it does **not** confirm the credential is real or certify the PR as safe.

## GitHub Action

[`.github/workflows/claude-review.yml`](.github/workflows/claude-review.yml) runs on `pull_request`, checks out this reviewer repository's trusted base commit, generates `review.md`, and uploads it as the `pr-review-draft` artifact. It grants read permissions only and does not post a comment. Target PR code is not executed. It becomes usable after these reviewer files exist on the base branch of the repository containing the workflow. For another target repository, copy the reviewer package/script into that repository's base branch alongside the workflow, or change checkout to a fixed trusted commit of your published reviewer repository. No remote publication or workflow run was performed here.

## LLM backend slot (documentation only)

`reviewer.engine.HeuristicEngine.review(snapshot) -> str` is the replaceable engine interface. To add Claude/Anthropic later, implement another class with the same method and select it explicitly in the CLI. An adapter would read `ANTHROPIC_API_KEY` and a configured `ANTHROPIC_MODEL` from environment variables, send bounded/redacted patches to Anthropic's Messages API, treat all PR text as untrusted data, and validate that the result has the required Markdown sections and confidence enumeration. It should report API errors explicitly and require an intentional opt-in before sending repository content externally.

No Anthropic client, API call, `--backend` flag, Claude Code integration, or LLM test is included. Setting an Anthropic environment variable alone does not change the offline engine. This delivery implements the brief's documentation-only backend slot; it does not claim to be an active Claude Code sub-agent.

## Known limitations

- Signals use paths, observed added/removed lines, deletion ratio, test-file changes, and credential regexes; they do not establish bugs or test coverage.
- No repository context, semantic/type analysis, dependency advisories, target test execution, or merge approval. A filename-based security signal can be a false positive; secrets outside configured patterns can be missed.
- Binary files and truncated/omitted patches are not analyzed. Large responses over the resource cap fail explicitly. GitHub's file cap and missing textual patches reduce confidence.
- Review output redacts matched credential values and escapes title/path Markdown and HTML. Saved source snapshots still contain original patches and should be handled according to their contents.
- The workflow is supplied but not executed here. Python live GitHub access was blocked; connector retrieval plus local replay is the demonstrated integration.
- The original bounty asks for a Claude Code agent; the brief deliberately specifies an offline engine and a documentation-only LLM slot. Bounty acceptance of that scope has not been confirmed.
