# Changelog

## [Unreleased] - 2026-06-14

> Auto-generated from [git history](https://github.com/brandonkindred/Khala-Agentic-AI-Teams)


### Added

- Add issue-dependency indicator to the coding team github issues picker (#787) ([`03fad1f`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/03fad1f))
- Add code review panel: run reviewer agents on a github pr (#795) ([`d56c75f`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/d56c75f))
- Add cognitivecontext facade (cognition step 8) (#835) ([`2ffacfc`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/2ffacfc))
- Add live code-review progress, current-activity reporting, and stall detection (#847) ([`ecdca02`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/ecdca02))
- Add code review guide for task-changed files and prevent input truncation ([`7fb5b0c`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/7fb5b0c))
- Address review feedback: translate to english, fix script bugs, add detail ([`144e9a8`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/144e9a8))

### Fixed

- Fix coding-team tech lead review deadlock; route rejections back to the engineer (#776) ([`1317d0d`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/1317d0d))
- Fix coding-team re-implementation/re-planning loop (#778) ([`5d38a9f`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/5d38a9f))
- Fix rule-probe exit synthesis so stop-loss no longer pre-empts the targeted exit (#790) ([`4e8aeaf`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/4e8aeaf))
- Drop arbitrary 1-3 word cap from naming convention rules (#865) ([`34e5e56`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/34e5e56))

### Changed

- Harden crypto -usd canonicalization against compound/empty suffixes (#773) ([`24801c0`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/24801c0))
- [cognition][step 7] tools layer (#766) ([`25b7d56`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/25b7d56))
- Coding team: active repo-inspection tools (list_files / read_file) for the senior swe agent (#780) ([`51adae7`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/51adae7))
- Coding team: stop truncating llm inputs (#784) ([`680638a`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/680638a))
- Coding team: human-in-the-loop decision gate (spec-023) (#782) ([`b38c0f0`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/b38c0f0))
- Consolidate background-heartbeat scaffolding into a shared helper (#785) ([`915c653`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/915c653))
- Stop truncating senior swe repo-context briefing (#792) ([`b9912f9`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/b9912f9))
- Replace synthetic-data rule validation with deterministic math in strategy lab (#797) ([`df704d8`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/df704d8))
- Exponential backoff for 429 rate limits (300s first retry) (#789) ([`dff1612`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/dff1612))
- Knowledge-graph layer for agent cognition (neo4j + graphiti) (#805) ([`7268675`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/7268675))
- Make max_position_pct a pre-entry sizing bound for all engine sizing kinds (#814) ([`9561dda`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/9561dda))
- Strategy lab: harden refinement agent against unparseable llm output (#809) ([`2c48ed1`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/2c48ed1))
- Coding team: surface agent thinking tokens in the ui (#811) ([`d79e18b`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/d79e18b))
- Consolidate per-trade loss into max_position_pct; decouple stop_loss (#817) ([`8639c83`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/8639c83))
- Move env-var reference detail out of claude.md into docs/env_vars.md (#829) ([`2fd02a9`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/2fd02a9))
- Dedupe defensive-parsing notes in docs/env_vars.md (#832) ([`b034960`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/b034960))
- Agent cognition graph sync: re-ingest rollup summaries per version (#820) ([`bd0c3bf`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/bd0c3bf))
- Extract barpredicate ir into a dedicated module with snapshot tests (#821) ([`09d1603`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/09d1603))
- Strategy lab: forward the strands transport timeout instead of dropping it (#834) ([`dd2cf13`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/dd2cf13))
- Code review page: inline pr expansion + persisted per-pr review history (#831) ([`a7eed05`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/a7eed05))
- Collapse duplicate json extractors onto shared string-aware helper (#838) ([`a6c2129`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/a6c2129))
- Slim claude.md to core guidance with pointers to detailed docs (#844) ([`9e93a08`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/9e93a08))
- Llm client: proof-of-change thinking-downgrade retry for empty responses (#839) ([`40949f1`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/40949f1))
- Cognition step 10: invoke gate — idempotent inject-on-invoke / writeback-on-return at the boundary (#841) ([`99478ae`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/99478ae))
- [cognition][step 11] ledger hygiene: gc terminal runs in the central scheduler (#853) ([`65832b2`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/65832b2))
- Code review: bounded per-file chunking with always-on map-reduce coordinator (#852) ([`60d4618`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/60d4618))
- Cognition step 12: operator hitl api — memory inspect, author tagging, gateway gating (#854) ([`17af193`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/17af193))
- [cognition][step 13] seed rule packs install on first provision + config/env docs (#856) ([`8c39bbe`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/8c39bbe))
- Findings-only synthesis pass for the merged review summary (stage 2) (#855) ([`5d2819b`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/5d2819b))
- Restore structured block fields on replay of blocked runs (#857) ([`348e8f5`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/348e8f5))
- [cognition][step 14] generator wiring: stamp + consume the cognition core (agentic team) (#858) ([`1a63f4c`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/1a63f4c))
- Merge branch 'main' into docs/code-review-guide ([`b0876ce`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/b0876ce))
- Merge branch 'main' into docs/code-review-guide ([`df12191`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/df12191))

### Removed

- Remove genuine string truncation from strategy lab llm prompts (#793) ([`878b9ab`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/878b9ab))
- Strategy lab: remove expected-trade-count anomaly gate (#819) ([`10c171e`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/10c171e))
- Remove spec-unaware diversification warning from backtest anomaly gate (#828) ([`16eaf74`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/16eaf74))
- Remove issue-number refs and phase-history narration from claude.md (#840) ([`fe315fc`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/fe315fc))
- Remove max-drawdown constraint; stop llm reviewer vetoing on sizing/risk math (#869) ([`94fafe9`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/94fafe9))

### Documentation

- Add agent architecture document (#781) ([`a21d905`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/a21d905))
- De-duplicate claude.md sections covered by linked readmes (#836) ([`42a5d86`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/42a5d86))
- Relocate strategy_lab_* knob reference to strategy lab readme (#837) ([`34a1172`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/34a1172))

### CI/CD

- Run shared_neo4j + agent_cognition suites under the 90% coverage gate (#815) ([`55bf135`](https://github.com/brandonkindred/Khala-Agentic-AI-Teams/commit/55bf135))
