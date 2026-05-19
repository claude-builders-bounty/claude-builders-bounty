# Changelog

All notable changes to this project will be documented in this file.

## Unreleased (changes since v2.0-m1-rc0)

### Added

- fix(uploads): add Windows support for safe symlink-protected uploads (#2794) ([0d1053ca](https://github.com/bytedance/deer-flow/commit/0d1053ca)) — yangyufan, 2026-05-09
- feat(debug): print presented file paths with physical resolution (#2825) ([4063dd71](https://github.com/bytedance/deer-flow/commit/4063dd71)) — He Wang, 2026-05-09
- fix(packaging): add postgres extra for store/checkpointer supportFix postgres extra install guidance (#2584) ([7caf03e9](https://github.com/bytedance/deer-flow/commit/7caf03e9)) — KiteEater, 2026-05-09
- feat: static system prompt with DynamicContextMiddleware for prefix-cache optimization (#2801) ([c1b7f1d1](https://github.com/bytedance/deer-flow/commit/c1b7f1d1)) — DanielWalnut, 2026-05-09
- fix(tools): introduce Runtime type alias to eliminate Pydantic serialization warning (#2774) ([7de9b582](https://github.com/bytedance/deer-flow/commit/7de9b582)) — He Wang, 2026-05-08
- feat(loop-detection): make loop detection configurable with per-tool frequency overrides (#2711) ([daa3ffc2](https://github.com/bytedance/deer-flow/commit/daa3ffc2)) — Tao Liu, 2026-05-07
- feat(agent): add custom-agent self-updates with user isolation (#2713) ([59c4a3f0](https://github.com/bytedance/deer-flow/commit/59c4a3f0)) — yangzheli, 2026-05-05

### Fixed

- fix(persistence): reuse token usage model grouping expression (#2910) ([2a1ac06b](https://github.com/bytedance/deer-flow/commit/2a1ac06b)) — Eilen Shin, 2026-05-13
- fix(agents): make update_agent honor runtime.context user_id like setup_agent (#2867) ([68d8caec](https://github.com/bytedance/deer-flow/commit/68d8caec)) — Xinmin Zeng, 2026-05-12
- fix(middleware): Handle invalid tool calls in dangling pairing middleware (#2890) (#2891) ([20d2d2b3](https://github.com/bytedance/deer-flow/commit/20d2d2b3)) — Nan Gao, 2026-05-12
- fix(harness): wrap async-only config tools for sync client execution (#2878) ([bedbf229](https://github.com/bytedance/deer-flow/commit/bedbf229)) — AochenShen99, 2026-05-11
- fix(runtime): persist run message summaries (#2850) ([2eb11f97](https://github.com/bytedance/deer-flow/commit/2eb11f97)) — Nan Gao, 2026-05-11
- fix(nginx): defer CORS to gateway allowlist (#2861) ([c3bc6c7c](https://github.com/bytedance/deer-flow/commit/c3bc6c7c)) — AochenShen99, 2026-05-11
- fix(subagents): consolidate system_prompt and skills into single SystemMessage (#2701) ([813d3c94](https://github.com/bytedance/deer-flow/commit/813d3c94)) — Willem Jiang, 2026-05-11
- fix(harness): reset local sandbox singleton with provider lifecycle (#2834) ([2b5bece7](https://github.com/bytedance/deer-flow/commit/2b5bece7)) — KiteEater, 2026-05-11
- fix(tools): make write_file append discoverable in model-facing schema (#2843) ([30a58462](https://github.com/bytedance/deer-flow/commit/30a58462)) — Maz Benoscar, 2026-05-10
- fix: bucket subagent token usage into parent run totals (#2838) ([9892a7d4](https://github.com/bytedance/deer-flow/commit/9892a7d4)) — YuJitang, 2026-05-10
- fix(scripts): preserve uv extras across `make dev` restarts (#2754) (#2767) ([94da8f67](https://github.com/bytedance/deer-flow/commit/94da8f67)) — Xinmin Zeng, 2026-05-10
- fix(lint): remove duplicate is_dynamic_context_reminder definition (#2837) ([08ee7ade](https://github.com/bytedance/deer-flow/commit/08ee7ade)) — DanielWalnut, 2026-05-09
- fix: keep new agent bootstrap in user scope (#2784) ([1c96a6af](https://github.com/bytedance/deer-flow/commit/1c96a6af)) — Eilen Shin, 2026-05-09
- fix: use backend thread token usage for header total (#2800) ([41741608](https://github.com/bytedance/deer-flow/commit/41741608)) — YuJitang, 2026-05-09
- fix(harness): preserve dynamic context across summarization (#2823) ([881ff712](https://github.com/bytedance/deer-flow/commit/881ff712)) — DanielWalnut, 2026-05-09
- fix title generation with dynamic context reminder (#2830) ([f76e4e35](https://github.com/bytedance/deer-flow/commit/f76e4e35)) — DanielWalnut, 2026-05-09
- Fix duplicate gateway upload filenames (#2789) ([7a3c58a7](https://github.com/bytedance/deer-flow/commit/7a3c58a7)) — ChenglongZ, 2026-05-09
- fix(nignx):resolve CSRF auth failure on non-standard ports (#2796) ([70737af7](https://github.com/bytedance/deer-flow/commit/70737af7)) — Willem Jiang, 2026-05-08
- fix(task): remove max_turns parameter from task tool interface (#2783) ([2b1fcb3e](https://github.com/bytedance/deer-flow/commit/2b1fcb3e)) — DanielWalnut, 2026-05-08
- fix(events): serialize structured db event content (#2762) ([37db6893](https://github.com/bytedance/deer-flow/commit/37db6893)) — Eilen Shin, 2026-05-08
- fix(sandbox): disable msys path conversion (#2766) ([bd45cb28](https://github.com/bytedance/deer-flow/commit/bd45cb28)) — Eilen Shin, 2026-05-08
- fix(middleware): sync raw tool call metadata (#2757) ([5fd0e6ac](https://github.com/bytedance/deer-flow/commit/5fd0e6ac)) — Eilen Shin, 2026-05-08
- fix: dedupe token usage aggregation by message id (#2770) ([530bda71](https://github.com/bytedance/deer-flow/commit/530bda71)) — YuJitang, 2026-05-08
- fix(chat): prevent first user message from being swallowed in new conversations (#2731) ([6c220a9a](https://github.com/bytedance/deer-flow/commit/6c220a9a)) — Willem Jiang, 2026-05-07
- fix(frontend): defer thread id to onStart to avoid 404 on new chat (#2749) ([27559f36](https://github.com/bytedance/deer-flow/commit/27559f36)) — Xinmin Zeng, 2026-05-07
- fix(skills): enforce allowed-tools metadata (#2626) ([cef42243](https://github.com/bytedance/deer-flow/commit/cef42243)) — AochenShen99, 2026-05-07
- fix(channels): authenticate gateway command requests (#2742) ([1336872b](https://github.com/bytedance/deer-flow/commit/1336872b)) — Eilen Shin, 2026-05-06
- fix(config): reset config-backed singletons on hot reload (#2588) ([4ead2c6b](https://github.com/bytedance/deer-flow/commit/4ead2c6b)) — KiteEater, 2026-05-06
- fix(loop-detection): keep tool-call pairing on warn injection (#2724) (#2725) ([e8675f26](https://github.com/bytedance/deer-flow/commit/e8675f26)) — Nan Gao, 2026-05-05
- fix: Supplement list_running in RemoteSandboxBackend (#2716) ([680187dd](https://github.com/bytedance/deer-flow/commit/680187dd)) — Xun, 2026-05-05
- fix(frontend): restore localhost fallback for getGatewayConfig in prod mode (#2705) (#2718) ([aded753d](https://github.com/bytedance/deer-flow/commit/aded753d)) — Xinmin Zeng, 2026-05-05
- fix(docker):force ngix to resolve upstream names at request time (#2717) ([028493bf](https://github.com/bytedance/deer-flow/commit/028493bf)) — Willem Jiang, 2026-05-05
- fix(channels): preserve clarification conversation history across follow-up turns (#2444) ([8e48b7e8](https://github.com/bytedance/deer-flow/commit/8e48b7e8)) — Willem Jiang, 2026-05-04

### Changed

- perf(harness): push thread metadata filters into SQL (#2865) ([e9deb6c2](https://github.com/bytedance/deer-flow/commit/e9deb6c2)) — He Wang, 2026-05-12
- docs: clarify LangGraph compatibility entrypoints (#2914) ([506be8bf](https://github.com/bytedance/deer-flow/commit/506be8bf)) — AochenShen99, 2026-05-12
- docs: document auth design and user isolation (#2913) ([f734e14d](https://github.com/bytedance/deer-flow/commit/f734e14d)) — greatmengqi, 2026-05-12
- docs: align runtime docs with gateway mode (#2868) ([84f88b66](https://github.com/bytedance/deer-flow/commit/84f88b66)) — Eilen Shin, 2026-05-12
- chore(deps): bump next from 16.1.7 to 16.2.6 in /frontend (#2899) ([00096554](https://github.com/bytedance/deer-flow/commit/00096554)) — dependabot[bot], 2026-05-12
- chore(deps): bump urllib3 from 2.6.3 to 2.7.0 in /backend (#2898) ([1f978393](https://github.com/bytedance/deer-flow/commit/1f978393)) — dependabot[bot], 2026-05-12
- docs: clarify token usage accounting semantics (#2845) ([e82b2fb4](https://github.com/bytedance/deer-flow/commit/e82b2fb4)) — YuJitang, 2026-05-11
- chore(deps): bump langchain-core from 1.3.2 to 1.3.3 in /backend (#2807) ([1edc9d9f](https://github.com/bytedance/deer-flow/commit/1edc9d9f)) — dependabot[bot], 2026-05-09
- chore(deps): bump uuid from 10.0.0 to 14.0.0 in /frontend (#2802) ([41b04a55](https://github.com/bytedance/deer-flow/commit/41b04a55)) — dependabot[bot], 2026-05-09
- chore(deps): bump python-multipart from 0.0.26 to 0.0.27 in /backend (#2799) ([109490da](https://github.com/bytedance/deer-flow/commit/109490da)) — dependabot[bot], 2026-05-08
- chore(deps): bump mako from 1.3.11 to 1.3.12 in /backend (#2798) ([14c0a32e](https://github.com/bytedance/deer-flow/commit/14c0a32e)) — dependabot[bot], 2026-05-08

### Other

-   feat(run): Propagates `model_name` from the gateway request through the runtime and persistence stack to the SQLite database. (#2775) ([de253e4a](https://github.com/bytedance/deer-flow/commit/de253e4a)) — Yi Tang, 2026-05-11
- enable token usage by default (#2841) ([5127f08e](https://github.com/bytedance/deer-flow/commit/5127f08e)) — YuJitang, 2026-05-10
- [codex] fix follow-up suggestions layout (#2836) ([dfa4eb0c](https://github.com/bytedance/deer-flow/commit/dfa4eb0c)) — DanielWalnut, 2026-05-10
- [security] fix(auth): reject cross-site auth POSTs (#2740) ([2b0e62f6](https://github.com/bytedance/deer-flow/commit/2b0e62f6)) — Hinotobi, 2026-05-07

