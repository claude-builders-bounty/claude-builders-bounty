# TentOfTrials — Agent Instructions

Tone: We made a mess. Let's fix it politely.

## Purpose

TentOfTrials is a chaotic multiplayer party game built with Love2D. It's a collection of mini-games where agents (AI-controlled or human) compete in absurd challenges. The codebase is intentionally messy — we didn't have time to make it clean, only fast. Read before you commit.

---

## Tech Stack per Directory

### `conf/`
- **Language:** Lua
- **Purpose:** Project-wide configuration constants (canvas sizes, default settings, feature flags)
- **Read first:** `conf/settings.lua`
- **Warning:** Don't change defaults without checking `src/main.lua` — it hardcodes some of them.

### `diagnostic/`
- **Language:** Python + Lua
- **Purpose:** Build diagnostics, test runners, log collectors
- **Read first:** `diagnostic/run_tests.py`
- **Output:** `.logd` artifacts and optional `.json` summaries after each build
- **Warning:** These files are ignored by git. Do NOT commit them.

### `game/`
- **Language:** Lua
- **Purpose:** Core game loop, state machine, scene management
- **Read first:** `game/main.lua`
- **Subdirs:**
  - `game/scenes/` — Individual mini-game implementations
  - `game/entities/` — Player, projectile, and particle classes
- **Warning:** Scene loading is dynamic via `require()`. Renaming a scene file breaks boot.

### `lib/`
- **Language:** Lua (third-party)
- **Purpose:** Vendored dependencies (Love2D extensions, utility libs)
- **Read first:** `lib/README.md` (if it exists; otherwise assume broken)
- **Warning:** Do not modify vendored code. File bugs against upstream instead.

### `media/`
- **Language:** N/A (assets)
- **Purpose:** Images, sounds, fonts, particles
- **Subdirs:**
  - `media/sprites/` — PNG spritesheets
  - `media/audio/` — OGG/WAV files
  - `media/fonts/` — TTF/OTF
  - `media/particles/` — JSON particle configs
- **Warning:** Asset paths are case-sensitive on Linux. Match casing exactly.

### `src/`
- **Language:** Lua
- **Purpose:** Entry point and bootstrap logic
- **Read first:** `src/main.lua`
- **Warning:** This file does WAY more than a `main.lua` should. It loads conf, scans scenes, and initializes the engine. Look elsewhere for actual game logic.

### `tests/`
- **Language:** Lua (with busted)
- **Purpose:** Unit and integration tests for individual systems
- **Read first:** `tests/test_runner.lua`
- **Warning:** Many tests are skipped because they depend on mutable global state. Read before writing new ones.

### `tools/`
- **Language:** Python, Lua, Bash
- **Purpose:** Build scripts, asset pipelines, dev utilities
- **Read first:** `tools/build.py`
- **Warning:** This is the canonical build script. Everything flows through it.

---

## Common Dev Commands

```bash
# Full build + diagnostics (DO THIS AFTER EVERY CHANGE)
python3 build.py

# Run just the tests
python3 build.py --test

# Launch the game (requires Love2D installed)
love .

# Asset sanity check (reports missing/corrupt files)
python3 tools/check_assets.py

# Format Lua code (stylua required)
stylua src/ game/ conf/

# Clean diagnostic artifacts
rm -rf diagnostic/*.logd diagnostic/*.json
```

### Build-and-Diagnostic Workflow

**Always run `python3 build.py` after changes and include the diagnostic artifacts in your PR.**

1. Run `python3 build.py`
2. Locate the generated artifact: `diagnostic/build-<timestamp>.logd`
3. Copy it into your PR description (attach or paste path)
4. If `diagnostic/build-<timestamp>.json` exists, include that too
5. The build script checks: Lua syntax, asset integrity, test pass rate, and scene registration

---

## Coding Conventions

### Lua Style
- 4-space indentation (no tabs)
- Module-level functions use `Local:` prefix for private, `Public.` for exported
- Comments on every public function: `-- @param x number`, `-- @return boolean`
- Never mutate upstream tables — copy before modifying

### Naming
- Files: `snake_case.lua`
- Classes: `PascalCase`
- Private vars: `_private_name`
- Constants: `UPPER_CASE`

### Git
- Branches: `fix/<thing>`, `feat/<thing>`, `chore/<thing>`
- Commit messages: imperative mood, present tense ("Fix scene load order" not "Fixed")
- Squash before merge. We're not proud of our history.

### Tests
- Test files mirror source structure: `tests/test_<module>.lua`
- Use `busted` style (`describe`, `it`, `assert`)
- Mock Love2D globals with `mock_love.lua` — see `tests/helpers/`

---

## Known Pitfalls

### 1. Dynamic Scene Require
Scenes are loaded with `require(scene_path)` at runtime. If you rename a file, the game won't start. Always check `game/scenes/scene_registry.lua` when renaming anything.

### 2. Global State Leakage
Several modules write to `_G` or singleton tables during `init()`. Running tests out of order causes silent failures. Always call `reset_globals()` between test suites.

### 3. Asset Path Cases
`media/Sprites/foo.png` ≠ `media/sprites/foo.png` on ext4. Linux CI will fail while macOS dev works. Match cases.

### 4. Love2D Frame Time
The game uses fixed timestep physics but some mini-games read `dt` directly. If a game runs at 60fps on your machine but jitters on CI, check for `love.timer.getFrameTime()` usage inside event loops.

### 5. Config Hot-Reload Doesn't Work
Changes to `conf/settings.lua` require a full restart. The "reload" button just calls `love.event.quit()` and relaunches. Don't rely on hot-reload for config changes.

### 6. The Diagnostic Script is the Source of Truth
`build.py` checks things the README doesn't mention: scene count validation, audio channel limits, sprite sheet dimensions. If your PR fails CI but passes locally, run `python3 build.py` and read the `.logd` output carefully.

### 7. Stylua Will Rewrite Your Commas
Trailing commas in Lua tables are supported but stylua may move them. Run `stylua` before committing or your PR will fail formatting checks.

---

## Where to Start

| Module | Read First | Why |
|--------|-----------|-----|
| **Game Boot** | `src/main.lua` | Understands the load sequence |
| **Scene System** | `game/scenes/scene_registry.lua` | Every game lives here |
| **Player Entity** | `game/entities/player.lua` | Base class all entities extend |
| **Conf System** | `conf/settings.lua` | Defaults that everything overrides |
| **Build Pipeline** | `tools/build.py` | CI, tests, diagnostics — all one script |
| **Tests** | `tests/test_runner.lua` | How to run and extend the suite |
| **Assets** | `media/README.md` | Sprite sheet format specs |

---

## PR Template

Use `.github/pull_request_template.md` for all submissions. It includes mandatory sections for diagnostic artifacts.

---

*Last updated: 2025. We still haven't fixed the collision detection.*
