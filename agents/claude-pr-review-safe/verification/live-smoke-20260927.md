# Live CLI smoke test (2026-09-27)

The first Claude Code 2.1.283 replay against public PR #4455 exited successfully, but its `result` was a fenced JSON object using a different contract (`summary` string, `findings`, and `Medium-High` confidence). The local validator correctly rejected it. The raw envelope reported `is_error=false`, `stop_reason=end_turn`, and `total_cost_usd=0.4112144`; that value is CLI usage telemetry, not an independently verified incremental cash charge.

The agent instructions and CLI request now name the exact required fields and enum values. The parser removes a surrounding `json` fence from a string result before running the same strict local schema validation; it does not translate or silently accept the incompatible `findings` format.

After that change, the CLI was run on two public GitHub diffs with `--format json`, `--timeout 240`, `--budget-usd 0.50`, no repository checkout, no enabled tools/MCP, no private data, and no posting:

| Public PR | CLI exit | Contract result | Output |
| --- | ---: | --- | --- |
| [claude-builders-bounty#4455](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4455) | 0 | Accepted by the exact schema; 3 summary sentences, 4 risks, 4 suggestions, High confidence | [`samples/review-pr4455.md`](../samples/review-pr4455.md) |
| [claude-builders-bounty#4448](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4448) | 0 | Accepted by the exact schema; 3 summary sentences, 0 risks, 1 suggestion, High confidence | [`samples/review-pr4448.md`](../samples/review-pr4448.md) |

The two Markdown samples were rendered from the validated live CLI results using the same renderer as the command. The 19-test suite, Ruff, and `git diff --check` also pass. This is not an award, merge, or payout receipt.
