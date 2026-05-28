# Changelog

## [2026.5.17] — 2026-05-28

### Added
  - feat(auxiliary): add configurable fallback chains + main-agent safety net
  - feat(kanban): orchestrator-driven auto-decomposition on triage (#27572)
  - feat(status): show xAI OAuth login state in hermes status

### Fixed
  - fix(auxiliary): detect quota exhaustion as payment error; allow capacity-error fallback for explicit providers
  - fix(auth) fix a few cases where refresh tokens were not rotated.
  - fix(auth): stop replaying invalid Nous refresh tokens
  - fix(mcp): use module-level time so test patches do not race background sleepers
  - fix(xai): wire schema sanitizer into post-refactor build_api_kwargs
  - fix(schema_sanitizer): strip pattern/format from Responses-format tools for xAI compatibility
  - fix(run_agent): scope kimi tool-reasoning trigger to host, not model name substring
  - fix(model_switch): preserve explicit custom-provider model list when no api_key
  - fix(cli): include send in _BUILTIN_SUBCOMMANDS for plugin discovery gating
  - fix(aux): default OpenRouter auxiliary to gemini-3-flash-preview
  - fix(xai-oauth): echo code_challenge in token POST so PKCE exchange succeeds
  - fix(gateway): ignore inaccessible service path dirs
  - fix(tests): stabilize xai env and provider parity
  - fix(doctor): flag missing credentials for active openrouter provider
  - fix(docker): preload messaging gateway deps
  - fix(codex): allow kanban worker board writes
  - fix(mcp): prevent parallel-safe prefix collisions
  - fix(delegation): preserve configured_provider name when runtime returns 'custom'
  - fix(dashboard): respect HERMES_BASE_PATH in WebSocket URLs (#25547)
  - fix(web_server): pass proxy_headers=False to uvicorn.run so the dashboard's loopback gate sees the real connection peer
  - fix(gateway): use service restart path in Docker/Podman containers
  - fix(agent): honor provider timeout config in streaming API calls
  - fix(send_message): preserve Slack and Matrix thread targets resolved from channel directory
  - fix(transports): use monotonic deadlines in codex app-server turn loop
  - fix(doctor): show xAI OAuth login state in hermes doctor Auth Providers section
  - fix(doctor): isolate per-provider OAuth imports to prevent fallback regression
  - fix(doctor): suppress stale XAI_API_KEY issue when xAI OAuth is healthy
  - fix(tui): align composer cursorLayout with wrap-ansi to kill multiline cursor drift
  - fix(plugins/browser): carry forward requests.RequestException wrapping
  - fix(browser): self-review pass — dead-import, log levels, future-proofing
  - fix(browser): ensure plugin discovery before registry lookup; parity harness

### Changed
  - docs(fallback): document layered auxiliary fallback ladder
  - test(auxiliary): cover layered fallback (chain → main agent → warn)
  - chore(release): map zccyman noreply email for #26998
  - test(auxiliary): adapt eviction tests to capacity-error fallback
  - refactor(auth): mostly cleanups and style changes
  - refactor(auth): collapse Nous inference fallback controls
  - Switch to JWT token for inference against Nous, falling back to old opaque token on failure.
  - docs(messaging): clarify admin/user split and signal future gating (#27623)
  - test(tools_config): align post_setup parametrize with current browser provider catalog
  - test(gateway): include direct_messages_topic_id in telegram DM metadata assertions
  - test(gateway): accept trust_env in fake aiohttp ClientSession lambdas
  - chore(acp): bump registry manifest to 0.14.0 matching pyproject
  - test(xai-oauth): pin PKCE token-exchange wire format
  - chore(release): map vaddisrinivas for #26394 salvage
  - chore(release): map hehehe0803 email for #26212 salvage
  - test(delegation): add regression test for runtime missing 'provider' key
  - chore(release): AUTHOR_MAP entries for batch salvage group 6 contributors
  - chore(release): map QuenVix, Mind-Dragon, soynchux emails for Tier 4 salvage
  - chore: revert unrelated package-lock + nix hash churn to keep PR diff minimal
