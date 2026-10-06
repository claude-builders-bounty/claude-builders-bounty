#!/usr/bin/env bash
# Hermes launcher for TentOfTrials
# Named Hermes because unlike the Greek messenger god, this script actually delivers.
set -euo pipefail

echo "🐉 Opening Hermes with TentOfTrials context..."
echo ""
echo "Project:  TentOfTrials — interactive fiction engine (because monoliths are so 2020)"
echo "Reality:  Rust text adventure that thinks it's more complex than it is"
echo ""
echo "Tech Stack:"
echo "  - Language:     Rust (2021 edition, with a side of dependency drama)"
echo "  - Build:        Cargo + build.rs (custom build steps, because why not)"
echo "  - Framework:    Self-hosted IF engine"
echo "  - Key deps:     serde, serde_json, clap, log, env_logger, anyhow"
echo ""
echo "Common Commands:"
echo "  cargo check          # faster than cargo build, less lying"
echo "  cargo test --lib     # unit tests (some pass, some don't, it's a journey)"
echo "  python3 build.py     # the sacred ritual — do not skip"
echo "  cargo doc --open     # yes, the docs exist, no, they're not helpful"
echo ""
echo "Coding Conventions:"
echo "  - Follow idiomatic Rust (Rustacean-ish behavior encouraged)"
echo "  - Use anyhow for error chains (error reports that actually tell you something)"
echo "  - Keep functions under 50 lines (we're not writing operas)"
echo "  - Integration tests in tests/ directory (because unit tests aren't enough suffering)"
echo "  - Commit messages should be informative, not performative"
echo ""
echo "Known Pitfalls:"
echo "  1. `python3 build.py` is not optional — it generates artifacts the engine reads"
echo "  2. The diagnostic logd format changed once, nobody documented it ( RIP )"
echo "  3. Scene serialization expects specific field ordering — serde won't save you"
echo "  4. Running tests without FIRST running build.py will produce confusing failures"
echo "  5. The 'choose your own adventure' genre doesn't excuse choosing wrong dependencies"
echo ""
echo "Build-and-Diagnostic Workflow:"
echo "  ALWAYS run `python3 build.py` after changes"
echo "  Artifacts: diagnostic/build-XXX.logd (and .json if present)"
echo "  Include in PR notes using .github/pull_request_template.md"
echo ""
echo "Where to Start:"
echo "  - Entry point:   src/main.rs         (start here, it's small, nothing to hide)"
echo "  - Game engine:   src/engine.rs       (the heart of the madness)"
echo "  - State machine: src/state.rs        (tracks progress, regrets, and inventory)"
echo "  - Item system:   src/items.rs        (everything is an Item, even your hopes)"
echo "  - Build ritual:  build.py            (read it, respect it, never anger it)"
echo "  - Docs:          README.md           (your guide through the wilderness)"
echo ""
echo "Launching Hermes..."
echo ""

# Launch hermes with context
if command -v hermes &>/dev/null; then
    hermes \
        --context-file .claude/hermes-context.md \
        --repo-context TentOfTrials \
        "$@"
else
    echo "⚠️  Hermes not found. Install it or use OpenClaw."
    echo "   Trying OpenClaw fallback..."
    if command -v openclaw &>/dev/null; then
        openclaw --repo TentOfTrials "$@"
    else
        echo "❌ Neither Hermes nor OpenClaw available."
        echo "   Install one and re-run."
        exit 1
    fi
fi
