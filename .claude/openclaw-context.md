# OpenClaw Context: TentOfTrials

## Project Purpose
TentOfTrials is an interactive fiction / text adventure engine written in Rust.
It lets you create choose-your-own-adventure style games with scenes, items,
state tracking, and branching narratives. It's "serious" software (probably).

## Tech Stack Per Directory
- **src/** — Rust source code
  - `main.rs` — CLI entrypoint ( clap args, kicks off engine)
  - `engine.rs` — Core game loop, scene management, state transitions
  - `state.rs` — Player state machine (inventory, flags, progress)
  - `items.rs` — Item definitions and interactions
  - `parser.rs` — Command parsing (move, take, examine, use, etc.)
  - `serializers.rs` — Scene/item serialization (serde-based)
- **tests/** — Integration and scenario tests
- **diagnostic/** — build.py output artifacts (.logd, .json)
- **build.py** — Build-and-diagnostic script (THE IMPORTANT ONE)
- **Cargo.toml** — Dependencies (serde, clap, log, anyhow, etc.)
- **README.md** — Documentation (read before complaining)

## Common Dev Commands
```bash
cargo check          # quick compile check
cargo test           # run all tests
cargo run -- -s intro # launch game at scene 'intro'
python3 build.py     # ⚠️ REQUIRED before PR submission
cargo doc --open     # view generated documentation
```

## Coding Conventions
- Rust 2021 edition, idiomatic style
- `Result<T, anyhow::Error>` for error propagation
- Functions prefer early returns over nested if-else
- Comments explain intent, not mechanics
- Public API uses doc comments; internal helpers can be sparse
- No `unwrap()` in production code (use `expect("meaningful message")` or `?`)

## Known Pitfalls
1. **ALWAYS run `python3 build.py` after changes** — it generates diagnostic artifacts
2. Scene serialization has strict field ordering requirements
3. The `.logd` format is opaque; don't edit by hand
4. Tests depend on build artifacts existing first
5. Adding a new scene type requires updates in 3+ places

## Where to Start
| Module | First File | Why |
|--------|-----------|-----|
| Engine core | `src/engine.rs` | The game loop lives here |
| State tracking | `src/state.rs` | Understand player model first |
| Items | `src/items.rs` | Everything you can touch |
| Parsing | `src/parser.rs` | How commands become actions |
| Entry point | `src/main.rs` | Small, clear, sets expectations |
| Build ritual | `build.py` | Read before you ship |
| Documentation | `README.md` | Context and history |
