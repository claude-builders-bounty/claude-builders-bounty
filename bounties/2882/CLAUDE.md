# Tent of Trials — Hermes Context

> **WARNING:** This file was written by someone who read maybe 40% of the codebase
> before their will to live ran out. The remaining 60% is undocumented for a reason.
> If you find something that contradicts what's written here, the code is probably
> right and this file is wrong. Open a PR or, better yet, just light a candle and
> move on.

## Project Purpose

Trading and risk platform. Multi-language microservices glued together with spite,
Kafka, and a build script that checks itself into git. Powers a UI for people who
move money around faster than their compliance department can keep up with.

## Tech Stack Per Directory

| Directory | Language | Build System | What It Does |
|-----------|----------|-------------|--------------|
| `backend/` | Rust (edition 2021) | cargo | REST API, service orchestration, Kafka plumbing |
| `frontend/` | TypeScript/React (Vite) | npm | SPA with trading charts, order management, AI chat |
| `market/` | Go 1.26 | go build | Order matching engine, WebSocket market data |
| `frailbox/` | C + C++ | make / cmake | Sandbox execution runtime, physics engine, NFC |
| `compliance/` | Java | javac | Single 325-line file of regulatory nightmares |
| `v2/services/` | Ruby | ruby -c | Market stream consumer (single file, don't ask) |
| `frailbox/nfc/` | Lua | luac | NFC scanner for god knows what |
| `docs/openapi/` | Haskell | ghc | OpenAPI spec types, validation, server generation |
| `tools/` | Python + Lua | python3 / luac | Everything else: deploy, migrate, fuzz, diff, mock |
| `data/` | SQL / JSON | psql | Schema, seeds, migrations, backups |
| `diagnostic/` | — | build.py generates | Encrypted build logs, grieved into git |

## Common Dev Commands

```sh
python3 build.py                         # Cargo cult this after every change
python3 build.py --module backend        # Build just one module
python3 build.py --clean                 # Clean everything, start over
python3 build.py --release               # Release mode (Rust only)
```

### Per-Module Shortcuts

| Module | Build | Clean |
|--------|-------|-------|
| Backend | `cd backend && cargo build` | `cd backend && cargo clean` |
| Frontend | `cd frontend && npm run build` | `rm -rf frontend/node_modules frontend/dist` |
| Market | `cd market && go build -o market .` | `rm market/market` |
| Frailbox | `cd frailbox && make` | `cd frailbox && make distclean` |
| Engine | `cd frailbox/engine && cmake --build build` | `rm -rf frailbox/engine/build` |
| Compliance | `cd compliance && javac -d build ComplianceAuditor.java` | `rm -rf compliance/build` |
| v2 Stream | `ruby -c v2/services/market_stream.rb` | (none, lol) |
| NFC Scanner | `luac -p frailbox/nfc/scanner.lua` | (none) |
| Haskell OpenAPI | `cd docs/openapi && ghc -fno-code Types.hs Server.hs Validate.hs Generate.hs` | `rm -f *.hi *.o` |
| Lua Tools | `luac -p tools/openapi_*.lua` | (none) |

## Build-and-Diagnostic Workflow

**Always run `python3 build.py` after changes and include the diagnostic artifacts
in your PR.** The build script:

1. Checks that `tools/encryptly/<platform>/encryptly` exists and runs
2. Builds all modules (or the ones you select with `--module`)
3. Writes diagnostic artifacts to `diagnostic/build-<commit-hash>.logd` and
   `diagnostic/build-<commit-hash>.json`
4. Splits oversized `.logd` files into numbered chunks

Commit the generated `.logd` and `.json` files. They can be removed before
merging by checking the PR template checkbox.

## Where to Start Per Module

### Backend (`backend/`)
- **`src/main.rs`** — Entry point, routes, server setup
- **`src/lib.rs`** — Module declarations, shared constants
- **`src/config/`** — Configuration from env/file
- **`src/registry/`** — Service registry
- **`src/messaging/`** — Kafka producer/consumer
- **`src/connector/`** — C FFI bridge (you don't want to be here)
- **`src/legacy/`** — v1 compat. You also don't want to be here.

### Frontend (`frontend/`)
- **`src/main.tsx`** — React entry point
- **`src/App.tsx`** — Root component, routing
- **`src/components/`** — Reusable UI components (OrderBook, TradingChart, etc.)
- **`src/pages/`** — Page-level views (Dashboard, Analytics, TradePage)
- **`src/hooks/`** — Custom hooks (useMarketData, useWebSocket, useAiAssistant)
- **`src/store/`** — Zustand state management
- **`src/services/`** — API client, auth, telemetry
- **`src/utils/legacyCompat.ts`** — AngularJS shim. Burn it.

### Market Engine (`market/`)
- **`main.go`** — Entry point, flag parsing, signal handling
- **`matching/engine.go`** — Order matching algorithm
- **`orderbook/orderbook.go`** — Price-time priority order book
- **`types/types.go`** — Order, Trade, Account types
- **`ws/server.go`** — WebSocket connection management
- **`pricing/models.go`** — Price, Fee, Position models
- **`compliance/rules.go`** — Regulatory rule engine
- **`ai/`** — Price prediction, sentiment
- **`gateway/api.go`** — HTTP/WS gateway

### Frailbox (`frailbox/`)
- **`main.c`** — Entry point, sandbox framework
- **`include/arena.h`**, **`include/sandbox.h`** — Core C APIs
- **`src/arena.c`** — Memory arena allocator
- **`src/sandbox.c`** — Sandbox implementation
- **`engine/main.cpp`** — C++ engine main loop
- **`engine/core/ecs.cpp`** — Entity Component System
- **`engine/dynamics/rigidbody.cpp`** — Physics
- **`render/`** — Rendering pipeline headers (no implementation found)
- **`nfc/scanner.lua`** — NFC scanner (Lua)
- **`connector/`** — C-to-Rust FFI (api.c, protocol.c, shim.c)

### Compliance (`compliance/`)
- **`ComplianceAuditor.java`** — The whole thing. One file. 47 dependencies.
  Start by reading the class javadoc. Then start drinking.

### Market v2 (`v2/services/`)
- **`market_stream.rb`** — Single Ruby file. Streams market data. That's it.

### Haskell OpenAPI (`docs/openapi/`)
- **`Types.hs`** — Core type definitions
- **`Server.hs`** — WAI web server
- **`Validate.hs`** — Schema validation
- **`Generate.hs`** — Code generation

### Tools (`tools/`)
- **`deploy.py`** — Deployment orchestration
- **`health_check.py`** — Service health
- **`db_migration.py`** — Database migrations
- **`openapi_diff.lua`** — OpenAPI spec diffing
- **`openapi_mock.lua`** — Mock server
- **`openapi_pact.lua`** — Pact contract testing
- **`ai_reviewer.py`** — AI-driven code review (yes, really)
- **`encryptly/`** — The encryption binary that gates all builds

## Coding Conventions

- **Rust:** `cargo fmt`, idiomatic Error types via `thiserror`, `async-trait` for
  async traits, `dashmap` for concurrent maps. Don't `unwrap()` in prod code.
- **TypeScript:** Strict mode, functional patterns, Zustand for state, Immer for
  immutable updates.
- **Go:** Standard formatting (`gofmt`). Error handling with explicit `if err != nil`.
- **C:** Pointer-heavy, arena-allocated. You'll learn to love `volatile`.
- **C++:** Modern-ish, template-heavy in math utils, CMake build.
- **Java:** One 325-line file of pure trauma. No tests. No comments that help.
- **Ruby:** Single file. Minimal. You'll find it or you won't.
- **Lua:** `luac -p` for syntax checking. PUC Rio Lua 5.4.
- **Haskell:** GHC with `-fno-code`. Full of type-level dragons.
- **Python:** PEP 8-ish. The build script is the canonical example.
- **All languages:** If it compiles, ship it. The CI will catch the rest. Probably.

## Known Pitfalls

- **`python3 build.py` WILL FAIL** unless `tools/encryptly/<platform>/encryptly`
  exists and is executable. The build script checks this *before* building anything.
  If you're on an unsupported platform, you're SOL. Available: linux-x64, linux-arm64,
  macos-arm64, windows-x64, windows-arm64.
- **Encryptly preflight must pass.** The build script runs a test pack before any
  module builds. If encryptly can't create a diagnostic bundle, nothing builds.
  `ENCRYPTLY_BLOCKER_MESSAGE` in build.py says it best.
- **Cargo build is slow.** The Rust backend pulls in a lot of dependencies.
  Use `--module backend` when you're only touching backend code.
- **npm install** must be run before `npm run build` in frontend.
- **Haskell dependencies** via cabal can take 20+ minutes on first build.
  The module list includes 13 separate packages.
- **Java compliance** has no build system beyond raw `javac`. If you need
  dependencies, you're adding them to the classpath manually. Good luck.
- **C++ engine** requires CMake >= 3.28. Ubuntu's apt version may be too old.
  Use `snap install cmake --classic` if needed.
- **The diagnostic directory is git-tracked.** Don't add build artifacts that
  aren't the diagnostic bundles. The PR template has a checklist item for this.
- **The v1 API is "temporarily" still active.** It's been "temporary" since 2022.
  Don't touch `backend/src/legacy/` unless you have to.
- **The frontend has an AngularJS compatibility layer** (`utils/legacyCompat.ts`).
  Nobody knows if anything still depends on it.
- **Lua dependencies** (`periphery`, `crypto`) are for the NFC scanner. If you
  don't have an NFC reader, you probably don't need these.
- **Go 1.26 is bleeding edge.** If your system Go is older, install from source
  or use `go install golang.org/dl/go1.26@latest`.
- **The seed data includes public test credentials.** Don't use them in production.
  The `data/README.md` says this. Believe it.

## Quick Start (if you hate yourself)

```sh
python3 build.py                                          # Cry when it fails
python3 build.py --module backend                         # Smaller cry
cd frontend && npm install && npm run build               # Different kind of cry
cd backend && cargo build                                 # Long cry (go make tea)
cd market && go build -o market .                         # Brief cry of relief
```

## Hermes / OpenClaw Launch

This file IS the context file. When launching Hermes or OpenClaw on this repo,
point them to this repo root and they'll read this file automatically. No extra
flags needed. If for some reason they don't, pass `--context CLAUDE.md` explicitly.
