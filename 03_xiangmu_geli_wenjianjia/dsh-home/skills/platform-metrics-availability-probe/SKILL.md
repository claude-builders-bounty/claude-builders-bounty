---
name: platform-metrics-availability-probe
description: Prove which platform metrics an API can return.
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [data-availability, probes, reverse-engineering, metrics, api]
    related_skills: [evidence-backed-deliverables, unattended-agent-execution, xianyu-automation, hermes-wf-kanban-orchestration]
---

# Platform Metrics Availability Probe

Before building a dashboard, diagnostic, or pricing model on top of a third-party platform, you must establish **which numbers the platform will actually hand you**. This skill is the read-only workflow for that: enumerate the fields the API really returns, classify every missing metric into one of three causes, and keep an errata trail so a wrong earlier conclusion cannot survive. It does not cover writing the feature that consumes the data.

## When to Use

- A task says 数据源摸底 / 指标探测 / 数据可得性 / 接口盘点 and the output is a capability matrix, not a feature
- You are about to compute a rate (客询率/成交率/曝光转化) and have not yet proved the denominator exists
- An earlier card claimed a metric is "unavailable" or "zero" and nobody re-checked it
- A platform SDK documents a field but you have not seen the raw response

Don't use for: fields you control end-to-end (your own DB), or pure web scraping where the HTML is the contract — use `browser-exec-web-scraping` there.

## Prerequisites

- Read-only credentials, and an explicit ban on write operations in the task (no publish / delete / message send)
- An `evidence/` directory outside the source tree or inside the repo's analysis dir, one raw response file per call
- The platform CLI/SDK **version** recorded (`<cli> version`) — capabilities differ between minor versions
- Interpreter: on Windows run `python <file>`, never `python -c` when unattended (`unattended-agent-execution`)

## How to Run

```bash
python scripts/tmp_probe_<metric>.py > <scratch>/probe_stdout.txt 2>&1
printf 'EXIT=%s\n' "$?"
```

One probe per question, each writing its raw JSON next to its stdout. Never summarise inside the probe — classify afterwards.

## Quick Reference

| Step | Command / check |
|---|---|
| Enumerate CLI surface | `<cli> list-commands --format json` → read the `write` flag per command |
| Version | `<cli> version` |
| Field sweep | regex the raw JSON keys: `(cnt\|count\|num\|rate\|amount\|time\|date)` |
| Negative proof | for each candidate key: `key in obj` → record True/False, not "probably not" |
| Raw capture | one file per call: `evidence/<card>/<api>_<ts>.json` |
| Errata | append `§勘误` to the interface inventory; keep the superseded file as `*.r1-已作废-<reason>.md` |

## Procedure

1. **Map the surface before probing values.** Dump the command/API list with its read/write flag and version. Completion: a table of commands with 只读/写 column and a recorded version string.
2. **Sweep one object's fields exhaustively.** Take a single raw response and list every key; classify candidates by regex on name. Completion: a counted statement like "itemDO 有 62 个字段，含 cnt 的 7 个：…；曝光类 8 个候选全部 False".
3. **Classify each missing metric into exactly one of three tiers.**
   - **不存在** — no command, no field, no endpoint in this version (prove by enumerating all commands + SDK modules and grepping for the semantic: `order|trade|deal|sold|amount`)
   - **存在但被拒** — the endpoint exists, the call is refused (risk-control / 风控 / 403 / RGV-style codes). Prove it is API-scoped, not account-scoped: another endpoint must succeed in the same minute
   - **存在且为零** — the call succeeds and the value really is 0; a `0` is a data point, not a missing capability
   Completion: every metric in the matrix carries a tier plus the command that proves it.
4. **Write the matrix deliverable** (`analysis/0x-<topic>探测.md`): one row per metric = 指标 / 结论(tier) / 证据文件 / 出处(源码行号或命令). Completion: no row without an evidence path.
5. **Re-run the negative probes once more before publishing**, because risk-control windows expire. A "blocked" verdict from 03:47 must be re-tested at 04:01 or labelled with its time window. Completion: each 被拒 verdict carries the window and the success/failure count (`13 次全拒`).
6. **Errata discipline.** If a later card overturns an earlier conclusion, do not silently edit history: append a numbered `§勘误` block to the inventory, and rename the superseded report to `*.r1-已作废-<reason>.md` so both versions stay readable. Completion: the errata block names the old claim, the new claim, and the evidence file.
7. **State the consumer impact.** Finish with `能算 / 不能算 / 只能近似` for the rates the business wanted. Completion: any metric used as a denominator is explicitly labelled, or the rate is declared not computable.

## Pitfalls

- **A `0` from a swallowed exception is not data.** SDK wrappers commonly `except: return []` (observed: `ItemManager.list_items` returns `[]` on auth failure, indistinguishable from "0 items"). Always grep the run log for `ERROR` before believing a zero count.
- **Documented fields lie.** A bundled skill doc claimed a view API exposes 曝光 (impressions); the code mapped only want/collect/browse. Treat docs as hypotheses, the raw response as truth.
- **Derived fields with misleading names.** `soldPrice` was the *listed* price, identical to `priceInfo.price` — multiplying it by sold count yields a permanently-zero GMV. Trace where a field is assigned before using it in arithmetic.
- **Risk control is per-API, not per-account.** Detail endpoints can be refused while list and session endpoints stay green in the same minute. Report that distinction, or the next engineer will go re-login for nothing.
- **Token refresh vs session death.** A signed-token expiry (`FAIL_SYS_TOKEN_*`) is usually recoverable by retrying once after the server issues a fresh token in `Set-Cookie`; a real session expiry is not. A SDK that jumps straight to browser re-login skips the retry and reports a permanent failure — check whether one retry would have worked before declaring the account dead.
- **CLI silently clamps and over-returns.** `--limit` was hard-clamped to 100, and the list endpoint returns delisted items too, so "N items" must be filtered by the platform's own status field. Read the CLI source for the clamp.
- **Never write while probing.** Set the SDK's auto-refresh / auto-login flag off (`GOOFISH_AUTO_REFRESH_TOKEN=0` style) so a probe cannot rewrite credential files; verify the credential file mtime is unchanged afterwards.
- **No credential values in evidence.** Record cookie *names*, domains, lengths and expiry only.

## Verification

- Every metric row has an evidence file that exists on disk and a command that reproduces it
- The negative claims are exhaustive against the enumerated command list, not sampled
- 被拒 verdicts carry a time window and a refusal count
- The deliverable's `能算 / 不能算` section names each requested rate explicitly
- Credential file mtime unchanged; zero write operations in the transcript
