# Release verification

Verified on 2026-09-07 from the solution root with Apple macOS Python 3.9.6. This focused verification covers the reviewed release plus the Claude Code integration. All commands ran offline against the final source and fixture state.

## Focused integration change

Added the Claude Code project subagent `.claude/agents/pr-reviewer.md`, documented its invocation and deterministic/static boundary in the README, and extended the offline suite with an agent-contract test. Review behavior, generated examples, fixtures, provenance, CLI contracts, and posting defaults were not changed.

## Deterministic regeneration

Each released example was generated twice at a temporary output path. Both runs were compared byte-for-byte with each other and with the released example; neither released example was overwritten. Temporary directories were removed automatically.

| PR | Run 1 status | Run 2 status | Stable and released SHA-256 |
| --- | ---: | ---: | --- |
| 4082 | 0 | 0 | `e74514e3a74ee7f8de251f570418fed3146fc73ec1d6c3bc827ac907329054c8` |
| 4122 | 0 | 0 | `96f12f213605e4878c9339ca16f58496c551d4005b52176721f6f0c05aa4d886` |

## Final commands and actual outcomes

1. `PYTHONPYCACHEPREFIX="$PWD/.verify-cache" python3 -m compileall -q .` — exit 0, no diagnostics. The Apple Python runtime hardcodes its default bytecode cache under the user library; that path is inaccessible in this managed workspace. The documented local `PYTHONPYCACHEPREFIX` scope keeps the cache in the solution, while running the requested Python module and arguments.
2. `python3 -m unittest discover -s tests -v` — exit 0; `Ran 22 tests in 0.255s`; `OK`.
3. `./claude-review --help` — exit 0; printed usage for `--pr`, `--offline`, `--context-dir`, `--output`, and `--version`.
4. `./claude-review --version` — exit 0; printed `claude-review 1.0.0`.
5. Regeneration of examples 4082 and 4122, twice each at temporary paths — exit 0 for all four runs; byte identity within each PR and against the released example.

Final output hashes remain exactly the deterministic hashes shown above.

## Known limitations

- The reviewer is deterministic and static. It is not Claude, another model, an AI reasoning engine, or an exhaustive expert audit.
- The Claude subagent relays only the CLI report and does not add model-derived findings. It invokes the existing deterministic CLI and does not provide credentials or post without explicit user direction.
- It evaluates supplied changed-line context and bounded metadata only; unchanged code, repository state, runtime behavior, intent, and semantic correctness remain out of scope.
- Binary and rename-only changes are labeled but not content-analyzed.
- Reports are capped at 24 findings, evidence at 240 characters, and output at 49,152 UTF-8 bytes.
- Online mode is unauthenticated and bounded to five 100-file pages (500 changed files).

## Cleanup statement

After verification and before manifest generation, `.compile-cache`, `.verify-cache`, and all solution-local `__pycache__` directories were removed, along with temporary regeneration directories and any empty directories. `claude-review` remains executable.

## Prior reconciliation

A separate GLM reviewer independently verified report contract, provenance, privacy/no-token behavior, static-review disclosure, examples, and manifest file hashes. It correctly blocked the prior release because the manifest root calculation omitted the documented NUL byte following each SHA-256; that root calculation was corrected and independently matched before this focused integration.
