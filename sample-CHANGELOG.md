# Changelog

All notable changes to **hermes-agent** are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/).

---

## [1.0.0] - 2026-06-05

_Commits since v2026.5.29 (1242 total)_

### Added

- universal task-completion guidance + local Python toolchain probe (#34340) (a4d8f0f)
-  tests/run_agent/test_run_agent.py — new classes  ()
- integrate NVIDIA/skills as a trusted skills hub tap (9992e32)
- approval: add docker restart/stop/kill to DANGEROUS_PATTERNS (#33438) (54bf798)
- Add iputils-ping (ping) to Docker image (#32015) (593e4b4)
- default_assignee fallback + per-profile concurrency cap (#27145, #21582) (#34244) (3b6347a)

### Fixed

- close three blocked/iteration-exhausted handling gaps (#29747) (592a4ff)
- bridge worker runtime activity to board heartbeat (#31752) (bc31ee5)
- tell workers not to use clarify; route to kanban_block instead (#32167) (40217aa)
- STATUS_DEAD for terminal OAuth failures (#32849) (#34412) (86a389f)
- add --reason flag to unblock for symmetry with block (#30897) (ae6817f)
- add bws_cache.json to file_safety read guard (4126da6)
- preserve Ctrl+J newlines in Ghostty (cf8862c)
- deepcopy tools_for_api before in-place mutation (#27907) (1386a7e)
- keep Telegram topic bindings aligned with compression children (#34409) (db96fc6)
- auto-join Docker socket group for docker-in-docker backend (ec7736f)
- accept PUID/PGID as aliases for HERMES_UID/HERMES_GID (#25872) (#34401) (4808321)
- rewrite Camofox Docker loopback URLs (#25541) (a0fc3df)
- restore side-effect imports in test files (test_kanban_tools, test_command_guards) (00b8204)
- re-export pruned names for tests that mock.patch or from-import them (e371bf5)
- recover gateway.log handler from external rotation (#34349) (75d2c08)
- prevent session-id fork from concurrent compressions (#34351) (a30480b)
- bridge Tailwind --font-sans to --theme-font-sans (#20406) (28bb7e0)
- Fix Telegram DM topic text batch keying (5407d25)
- skip credential/skills/cache mounts when source is invalid (#24490) (#34331) (40fa0c1)
- CLI dispatch honors max_in_progress/max_spawn from config; swap missing 'avoid-ai-writing' skill for bundled humanizer (#33488, #29415) (#34337) (69b74c1)
- cap mimo-v2.5-pro max_tokens at 131072 (8cf6b3d)
- guard Path.home() against PermissionError in has_direct_modal_credentials (#33528) (44df520)
- broaden deterministic compression fallback coverage (6dc068e)
- preserve context when summary generation fails (e785c0a)
- honor PIPEWIRE_REMOTE in PortAudio fallback checks (#33473) (c834624)
- share /api/* public allowlist between legacy and OAuth gates (a618789)
- cleanup_vm() default honors persist mode (don't kill container on session close) (2f0f03c)
- persist-mode cleanup is no-op; add force_remove kwarg (#20561) (5c2170a)
- startup orphan reaper for crashed-process containers (d77d877)
- reuse containers across processes + fix cleanup leaks (ac8e238)
- tag containers with hermes-agent labels for identification (8d129d0)

### Changed

- map seppe@fushia.be to GitHub login (71ae98b)
- clarify why F401 re-exports stay (f61fd59)
- prune unused imports and duplicate import redefinitions (66827f8)
- generalize topic recovery via adapter hook (1005361)
- add network egress isolation guide for Docker deployments (#26385) (90f0f32)
- refresh user-guide page for s6-overlay reality (42612aa)
- document new persist-across-processes contract and orphan reaper (#20561) (3c6e70a)

### Other

- test(kanban): update iteration-exhaustion tests for #29747 gap 2 (7d10105)
-  Test surface  ()
- --- ()
-  tests/tools/test_env_probe.py  ()
-  TestToolUseEnforcementConfig  ()
-  TestBuildSystemPrompt  ()
-  TestInvalidateSystemPrompt  ()
-  tests/agent/test_prompt_builder.py  ()
-  tests/hermes_cli/  ()
-  E2E AIAgent build (broken env)  ()
-  E2E AIAgent build (clean env)  ()
- Revert "feat(skills): integrate NVIDIA/skills as a trusted skills hub tap" (bfecfab)
- test: cover fallback dropped-turn handoff (042c1d6)
-  grep ((a foll)
- test(tui_gateway): stop reloading server module in fixture teardown (#34217) (300140e)

---

_Generated on 2026-06-05T08:34:29Z by changelog.sh_
