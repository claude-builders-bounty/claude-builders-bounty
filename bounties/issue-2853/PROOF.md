# Issue #2853 — Read Tool Hook (zeroeye)

Cross-repo bounty delivery for [claude-builders-bounty#2853](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2853).

## Implementation PR

https://github.com/lobster-trap/zeroeye/pull/3

Branch: `feat/read-tool-hook-market-ai` on `advancedresearcharray/zeroeye`

## What was implemented

Read-only `read_market_data` tool hook scaffolding across three layers:

| Layer | Files | Purpose |
|-------|-------|---------|
| Go AI | `market/ai/tools.go`, `tools_test.go` | `ToolHook`, `ToolRegistry`, `ReadTool`, `MarketDataProvider` |
| Gateway | `market/gateway/api.go`, `ai_tools_test.go` | `GET /api/v1/ai/tools`, `POST /api/v1/ai/tools/read`, `POST /api/v1/ai/tools/execute` |
| Frontend | `frontend/src/ai/readToolHook.ts`, `chat.ts` | `ReadToolHook` client wired into `AiChatService` |

## Verification (2026-06-17)

```bash
cd /workspace/zeroeye/market && go test ./ai/... ./gateway/... -v
# PASS — 7 tests (4 ai + 3 gateway)

python3 build.py -m market   # via Docker Ubuntu 24.04 + Go 1.26
# PASS — market module builds successfully
```

## Build diagnostics

| Artifact | Path |
|----------|------|
| Encrypted logd | `diagnostic/build-10027b8d.logd` |
| Metadata JSON | `diagnostic/build-10027b8d.json` |
| Password | `22b783167d7d16cd39f0` |
| Decrypt | `encryptly unpack diagnostic/build-10027b8d.logd <outdir> --password 22b783167d7d16cd39f0` |

## claude-builders-bounty tests

```bash
cd /workspace/claude-builders-bounty/claude-builders-bounty && npm test
# OK: all CI validation checks passed
```
