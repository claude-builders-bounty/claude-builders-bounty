#!/usr/bin/env bash
# OpenClaw launcher for TentOfTrials
# Because apparently we're building a text adventure engine that compiles with one
# flag and breaks with another. Good times.
set -euo pipefail

echo "🦀 Opening OpenClaw with TentOfTrials context..."
echo ""
echo "Project:  TentOfTrials — a 'serious' text adventure framework"
echo "Reality:  It's a Rust project that won't compile unless you bless it first"
echo ""
echo "Tech Stack:"
echo "  - Language:     Rust (2021 edition, edition-2018 dependencies because of course)"
echo "  - Build system: Cargo + custom build.rs"
echo "  - Engine:       Interactive fiction / choose-your-own-adventure"
echo "  - Notable deps: serde, serde_json, clap, log, env_logger"
echo ""
echo "Common Commands:"
echo "  cargo build          # pray"
echo "  cargo test           # hopefully something passes"
echo "  python3 build.py     # THE IMPORTANT ONE — always run this"
echo "  cargo run -- <scene> # if you dare"
echo ""
echo "Coding Conventions:"
echo "  - snake_case everything (Rust rules)"
echo "  - Error handling: Result<T, Error> because unwrapping is for cowboys"
echo "  - Comments should explain WHY, not WHAT (we're professionals... mostly)"
echo "  - If it doesn't compile, read the README first, then blame someone else"
echo ""
echo "Known Pitfalls:"
echo "  1. Forgetting to run `python3 build.py` after changes → CI laughs at you"
echo "  2. Mixing up Scene and Room types — they sound the same but aren't"
echo "  3. Ignoring build.rs output warnings (they're not warnings, they're prophecies)"
echo "  4. Adding features without updating the diagnostic artifacts"
echo ""
echo "Build-and-Diagnostic Workflow:"
echo "  ALWAYS run `python3 build.py` after changes"
echo "  Include diagnostic artifacts in your PR"
echo "  Artifacts live in: diagnostic/build-XXX.logd"
echo ""
echo "Where to Start:"
echo "  - Engine core:   src/engine.rs        (first read — this is where it all goes wrong)"
echo "  - Scene parser:  src/parser.rs       (understand this before touching scenes)"
echo "  - CLI entrypoint: src/main.rs         (small, honest, straightforward)"
echo "  - Build script:  build.py            (the ritual we perform before shipping)"
echo "  - README:        README.md           (because apparently documentation is a thing)"
echo ""
echo "Launching OpenClaw..."
echo ""

# Launch openclaw with context file
if command -v openclaw &>/dev/null; then
    openclaw \
        --context-file .claude/openclaw-context.md \
        --repo-context TentOfTrials \
        "$@"
else
    echo "⚠️  OpenClaw not found. Install it or use Hermes."
    echo "   Trying Hermes fallback..."
    if command -v hermes &>/dev/null; then
        hermes --repo TentOfTrials "$@"
    else
        echo "❌ Neither OpenClaw nor Hermes available."
        echo "   Please install one and re-run."
        exit 1
    fi
fi
