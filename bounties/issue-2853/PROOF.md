# Issue #2853 — Read Tool Hook (zeroeye)

Cross-repo bounty delivery for [claude-builders-bounty#2853](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2853).

## Implementation PR

https://github.com/lobster-trap/zeroeye/pull/109

Branch: `pr-3-read-tool-hook` on `advancedresearcharray/zeroeye`

## What was implemented

Read-only `read_market_data` tool hook scaffolding across three layers:

| Layer | Files | Purpose |
|-------|-------|---------|
| Go AI | `market/ai/tools.go`, `tools_test.go` | `ToolHook`, `ToolRegistry`, `ReadTool`, `MarketDataProvider` |
| Gateway | `market/gateway/api.go`, `ai_tools_test.go` | `GET /api/v1/ai/tools`, `POST /api/v1/ai/tools/read`, `POST /api/v1/ai/tools/execute` |
| Frontend | `frontend/src/ai/readToolHook.ts`, `chat.ts` | `ReadToolHook` client wired into `AiChatService` |

## Verification (2026-06-17, hands-on takeover #2)

```bash
cd /workspace/claude-builders-bounty/claude-builders-bounty && npm test
# PASS — 2 README + 14 peer review + 7 issue #2853 + 7 delivery — all OK
```

Committed delivery gates now include `test_pr2871_peer_review_fixes_are_committed_vs_main` so fleet hands-on takeover verifies peer review security/redundancy fixes are in the branch diff vs `main`, not only in the working tree.

## Verification (2026-06-17, hands-on takeover)

```bash
cd /workspace/zeroeye/market && go test ./ai/... ./gateway/... -v
# PASS — 7 tests (4 ai + 3 gateway)

docker run --rm -v /workspace/zeroeye:/workspace/zeroeye -w /workspace/zeroeye golang:1.26 \
  bash -lc 'export PATH=/usr/local/go/bin:$PATH && python3 build.py -m market'
# PASS — market module builds (9.3s); encrypted diagnostic logd created

cd /workspace/claude-builders-bounty/claude-builders-bounty && npm test
# PASS — README, peer review, delivery, and issue #2853 acceptance tests
```

Local zeroeye branch `pr-3-read-tool-hook` HEAD: `069e238` (with fresh diagnostics committed).

## Build diagnostics (latest)

| Artifact | Path |
|----------|------|
| Encrypted logd | `diagnostic/build-069e2382.logd` |
| Metadata JSON | `diagnostic/build-069e2382.json` |
| Password | `5ee81ef173cfefa58e6a` |
| Decrypt | `encryptly unpack diagnostic/build-069e2382.logd <outdir> --password 5ee81ef173cfefa58e6a` |

## claude-builders-bounty acceptance tests

`tests/test_issue_2853_read_tool_hook.py` verifies zeroeye source files, symbols, go tests, and build diagnostics.

```bash
cd /workspace/claude-builders-bounty/claude-builders-bounty && npm run test:issue-2853
# OK: issue #2853 read tool hook acceptance tests passed
```

## PR #2871 peer review resolution

Delivery PR: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2871

| Peer review item | Resolution |
|------------------|------------|
| Security: `git diff --check` in CI script | Replaced with scoped `find` + `grep` trailing-whitespace scan over CI-guarded paths only |
| Correctness: redundant npm subprocess tests | Removed `test_peer_review_script_runs_green` and `test_npm_test_entry_point_runs_green`; coverage lives in `test_peer_review_acceptance.py` |
| Tests: README bounty table absolute links | Covered by `tests/test_readme_links.py` and `tests/test_peer_review_acceptance.py` |
| Style/scope: multiple scaffold files | Each file is required by acceptance tests (workflow, Makefile, package.json, run-ci-checks.sh, .gitignore) |
