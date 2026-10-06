# Hermes Context: TentOfTrials

## Project Purpose
TentOfTrials is a Rust-based interactive fiction engine for building
choose-your-own-adventure games. Scenes branch, items interact, and state
persists across choices. It is occasionally compared to Zork. This is both
a compliment and a threat.

## Tech Stack Per Directory
- **src/main.rs** — CLI bootstrap (clap argument parsing, engine instantiation)
- **src/engine.rs** — Main game loop, scene resolution, I/O handling
- **src/state.rs** — Player State struct: inventory Vec<Item>, flags HashSet<String>, current_scene
- **src/items.rs** — Item enum/struct definitions, interaction handlers
- **src/parser.rs** — Text command → Action enum conversion
- **src/serializers.rs** — serde Serialize/Deserialize impls for persistence
- **tests/** — Scenario-based integration tests
- **diagnostic/** — `python3 build.py` produces `.logd` and optional `.json` here
- **build.py** — Critical: validates project structure, runs diagnostics, emits artifacts
- **Cargo.toml** — Rust dependencies
- **README.md** — Human-readable project overview

## Common Dev Commands
```bash
cargo build                       # compile (with luck)
cargo test                        # verify (with more luck)
python3 build.py                  # mandatory pre-PR ritual
cargo clippy                      # let the linter judge you
cargo fmt                         # please do this
```

## Coding Conventions
- Idiomatic Rust; `cargo clippy -- -D warnings` should pass
- Error handling: `?` operator everywhere; no naked `unwrap()`
- Doc comments on all public items; inline comments for non-obvious logic
- Naming: `snake_case` for items/functions, `PascalCase` for types
- Test names describe the scenario: `test_player_cannot_take_nonexistent_item`

## Known Pitfalls
1. `python3 build.py` must be run before every PR — it generates diagnostic data the CI reads
2. The `.logd` artifact is machine-generated; editing it manually will cause undefined behavior
3. Adding a new command verb requires updates in parser.rs AND the test suite
4. Scene JSON schema changes are NOT backwards compatible — document in README
5. `cargo test` will fail if diagnostic artifacts are stale

## Where to Start
| Module | First File | Notes |
|--------|-----------|-------|
| Entrypoint | `src/main.rs` | 80 lines of honest work |
| Core engine | `src/engine.rs` | Where scenes become outcomes |
| Player state | `src/state.rs` | Inventory is everything |
| Items | `src/items.rs` | The fun part (and the bug part) |
| Parsing | `src/parser.rs` | Commands → actions |
| Build script | `build.py` | The gatekeeper |
| README | `README.md` | The truth, roughly |
