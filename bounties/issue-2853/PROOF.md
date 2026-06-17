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
