# claude-review

`claude-review` creates a deterministic, static, evidence-grounded Markdown review of one GitHub pull request. It parses the pull request metadata, changed-file records, and unified diff, then reports a bounded set of patterns found on changed lines. The package uses only the Python standard library.

## Important limitation

This is not an AI-model reviewer and does not invoke, simulate, or represent reasoning by Claude or any other model. It performs deterministic, rule-based scanning of text visible in the supplied diff. It cannot understand intent, validate business behavior, prove safety, reason across unchanged code, inspect a repository working tree, or replace expert review. Every report also identifies itself as deterministic and static, rather than a paid-model or exhaustive expert audit.

## Tested version and setup

Verification used Apple macOS Python 3.9.6. The implementation uses only that standard library; no dependency installation, API key, token, or configuration file is required. Newer Python versions are expected but were not exercised in this release.

Run commands from the directory containing this README and the executable `claude-review` launcher.

To check that the launcher and CLI are available:

```bash
./claude-review --help
./claude-review --version
```

## Online review

Online mode reviews a public GitHub pull request by making unauthenticated requests to:

- `https://api.github.com/repos/OWNER/REPO/pulls/NUMBER`
- the pull request files endpoint, up to five pages of 100 files
- `https://github.com/OWNER/REPO/pull/NUMBER.diff`

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
./claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
```

The first command writes Markdown to stdout. The second creates the parent directory when needed and writes UTF-8 text ending in a newline. Do not use `--context-dir` with online mode.

## Claude Code integration

The bundled Claude Code subagent is [.claude/agents/pr-reviewer.md](.claude/agents/pr-reviewer.md). In Claude Code, invoke the `pr-reviewer` agent with a GitHub PR URL; from the repository root, it runs `./claude-review --pr <URL>` and returns the deterministic four-heading report verbatim. It performs deterministic/static analysis, not model analysis, and says so on request. It posts only after you explicitly request posting, through your existing configured GitHub CLI workflow.

## Offline review

Offline mode does not make network requests. It reads three immutable files from `CONTEXT`:

```text
metadata.json
files.json
pr.diff
```

Prepare those files with your own authorized GitHub export process; this CLI does not fetch or refresh them. The `metadata.json` number, optional `html_url`, and required `updated_at` field are validated; the number and URL, when present, must match the `--pr` URL.

```bash
./claude-review \
  --pr https://github.com/owner/repo/pull/123 \
  --offline \
  --context-dir /path/to/snapshot \
  --output review.md
```

Relative context and output paths are interpreted from the current working directory, not the launcher path.

## Output contract

A successful report has exactly these second-level headings, in this order:

```text
## Summary of changes
## Identified risks
## Improvement suggestions
## Confidence score
```

The summary has two to three sentences. Risks cite a changed file, hunk, and changed-line number when line evidence is available, show at most 240 characters of evidence, and include why the pattern matters and a concrete check or change. Output is capped at 49,152 UTF-8 bytes. Findings are capped at 24; omitted lower-priority findings are explicitly counted rather than silently discarded.

The confidence line uses one of `Low`, `Medium`, or `High`. The deterministic scanner currently elevates any report containing a high-severity finding to `Medium`, reflecting the limits of changed-line-only evidence.

## Real-PR examples and provenance

Two examples were generated from frozen real-PR snapshots:

- [examples/pr-4082/review.md](examples/pr-4082/review.md), with [examples/pr-4082/provenance.json](examples/pr-4082/provenance.json)
- [examples/pr-4122/review.md](examples/pr-4122/review.md), with [examples/pr-4122/provenance.json](examples/pr-4122/provenance.json)

Each provenance record contains the canonical PR URL, head and base SHAs, the source `metadata.json` field `updated_at`, source paths, SHA-256 hashes for all three inputs and generated output, CLI version, and the exact offline command. That timestamp identifies when GitHub last reported the source pull-request metadata as updated; it is not the time this tool generated the report. The examples are reproducible artifacts, not claimed live-model responses.

## Privacy and security

The CLI sends no credentials, environment values, repository contents, or local files to another service. Online requests are unauthenticated; GitHub receives the PR URL request and sees the caller network address as with any HTTPS request. No authorization header is set, and no GitHub token is read.

Offline mode performs no HTTP requests. Snapshot contents remain local, but a report can quote up to 240 characters of changed-line evidence, so treat saved reports with the same sensitivity as the source diff. File and response limits are intended to bound unexpected input: metadata and diff are limited to 1 MiB, files records to 4 MiB per online page, and online mode stops above 500 changed files.

## Exit codes

| Code | Meaning |
| ---: | --- |
| `0` | Review completed; help or version also exits successfully. |
| `1` | Controlled review error without a more specific code. |
| `2` | Invalid PR URL or command-line usage. |
| `3` | Offline context is missing or unreadable; online request failed, was not found/private, or was rate-limited. |
| `4` | Input snapshot or remote response is malformed, unsafe, oversized, or has negative counts. |
| `5` | Pull-request diff is empty. |
| `6` | Output validation failed or an internal implementation error occurred. |

Controlled errors print a single `claude-review: error:` message on stderr and do not print tracebacks.

## Tests and verification

From this directory, run the offline test suite:

```bash
python3 -m unittest discover -s tests -v
```

The release verification used the following commands, all from this directory, and each completed successfully:

```bash
PYTHONPYCACHEPREFIX="$PWD/.compile-cache" python3 -m compileall -q .
python3 -m unittest discover -s tests -v
./claude-review --help
./claude-review --version
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4082 --offline --context-dir tests/fixtures/pr-4082 --output examples/pr-4082/review.md
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4122 --offline --context-dir tests/fixtures/pr-4122 --output examples/pr-4122/review.md
```

The suite contains 22 tests. Both examples were generated twice and compared byte-for-byte; each SHA-256 was identical across the two generations. `release/verification.md` records the commands, statuses, and hashes.

On the managed macOS Python installation, set `PYTHONPYCACHEPREFIX="$PWD/.compile-cache"` before `compileall` so bytecode stays inside the task workspace; remove that cache after verification. The verification record discloses this environment scope.

## Troubleshooting

- `Invalid PR URL`: use an HTTPS `github.com` URL ending in `/pull/POSITIVE_INTEGER`; query strings and fragments are accepted, but API URLs and issue URLs are not.
- `Offline context is missing`: all three exact filenames must exist directly under `--context-dir`, and the directory must be readable.
- `metadata.json does not match`: the PR number and, when present, canonical HTML URL must match `--pr`.
- `metadata.json is missing an updated_at timestamp`: export the complete public PR metadata object; deterministic provenance uses GitHub's source update time rather than runtime generation time.
- `Malformed JSON`, `Malformed diff`, or `Oversized`: inspect the snapshot export and recreate it rather than editing reports.
- Online `HTTP 403`: an unauthenticated request may be GitHub rate-limited or forbidden; retry later or use an offline snapshot.
- Permission denied on the launcher: ensure `claude-review` remains executable (`chmod +x claude-review`) and invoke it from a mounted filesystem that permits execution.
- An unexpected `internal review failure` with exit code 6 is an implementation boundary, not a report finding; reproduce with the tests and inspect the relevant input before changing code.
