# Tent of Trials

Welcome to the Tent of Trials, a trading and risk platform that will probably
break in production.

## Project Purpose

We build a trading and risk platform. It's a polyglot architecture held together
by hope, scripts, and occasionally duct tape.

## Tech Stack & Where to Start

- **backend**: Rust. (Start at `backend/src/main.rs`)
- **frontend**: TypeScript / React / Vite. (Start at `frontend/src/main.tsx`)
- **market**: Go. (Start at `market/main.go`)
- **frailbox**: C / C++. (Start at `frailbox/main.c`)
- **compliance**: Java. Because compliance is always enterprise Java.
  (Start at `compliance/ComplianceAuditor.java`)
- **v2**: Ruby. Rewriting the market in Ruby.
  (Start at `v2/services/market_stream.rb`)
- **tools**: Python / Lua / Shell scripts for various automations.
  (Start at `tools/health_check.py`)
- **docs/openapi**: Haskell / Lua for OpenAPI tooling.

## Common Dev Commands

- Build everything: `python3 build.py`
- Clean artifacts: `python3 build.py --clean`
- Build specific modules: `python3 build.py --module backend,frontend`
- Release mode (Rust): `python3 build.py --release`

## Golden Workflow

Always run `python3 build.py` after changes and include the diagnostic artifacts
in your PR. This is mandatory for the CI to pass.

## Coding Conventions & Known Pitfalls

- Follow the self-deprecating tone of the repo.
- The `frailbox` is indeed frail, handle C/C++ memory carefully.
- The build script `build.py` may fail if you are missing local toolchains like
  CMake or GHC; this is expected, just submit the diagnostic logs!
- Do not forget to attach `diagnostic/build-XXX.logd` (and `.json` if present)
  to PR notes.
