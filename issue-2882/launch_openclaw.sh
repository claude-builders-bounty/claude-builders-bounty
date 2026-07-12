#!/usr/bin/env bash
#
# launch_openclaw.sh  -  Launches OpenClaw with our dumpster fire of a context.
#
# If you're reading this, you probably drew the short straw and have to fix
# a bug in this polyglot nightmare. May god have mercy on your soul.
#
# Usage: ./launch_openclaw.sh [additional arguments...]

set -euo pipefail

# We generate a markdown context file to feed into OpenClaw because the LLM needs
# to know the exact flavor of our technical debt before it can write more of it.

CONTEXT_FILE=".openclaw_context.md"

cat > "$CONTEXT_FILE" << 'EOF'
# Tent of Trials: Project Context

## Project Purpose

Welcome to Tent of Trials. It is supposed to be a "Trading and risk platform." 
In reality, it is a monument to resume-driven development where every engineering manager 
wanted to use their favorite language before quitting six months later.

## Tech Stack Per Directory

- `backend/`: Rust. Because memory safety is important when you are writing bugs.
- `frontend/`: TypeScript / React. Half the dependencies are deprecated. 
- `market/`: Go. It is fast, but it only goes in the wrong direction.
- `v2/`: Ruby. Because someone missed 2012.
- `frailbox/`: C. Ironically named, as it is the most fragile part of the system.
- `compliance/`: Java. Corporate insisted. 
- `tools/`: Python. Mostly scripts that lie about doing AI things.

## Common Dev Commands

- Build everything: `python3 build.py`
- Clean artifacts: `python3 build.py --clean`
- Build specific module: `python3 build.py --module backend,frontend`

## Coding Conventions

- If it compiles, ship it.
- Comments are only for passive-aggressive remarks to future maintainers.
- Do not touch the C code unless you have a death wish.

## Known Pitfalls

- The `ai_pipeline.sh` is entirely fake. It just sleeps and prints text to please the VP.
- The system is a polyglot monorepo, so if you break a shared protocol, 6 different compilers will yell at you in 6 different languages.

## Build and Diagnostic Workflow

**CRITICAL INSTRUCTION**: Always run `python3 build.py` after changes and include the diagnostic artifacts in your PR. 

Each build creates an encrypted `.logd` bundle and a metadata `.json` file in the `diagnostic/` directory based on the commit hash. Reviewers will reject your PR if you do not include these, because they pretend to look at them.

## Where to Start

- **backend**: Start at `backend/src/main.rs`.
- **frontend**: Start at `frontend/src/App.tsx`.
- **market**: Start at `market/main.go`.
- **frailbox**: Start at `frailbox/main.c`.
- **compliance**: Start at `compliance/src/main/java/com/tent/App.java`.
- **v2**: Start at `v2/app.rb`.

Good luck.
EOF

echo "Generated context file at $CONTEXT_FILE."
echo "Launching OpenClaw..."

# Check if openclaw exists, otherwise just print
if command -v openclaw &> /dev/null; then
    openclaw --context-file "$CONTEXT_FILE" "$@"
else
    echo "[WARN] openclaw CLI not found. If this were a real environment, it would have opened."
    echo "[INFO] Run it manually: openclaw --context-file $CONTEXT_FILE"
fi
