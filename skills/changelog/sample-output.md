# Changelog

> Generated for **NousResearch/hermes-agent**
> Commits since `v2026.5.7`

## [desktop-pr20059-installers] — 2026-05-11

### ✨ Added

- add self-healing system (circuit breaker, cache, error processing, structured memory) ([`762729f`](https://github.com/NousResearch/hermes-agent/commit/762729f1e21708737bcd7be3f73481e842ee379b))
- /goal checklist + /subgoal user controls (#23456) ([`404640a`](https://github.com/NousResearch/hermes-agent/commit/404640a2b752f502825dc8b26212204fa890d495))
- make /handoff actually transfer the session live ([`00ce5f0`](https://github.com/NousResearch/hermes-agent/commit/00ce5f04d9cfad2e30d5e08e7a6bf135f6e53030))
- add /handoff command for cross-platform session transfer ([`878611a`](https://github.com/NousResearch/hermes-agent/commit/878611a79dfaa5435f2d904b3fb20539dea6c5a7))
- per-platform admin/user split for slash commands (salvage of #4443) (#23373) ([`a282434`](https://github.com/NousResearch/hermes-agent/commit/a282434301fbc193ecfea046953f93d8edced92c))
- shutdown forensics — non-blocking diag, per-phase timing, stale-unit warning (#23285) ([`cede612`](https://github.com/NousResearch/hermes-agent/commit/cede612987839d55aa8d5a65b87d36649d626724))
- aggregate all toolset-name typos in skills before raising ([`1f5983c`](https://github.com/NousResearch/hermes-agent/commit/1f5983c4c8cf9227266fcbff88ca1c91bbb4d344))
- native <details> collapse + skip empty metadata ([`a91e5a8`](https://github.com/NousResearch/hermes-agent/commit/a91e5a87594b4ba0ad5e215d741ddab4b8e5cec7))
- localize all gateway commands + web dashboard, add 8 new locales (16 total) (#22914) ([`c391684`](https://github.com/NousResearch/hermes-agent/commit/c39168453d019e758faab7fbe67cd939f8b56d0b))
- run any LLM call from inside a plugin via ctx.llm (#23194) ([`5aa755e`](https://github.com/NousResearch/hermes-agent/commit/5aa755e4e63cf84c048f85e0ac016138f36491d0))
- hint at `hermes curator pin` in the rename block (#23212) ([`7312f7f`](https://github.com/NousResearch/hermes-agent/commit/7312f7f849e892cbe6534e5e6cc32ae5b6d7a474))
- add LINE Messaging API platform plugin (#23197) ([`50f9fee`](https://github.com/NousResearch/hermes-agent/commit/50f9fee988b67c14a208ee75630ade6277f3d01f))
- add upstream + timing diagnostics to drop log (#23005) ([`126cbff`](https://github.com/NousResearch/hermes-agent/commit/126cbffb8ad5a9f0fb9bd99a1569d36c40a570fe))
- vision_analyze returns pixels to vision-capable models, not aux text (#22955) ([`3800972`](https://github.com/NousResearch/hermes-agent/commit/3800972dd05eabed8d75bfc4c0f5d532d85dafe2))
- show rename map in user-visible summary (#22910) ([`4375b82`](https://github.com/NousResearch/hermes-agent/commit/4375b82cd9b6173a58456db600aa1f4ead21af6f))
- richer info panels on the Skills Hub for built-in + optional skills (#22905) ([`5971a4e`](https://github.com/NousResearch/hermes-agent/commit/5971a4e0925f88fc6afa4f6ebef743d852d46810))
- wire Pareto Code router with min_coding_score knob (#22838) ([`c7f0aab`](https://github.com/NousResearch/hermes-agent/commit/c7f0aab9497bafa07695388e916a8466e90e6efa))
- add Telegram notification mode to suppress intermediate push notifications ([`236f3b0`](https://github.com/NousResearch/hermes-agent/commit/236f3b052171754884064a641da349f0455fe8bd))
- pass reasoning.effort to xAI Responses API ([`cd712b1`](https://github.com/NousResearch/hermes-agent/commit/cd712b176a9be62b0d1e70a865c1226bd1b0e6a3))
- add codex preset for built-in MCP server discovery ([`9aefa74`](https://github.com/NousResearch/hermes-agent/commit/9aefa74a9f572e123095287e64f559238272f807))
- show user's actual concurrency / spawn-depth limits in tool description (#22694) ([`1f4200d`](https://github.com/NousResearch/hermes-agent/commit/1f4200debf8c34af10cc2c5a1acde31917f970a7))
- HERMES_PLUGINS_DEBUG=1 surfaces plugin discovery logs (#22684) ([`7969401`](https://github.com/NousResearch/hermes-agent/commit/79694018f89e9c6c75cad11172855ca1de345c47))
- confirm prompt for destructive slash commands (#4069) (#22687) ([`b9c0011`](https://github.com/NousResearch/hermes-agent/commit/b9c001116e2bc6e2b112d9338ab6ce10040896a0))
- add standalone_sender_fn for out-of-process cron delivery ([`93e25ce`](https://github.com/NousResearch/hermes-agent/commit/93e25ceb1326770b369b8c4151cd3b9c3cdc0688))
- recognise Shift+Enter as a newline key ([`f5b635f`](https://github.com/NousResearch/hermes-agent/commit/f5b635f6ab6d81499d8940f7ab650b6e11956272))
- clean up User env, PATH, Scheduled Task, and portable tooling ([`35fce76`](https://github.com/NousResearch/hermes-agent/commit/35fce7699ef61eb11963a498c5489b4e7c7a508b))
- psutil for PID/process management + Windows footgun checker ([`cc38282`](https://github.com/NousResearch/hermes-agent/commit/cc38282b04d997468db782caa3443387fd454359))
- gateway as a Scheduled Task + Startup-folder fallback ([`9c263fb`](https://github.com/NousResearch/hermes-agent/commit/9c263fbf8a622566f0831b8b727ded31b67c64af))
- declare platforms frontmatter for all 79 undeclared built-in skills ([`98db898`](https://github.com/NousResearch/hermes-agent/commit/98db898c0bd4df0b09a5830b6a18a069c771e67c))
- declare platforms frontmatter for all 63 undeclared skills ([`db22efb`](https://github.com/NousResearch/hermes-agent/commit/db22efbe88bd822331a3220b9020e6d4800c37d1))
- gate 7 Linux/macOS-only skills from Windows via platforms frontmatter ([`b18b17f`](https://github.com/NousResearch/hermes-agent/commit/b18b17f9c9de0f43975a8987821f37be954603a2))
- Ctrl+Enter inserts newline on Windows Terminal ([`d183804`](https://github.com/NousResearch/hermes-agent/commit/d1838041e52499094b501056172cc7322233a7bc))
- enrich system-prompt environment hints with host + terminal-backend info ([`40e7a71`](https://github.com/NousResearch/hermes-agent/commit/40e7a71c350121a94a67d44e9f1e09239d6196d1))
- close remaining POSIX-only landmines — TUI crash, kanban waitpid, AF_UNIX sandbox, /bin/bash, npm .cmd shims, cwd tracking, detach flags ([`e93bfc6`](https://github.com/NousResearch/hermes-agent/commit/e93bfc6c93bfa6f9edd02629a03f717fc29ce013))
- bundle portable MinGit instead of relying on winget ([`b7fe7ed`](https://github.com/NousResearch/hermes-agent/commit/b7fe7ed7bd1740b01315c4bd15b254aa738124e5))
- close native-Windows install gaps — crash-free startup, UTF-8 stdio, tzdata dep, docs ([`9de893e`](https://github.com/NousResearch/hermes-agent/commit/9de893e3b078e7ef51437af1ce6743d96a103c6d))
- support attaching to an existing gateway (#21978) ([`1997b3b`](https://github.com/NousResearch/hermes-agent/commit/1997b3baf81440f5afd4b7963a23663e85557d18))
- add plugin runtime and operator cli ([`07bbd93`](https://github.com/NousResearch/hermes-agent/commit/07bbd933370882e8977e69f2d19b6f26a66ed271))
- background focus-safe backend — set_value, structured windows, MIME detection ([`e31f3b3`](https://github.com/NousResearch/hermes-agent/commit/e31f3b3c56e33ba96213de4312367b4f61a745ed))
- cua-driver backend, universal any-model schema ([`850413f`](https://github.com/NousResearch/hermes-agent/commit/850413f1203f02c42ac6b9fd21ff86a2402a974e))
- shareable profile distributions via git (#20831) ([`f209a35`](https://github.com/NousResearch/hermes-agent/commit/f209a358592fe9613fc11e779d80b3b4d4da4f45))
- watchers skill — poll RSS / HTTP JSON / GitHub via cron no-agent (#21881) ([`ea8e608`](https://github.com/NousResearch/hermes-agent/commit/ea8e608821b18f1cfa2f45c65542f7bc6c2f7b96))
- Drive write ops + Docs/Sheets create/append (#21895) ([`e43d2fe`](https://github.com/NousResearch/hermes-agent/commit/e43d2fe5205ef3a2027924f14380a6af08bda35e))
- bootstrap auth.json from env on first boot ([`5643c29`](https://github.com/NousResearch/hermes-agent/commit/5643c297901312d817713a8cc870a28a439e3114))
- segment turns with rule above non-first user msgs; trim ticker dead space (#21846) ([`42f9234`](https://github.com/NousResearch/hermes-agent/commit/42f9234da34e59e456240cb3ddb8bad1995427a4))
- routing intent — deliver=all fans out to every connected channel (#21495) ([`486b14b`](https://github.com/NousResearch/hermes-agent/commit/486b14b423e85120691e445df7bfc57f093459a0))
- add tooltips and docs link across dashboard (#21541) ([`7d66d30`](https://github.com/NousResearch/hermes-agent/commit/7d66d30d774e87b49cbe48af20c9904c9befb97e))
- add `specify` — auxiliary LLM fleshes out triage tasks (#21435) ([`24d48ff`](https://github.com/NousResearch/hermes-agent/commit/24d48ffb8294d6f13f0a6660dfff376d886d0466))
- add Brave Search (free tier) and DDGS search providers ([`04193cf`](https://github.com/NousResearch/hermes-agent/commit/04193cf71c2c208b747870f845c7c2539d50455f))
- pass image file attachments through as image_url parts ([`7e2af0c`](https://github.com/NousResearch/hermes-agent/commit/7e2af0c2e8727b3b01b974cb9bf8f0886ee00aac))

### 🐛 Fixed

- evict cached client on timeout/connection error (#23482) ([`e5bce32`](https://github.com/NousResearch/hermes-agent/commit/e5bce320db1a10f7f78f3d0811f1f040fb1e00ef))
- normalize dm threads and retry control sends ([`737314f`](https://github.com/NousResearch/hermes-agent/commit/737314fe914cea60e6df8dc50fbb5c917f0b66d3))
- use UTF-16 length for Telegram stream consumer message splitting ([`c0da5d0`](https://github.com/NousResearch/hermes-agent/commit/c0da5d09a67b97094b6db9b2dfd20657b043a273))
- drive _prompt_text_input directly when off main thread (#23454) ([`c5f1f86`](https://github.com/NousResearch/hermes-agent/commit/c5f1f863acd49c92d9fbe92550115d51dd5181d0))
- clarify kanban_complete phantom-card retry guidance ([`62cfe79`](https://github.com/NousResearch/hermes-agent/commit/62cfe79e9368ecb0fe3c329179984b7d76f35edb))
- pass source.thread_id explicitly on auto-reset notice (carve-out of #7404) ([`2f00559`](https://github.com/NousResearch/hermes-agent/commit/2f00559d9e7358fd5eb5605707db5aefdfbe86d9))
- right-click copies selection, only pastes when no selection ([`a2920b1`](https://github.com/NousResearch/hermes-agent/commit/a2920b17623e2903bd9481721f60c2bf26c6f97a))
- extend stale claim instead of killing live worker ([`88588b6`](https://github.com/NousResearch/hermes-agent/commit/88588b6159953407420d3778c4a5e87fecd0a30f))
- omit reasoning.effort for grok models that reject it (#23435) ([`d6e1fad`](https://github.com/NousResearch/hermes-agent/commit/d6e1fadbf59085214e3f97e231d3c7f0d1643941))
- preserve thread routing on overflow first-send path ([`e164a9c`](https://github.com/NousResearch/hermes-agent/commit/e164a9c1ed781ab5e6e597ec74e9a933b81b7acd))
- stream consumer first message drops thread context ([`ff14666`](https://github.com/NousResearch/hermes-agent/commit/ff14666cdc02ebad18a15de57ded4e9ec7d9f563))
- only mark final response sent when split-overflow chunks actually land (#23420) ([`6636fec`](https://github.com/NousResearch/hermes-agent/commit/6636fecd473b13a99f69fc2f742d7b2ce788c324))
- deduplicate kanban notifications for blocked/gave_up states ([`a96dd54`](https://github.com/NousResearch/hermes-agent/commit/a96dd5487274cbb678847b333d463d2075a6cc6a))
- align fallback delete with sibling style + add regression tests ([`ec1fad3`](https://github.com/NousResearch/hermes-agent/commit/ec1fad3449c871898d71200acabf9dd161e1d5b4))
- delete partial message after fallback send on flood control ([`4eb8479`](https://github.com/NousResearch/hermes-agent/commit/4eb8479ebdce46712d00694a82faf2aa1675497b))
- unbreak install + update on Windows (#23394) ([`4d9dcbc`](https://github.com/NousResearch/hermes-agent/commit/4d9dcbc47ae40ad1ddc2f02221fe7283c65106b6))
- drop models being retired May 15, 2026 from pickers (#23291) ([`5942093`](https://github.com/NousResearch/hermes-agent/commit/594209389d9bd4ca2ec1acf61c4b239facf330e2))
- tone down completed-run metadata panel (#19548) ([`0e0ddaa`](https://github.com/NousResearch/hermes-agent/commit/0e0ddaac8fa07494ef797b2f6293c0701fcff62e))
- guard task_age against corrupt created_at values like '%s' ([`061a183`](https://github.com/NousResearch/hermes-agent/commit/061a18300837351751b3c6028597d25ef5fe6665))
- correct dispatcher spawn module name + PATH-first lookup ([`62b1c74`](https://github.com/NousResearch/hermes-agent/commit/62b1c74cbc62cde1204fecc3c2682d312b995876))
- use sys.executable -m hermes for dispatcher spawn ([`d3db672`](https://github.com/NousResearch/hermes-agent/commit/d3db6724dd2efb5fe3c456cb43e133dc6ca95d17))
- require dashboard auth for plugin API routes ([`ec9329e`](https://github.com/NousResearch/hermes-agent/commit/ec9329ec419ab9cc3e72abd2ff4e282d280da4c3))
- restrict board routing tools to orchestrators ([`2704e7b`](https://github.com/NousResearch/hermes-agent/commit/2704e7b67efa6b25d294578319df54f18e76768f))
- defensive 128k entry in DEFAULT_CONTEXT_LENGTHS + clarify validation test docstring ([`44cdf55`](https://github.com/NousResearch/hermes-agent/commit/44cdf555a83c1d8d605d095442e11efd58089533))
- tell background reviewer not to capture transient env failures as skills (#23004) ([`e5af1dd`](https://github.com/NousResearch/hermes-agent/commit/e5af1dd6337b3db4eaf16b330f403e08f057a16d))
- /kanban slash command emits argparse garbage instead of help ([`d1fc748`](https://github.com/NousResearch/hermes-agent/commit/d1fc748defb9fceaa4abb3b5b6fb4c07931e2e68))
- drop redundant init_db() in gateway watchers (#21378) ([`6f2d605`](https://github.com/NousResearch/hermes-agent/commit/6f2d60559e970ba935761b20c2f3c32395e1d017))
- collapse two-line drop status, name provider, and let agent.log capture diagnostics (#22993) ([`68e4464`](https://github.com/NousResearch/hermes-agent/commit/68e44642c8d126e058ed0bf2fa3c888fe98d7cc5))
- persist via stdin to bypass 128 KB exec-arg cap (#22913) ([`08ec602`](https://github.com/NousResearch/hermes-agent/commit/08ec602770c4451f0e095ad3a288934dae6f98a6))
- use credential_pool for custom endpoint model listing probes ([`4fdaf0b`](https://github.com/NousResearch/hermes-agent/commit/4fdaf0b4d889f8bb9442f82eefa873d90477f2de))
- pass max_total_size_mb and max_file_size_mb to CheckpointManager ([`1fb9f7c`](https://github.com/NousResearch/hermes-agent/commit/1fb9f7c68c2d58951f8ce9ede9533b137e70ba92))
- detect gateway process via /proc in Docker without procps ([`6bf7ac3`](https://github.com/NousResearch/hermes-agent/commit/6bf7ac318558819ea81f528829d564baafda9c79))
- stop run_gateway() tests from rewriting the dev's installed systemd unit (#22900) ([`2ffef15`](https://github.com/NousResearch/hermes-agent/commit/2ffef1567584618d821ee8eabcf05979580c7c52))
- classify generic-typed timeout messages as transient (carve-out of #22664) ([`4f8d8ad`](https://github.com/NousResearch/hermes-agent/commit/4f8d8ad912452069e708fd1edac91f5f12a82147))
- resolve api_key_env in fallback chain entries (carve-out of #22665) ([`6ddc48b`](https://github.com/NousResearch/hermes-agent/commit/6ddc48b058a3f16ac62cb2c9adbbdc715a9ffa28))
- degrade gracefully when all platform adapters are missing ([`246c676`](https://github.com/NousResearch/hermes-agent/commit/246c676c2b02200901d1e762223efa9876b50c0f))
- bridge docker_env config to TERMINAL_DOCKER_ENV ([`116a144`](https://github.com/NousResearch/hermes-agent/commit/116a1446a474f38aa57944f5aa8c6eb4283a7953))
- kill orphaned Popen on post-spawn setup failure ([`53ec328`](https://github.com/NousResearch/hermes-agent/commit/53ec32819cc6a2dceee6538b4c3b665bbee67fcb))
- also patch psutil on Termux fresh-install path ([`c179bda`](https://github.com/NousResearch/hermes-agent/commit/c179bdab3c5f10e83c581d52c231cc58f4905007))
- guard _touch_project against non-dict project metadata ([`2245879`](https://github.com/NousResearch/hermes-agent/commit/2245879af0dcc48f93fa8d516b8748d65ac67c75))
- route OR-combined short CJK tokens to LIKE fallback (#20494) ([`058c508`](https://github.com/NousResearch/hermes-agent/commit/058c50816c70c5f9a1253a87776d50e8df4c5dcf))
- treat streaming premature-close as transient error ([`35f773c`](https://github.com/NousResearch/hermes-agent/commit/35f773c459a3602f253311328809363463f181d5))
- preserve reasoning_content, codex_message_items, finish_reason on transcript replay (#22839) ([`70bfd42`](https://github.com/NousResearch/hermes-agent/commit/70bfd429e55577f06c1b0e04955e19877161cd7b))
- add x-grok-conv-id header for Grok models to improve prompt cache hit rates (carve-out of #22708) ([`883e11f`](https://github.com/NousResearch/hermes-agent/commit/883e11f0a09a6683e35bb75758b686322e8634b0))
- adopt unit's HERMES_HOME for --system CLI ops ([`1508dcb`](https://github.com/NousResearch/hermes-agent/commit/1508dcb9c2169889ccc8db217387d45896e6afb5))
- default notifications to 'important' (silence intermediate) ([`448c11f`](https://github.com/NousResearch/hermes-agent/commit/448c11f16d79897a77c1d507d79e8ee897192aae))
- add explicit do-not-use guidance to acp_command/acp_args schema (carve-out of #22680) ([`ca13993`](https://github.com/NousResearch/hermes-agent/commit/ca139932171148290d53c7586e3eb659a7afa92c))
- align hy3-preview static fallback + delete change-detector test (#22805) ([`1c9ffb1`](https://github.com/NousResearch/hermes-agent/commit/1c9ffb177c378bba24ef208ba8f551722961c655))
- use valid zsh _arguments exclusion-group syntax ([`fe61d95`](https://github.com/NousResearch/hermes-agent/commit/fe61d95b44382d4b06e4a4cc42af55e1e62c0dbe))
- skip pluggable provider profiles when a dedicated check exists (#22346) ([`1dd0790`](https://github.com/NousResearch/hermes-agent/commit/1dd0790654a842cb2677b357fafc9d0790716ab1))
- make _migrate_add_optional_columns idempotent on concurrent open ([`7869838`](https://github.com/NousResearch/hermes-agent/commit/78698381af7ed7efa7e0c8e634af01dab4334511))
- extract thinking from content-list blocks for DeepSeek V4 Pro ([`68854cd`](https://github.com/NousResearch/hermes-agent/commit/68854cdcdb3d287558392104be0c04c37dcbcabc))
- declare youtube-transcript-api in pyproject.toml [youtube] extra ([`98e94be`](https://github.com/NousResearch/hermes-agent/commit/98e94beb1b24f6e8a28ee2f82740a586ff62c3f0))
- send IMAP ID extension to support 163/NetEase mailbox ([`3fd4ccb`](https://github.com/NousResearch/hermes-agent/commit/3fd4ccbd8b6eb7197386900a6a6908a778047018))
- do not cache transient None cloud provider resolution ([`3170c8d`](https://github.com/NousResearch/hermes-agent/commit/3170c8d4484e8fcc12d8a18acdb4f246071b4249))
- send correct resolution param to xAI image generation API ([`13b474c`](https://github.com/NousResearch/hermes-agent/commit/13b474c56e7fb4e7a636417ce3160d5c7fda50c6))
- install cua-driver when Computer Use is enabled via 'hermes tools' (#22765) ([`8f711f7`](https://github.com/NousResearch/hermes-agent/commit/8f711f79a473f1b32f469b47edc27e63f52aab43))
- tighten MEMORY_GUIDANCE against ephemeral PR/issue/SHA notes (#22781) ([`6e5489c`](https://github.com/NousResearch/hermes-agent/commit/6e5489c9f3ecb93c0b907d5647bcc6a569b8f77e))
- skip chain entries matching current provider/model/base_url (#22780) ([`e7c0d6e`](https://github.com/NousResearch/hermes-agent/commit/e7c0d6ee5371dab9eb8b54af60ea88f8455353b8))
- make Ctrl+Enter insert newline on WSL/SSH/Windows Terminal (#22777) ([`70bc52e`](https://github.com/NousResearch/hermes-agent/commit/70bc52e40896afe3a35a2115f8e1fc8af86cc363))
- emit length/error finish_reason for truncation/failure (#22775) ([`2124ad7`](https://github.com/NousResearch/hermes-agent/commit/2124ad72a27d72dfdca0189f3e0e7b6213cb72ea))
- hydrate memory-nudge counters from conversation_history (#22774) ([`86f69e8`](https://github.com/NousResearch/hermes-agent/commit/86f69e8c2a4cf446db69454e0dfe13898e871c8c))
- sanitize comment author rendering in build_worker_context (#22769) ([`ade5981`](https://github.com/NousResearch/hermes-agent/commit/ade5981429e6a44431529117c31be9bd8af77e09))
- harden run_tests.sh — uv-aware bootstrap + scrub HERMES_CRON_SESSION (#22767) ([`f00dc6d`](https://github.com/NousResearch/hermes-agent/commit/f00dc6d7a3a1d1a1cc5e98507d2efb201990f517))
- notify context engine on commit_memory_session (#22764) ([`e90aa7f`](https://github.com/NousResearch/hermes-agent/commit/e90aa7f2802ea1a688df7189b490843f829c6caf))
- follow-up for salvaged PR #22263 ([`dae94fa`](https://github.com/NousResearch/hermes-agent/commit/dae94fa6526dec0c7660276a4d875cebc6e344f6))
- move pytest.importorskip below pytest import in skip-guarded tests ([`b959cfa`](https://github.com/NousResearch/hermes-agent/commit/b959cfa056b68b9bc4cd47dc80de99b457f10454))
- allow quoted URL in github auth-header allowlist ([`b6ff96c`](https://github.com/NousResearch/hermes-agent/commit/b6ff96c057485d14adc8c9499bd9ca712eaa859a))
- honour active_profile when HERMES_HOME points to hermes root ([`a33c63b`](https://github.com/NousResearch/hermes-agent/commit/a33c63b9f8803ff0d9fb7f93896baf0d5bf0d2da))
- honor message.quote for partial-quote reply context ([`854c2ce`](https://github.com/NousResearch/hermes-agent/commit/854c2ce30922200aedb96e0f609697433efd2ec6))
- resolve Git binary for installs under minimal PATH ([`c8ede8a`](https://github.com/NousResearch/hermes-agent/commit/c8ede8aa1bdb0e79879f718db2d7745ac8108b2b))
- expand composite toolset when mixed with configurables in platform_toolsets ([`7d276bf`](https://github.com/NousResearch/hermes-agent/commit/7d276bfbee601f670989ff54c7bd90172af90250))
- gate claim + unblock on parent completion ([`cda20ee`](https://github.com/NousResearch/hermes-agent/commit/cda20eec0c022956b3a857e6bc9c5ae21a689fb9))
- call recompute_ready after unlink_tasks removes a dependency ([`0c22434`](https://github.com/NousResearch/hermes-agent/commit/0c22434f033ab0a8ec8c4e9ede319ecb85e4c206))
- exclude row-label column from bullet items in table rendering ([`8fdaf4d`](https://github.com/NousResearch/hermes-agent/commit/8fdaf4d3d6a877d362b8dd8deec00a9d2caaba17))
- resolve update-check repo from running code, not profile-scoped path ([`cca2869`](https://github.com/NousResearch/hermes-agent/commit/cca2869d78388e049ff1116e420b7209643a9c15))
- exclude infrastructure artifacts when cloning with --clone-all ([`f7e514d`](https://github.com/NousResearch/hermes-agent/commit/f7e514d4adab5b82d1cb58f4aab24ea455a7d0e1))
- pin UTF-8 encoding when reading source files on Windows ([`3801825`](https://github.com/NousResearch/hermes-agent/commit/3801825efd40465ec97e9b1f285cd0e009722dc8))
- replace get_event_loop() with get_running_loop() in async contexts ([`4a1840e`](https://github.com/NousResearch/hermes-agent/commit/4a1840e6835058b6d7fc2457dc652d9cd8d61ce4))
- drop caller-controlled author override in kanban_comment ([`9bbad3c`](https://github.com/NousResearch/hermes-agent/commit/9bbad3cc10cc12b0ad3f76ee323b4e8e6d241cb9))
- use PEP 604 annotation for ToolCall.extra_content ([`0f1d41a`](https://github.com/NousResearch/hermes-agent/commit/0f1d41a88cdddc953faac373505f184c8ee23293))
- add platform hint for MEDIA rendering ([`aad5490`](https://github.com/NousResearch/hermes-agent/commit/aad5490e749319d2f8fbcce3a92ee7aaa3d2aacc))
- log warnings for failed JSON-array coercion ([`7330183`](https://github.com/NousResearch/hermes-agent/commit/7330183d087f65c57db424fb03adf55d72661c32))
- accept JSON string batch tasks ([`326ca75`](https://github.com/NousResearch/hermes-agent/commit/326ca754ad780d1ba22b51970210a9631a3d7196))
- fall back to journal_mode=DELETE on NFS/SMB/FUSE (#22043) ([`2a7047c`](https://github.com/NousResearch/hermes-agent/commit/2a7047c2ed420083d8ff5ff0cb19d075e101a32f))
- map Telegram General topic id to None for forum groups (#22423) ([`ae005ec`](https://github.com/NousResearch/hermes-agent/commit/ae005ec588b70cfe7c928faa1c189734968cb7fe))
- always send tenant headers in OpenViking _headers() when account/user are set ([`8fb3e2d`](https://github.com/NousResearch/hermes-agent/commit/8fb3e2d63afbac1cdf10a192592cb411cb9cef7c))
- handle JSON decode errors in compression — salvage of #22248 (#22416) ([`c7e8add`](https://github.com/NousResearch/hermes-agent/commit/c7e8add12016bcc5591cb161af8c49b66e87a479))
- skip send_chat_action for DM topic reply-fallback lanes ([`aef297a`](https://github.com/NousResearch/hermes-agent/commit/aef297a45eab2afabd0084e62a5e7666eee68981))
- use getJobState helper in handlePauseResume ([`96dc272`](https://github.com/NousResearch/hermes-agent/commit/96dc2726232fc02c836b29968550d7dc5af03e36))
- trim markdown wrap spaces (#22062) ([`a7e7921`](https://github.com/NousResearch/hermes-agent/commit/a7e7921dbc0a593027f40b571861f50a71221aec))
- also catch restart TimeoutExpired; friendly message ([`78b0008`](https://github.com/NousResearch/hermes-agent/commit/78b0008f4451c4b3047107926e466dcfc257ae3e))
- advertise per-mode required params in schema descriptions ([`3adcc64`](https://github.com/NousResearch/hermes-agent/commit/3adcc6441916c40f0c5135e65194ff9642c99f29))
- bypass systemd RestartSec after graceful drain (#22101) ([`d971b26`](https://github.com/NousResearch/hermes-agent/commit/d971b26bfd8305285cac1f47c84cceef67624701))
- offer gateway service install on Windows (#22099) ([`a54cae6`](https://github.com/NousResearch/hermes-agent/commit/a54cae60d4ac72640f203193e810eec46d4a9859))
- guard hermes_bootstrap import so partial updates don't brick hermes (#22091) ([`26bac67`](https://github.com/NousResearch/hermes-agent/commit/26bac67ef90d99646b491f5df4ef3856abb072ad))
- move platforms key out of folded description: > scalars ([`291a158`](https://github.com/NousResearch/hermes-agent/commit/291a158441c2a94cbc33bff6506262ff001050a6))
- strip UTF-8 BOM that broke [scriptblock]::Create ([`59fbcd5`](https://github.com/NousResearch/hermes-agent/commit/59fbcd5ccb4d080f9a00d8a862f6998aa04a1ed7))
- gateway status dedup + install.ps1 platform-SDK bootstrap ([`0548fac`](https://github.com/NousResearch/hermes-agent/commit/0548facc506ff6d19044be28a10879c188b55087))
- os.kill(pid, 0) is NOT a no-op on Windows — route through new _pid_exists helper ([`324567c`](https://github.com/NousResearch/hermes-agent/commit/324567c93662d726e05650c83b06078dce599e37))
- UTF-8 BOM, tiered extras, skip tinker-atropos by default ([`52e497c`](https://github.com/NousResearch/hermes-agent/commit/52e497ce7f3f6910764679fcaeef6d53ebd7e46c))
- browser tool + spurious SIGINT from subprocess spawning ([`0ba1e12`](https://github.com/NousResearch/hermes-agent/commit/0ba1e12abc5aef96429413d7532341a69e37d8d8))
- auto-install Playwright Chromium + surface it in doctor ([`03566e5`](https://github.com/NousResearch/hermes-agent/commit/03566e5124d106656f4152c1b084c233d9c07f3f))
- prefer npm.cmd over npm.ps1, skip .py argv0 in relaunch ([`a2efad6`](https://github.com/NousResearch/hermes-agent/commit/a2efad6bea303a3a04a477dc662c711ec761f782))
- enable execute_code — stale AF_UNIX gate was blocking the tool ([`21efeb5`](https://github.com/NousResearch/hermes-agent/commit/21efeb51bb01bc4a24bb3afb9c621b9baaccabf7))
- %1 install error, patch CRLF false-negative, SOUL.md BOM ([`8f91d7b`](https://github.com/NousResearch/hermes-agent/commit/8f91d7bfa9d8427ca40a392c5fa1ce3dd2fe9231))
- step out of $InstallDir before touching it + harden repo probe ([`d52e541`](https://github.com/NousResearch/hermes-agent/commit/d52e54170ab2d1d7be609fdccfcc820557b8defb))
- validate existing repo via git itself + clean up broken stubs ([`c469a05`](https://github.com/NousResearch/hermes-agent/commit/c469a05ce58b0f269b9750dc6e9a857abcff7ccf))
- quote cache paths in bash + augment PATH so rg/bash resolve on first launch ([`fc91886`](https://github.com/NousResearch/hermes-agent/commit/fc918867b2bcc311ba8992b73b519d7c49626f3e))
- use PortableGit (not MinGit), fix relaunch os.execvp crash, surface npm errors ([`3601e20`](https://github.com/NousResearch/hermes-agent/commit/3601e20f47c886d9174aae4129f310f90a00a682))
- default EDITOR=notepad so /edit and Ctrl+X Ctrl+E work ([`b53bd12`](https://github.com/NousResearch/hermes-agent/commit/b53bd12fe4c2b5518049c61692090fe26a786d30))
- pass encoding=utf-8 to distribution.yaml open (#22083) ([`ea2cc4f`](https://github.com/NousResearch/hermes-agent/commit/ea2cc4f9023c02a2cc130814fdfacc51098efbcf))
- fill in missing delivery URL in adapter-reuse test ([`5e8dfc9`](https://github.com/NousResearch/hermes-agent/commit/5e8dfc9f6dad585b23502e8cd142e6e45d3f024c))
- drop-scheduler fallback + test wiring for enablement gate ([`a995477`](https://github.com/NousResearch/hermes-agent/commit/a99547740dab830c8b121574e4ef50db8fc500f8))
- harden image-rejection fallback + AUTHOR_MAP ([`d0aad4b`](https://github.com/NousResearch/hermes-agent/commit/d0aad4b021b445fbb605dfcfeaa3c533b88bee74))
- unwrap _multimodal tool results to content list for non-Anthropic providers ([`2937f9b`](https://github.com/NousResearch/hermes-agent/commit/2937f9bef60c7a2d5b1531833ffdebfc0af006e2))
- harden auth surface + IP allowlisting + response hygiene ([`b8d7e0e`](https://github.com/NousResearch/hermes-agent/commit/b8d7e0e6d386eceb081cab8123db26474b1a6b9d))
- stream download_to_file body instead of buffering ([`45d860d`](https://github.com/NousResearch/hermes-agent/commit/45d860d424ffbfd143c66ce0ce266c321cd89006))
- cron jobs must not be treated as gateway context ([`839cdd1`](https://github.com/NousResearch/hermes-agent/commit/839cdd1b054a75ff1b581199a83488c8e0f2f788))
- Ctrl+C during /goal loop auto-pauses the goal (#21888) ([`674fad1`](https://github.com/NousResearch/hermes-agent/commit/674fad14832006bfd742c5e3183f34c24018e43a))
- clean up job output dir in remove_job ([`f4e621f`](https://github.com/NousResearch/hermes-agent/commit/f4e621f7d834fe8dc879dd4f4fbf3e14d3d986cf))
- include terminal backend in quick setup wizard (#21842) ([`7190e20`](https://github.com/NousResearch/hermes-agent/commit/7190e20e0b84c581fe182b5038ade7483482e69e))
- cleanup for --check-live salvage ([`83c23e8`](https://github.com/NousResearch/hermes-agent/commit/83c23e88617c97ab5d3663ee8895eeda258a1eb9))
- detect disabled_client in --check and add --check-live ([`5fa493a`](https://github.com/NousResearch/hermes-agent/commit/5fa493a2ca6a5899acc40026283d3f47303f5937))
- prevent stale Ollama credentials after provider switch (#21703) ([`7338e5d`](https://github.com/NousResearch/hermes-agent/commit/7338e5d9ba94c1d90a644d0588ac003d1aaee350))
- auto-pause when judge model returns unparseable output ([`307c85e`](https://github.com/NousResearch/hermes-agent/commit/307c85e5c1b0dd0ca0d94ec362976254cbd949b4))
- defer goal status notices until after response delivery ([`03ddff8`](https://github.com/NousResearch/hermes-agent/commit/03ddff889719c7be164c3d329f9903fdd55aea31))
- set UV_NO_CONFIG=1 to avoid permission denied under sudo -u ([`c80fa72`](https://github.com/NousResearch/hermes-agent/commit/c80fa728bd847885e175a3f4e2b8490cd0bb90fc))
- unwrap platforms key in channels_list ([`292f468`](https://github.com/NousResearch/hermes-agent/commit/292f4683667eb0bdf529db8f82bf26b526a47da5))
- prevent silent token loss and add Claude 4.5–4.7 pricing (#21455) ([`d87c7b9`](https://github.com/NousResearch/hermes-agent/commit/d87c7b99e2a4c86b06368e5c3abf973a0f40f753))
- preserve session when switching personality ([`65c762b`](https://github.com/NousResearch/hermes-agent/commit/65c762b2e83ea39f5cda56a6abf737c3c864b188))
- refresh hermes-tui npmDepsHash for ui-tui lockfile ([`b162f9e`](https://github.com/NousResearch/hermes-agent/commit/b162f9ef9a923dc5765ae1c24c0a32f0a1f5be5e))

### 🔄 Changed

- replace _lazy_import with direct imports, add _degraded_models to __init__ ([`73aa2f5`](https://github.com/NousResearch/hermes-agent/commit/73aa2f56cc0a0679f161feb4be89a2c7f9f3f0d4))
- plug every gateway-kill leak path (#23486) ([`771b8c4`](https://github.com/NousResearch/hermes-agent/commit/771b8c4a368eb8e1841bd71701ca1519afd9c683))
- worker lane contract page + review-required convention ([`ae83a54`](https://github.com/NousResearch/hermes-agent/commit/ae83a54be450872f20832391df948dde739b4d2c))
- add UTF-16 overflow regression tests for #11170 ([`121bbe0`](https://github.com/NousResearch/hermes-agent/commit/121bbe0385198856659a6b335eb3f98eadc7b3ed))
- add 116 stories from the Hermes Discord archive (#23436) ([`3974a13`](https://github.com/NousResearch/hermes-agent/commit/3974a137c6164819282e880fb30ca9e30f7e9ccd))
- handle both lark-SDK-present and absent paths ([`f9e0d60`](https://github.com/NousResearch/hermes-agent/commit/f9e0d60a9989d11626405b71b66aa261da8ea216))
- cover redeliver-on-cycle + flip stale unsub-on-abnormal-event tests ([`787e3c3`](https://github.com/NousResearch/hermes-agent/commit/787e3c368cbf184ec40c959fa1910f92e777a845))
- block tests from killing the live hermes-gateway (#23397) ([`cdb6e5e`](https://github.com/NousResearch/hermes-agent/commit/cdb6e5e52a7169dffba149e18a4fb249f8d197a8))
- cover send-exception rewind + drop noisy success log to debug ([`9c68d12`](https://github.com/NousResearch/hermes-agent/commit/9c68d12079539cffa475ed4171e45da6866243d0))
- document /handoff cross-platform session transfer (#23400) ([`373c4d6`](https://github.com/NousResearch/hermes-agent/commit/373c4d6647fd9a60cff3fe59ea499e8c184979b3))
- drop hardcoded specialist roster, add Step-0 profile discovery ([`6e5c49b`](https://github.com/NousResearch/hermes-agent/commit/6e5c49bdc40d745c77f59daa610c1d1ae5b0e00c))
- document max_spawn as live concurrency cap (not per-tick budget) ([`3fbbf58`](https://github.com/NousResearch/hermes-agent/commit/3fbbf588531fabe2dc3d006142de4f8f4f26bd4b))
- route browser_console eval through supervisor's persistent CDP WS (180x faster) (#23226) ([`d4b26df`](https://github.com/NousResearch/hermes-agent/commit/d4b26df8974bca7114fa4fbff83e4600c31230f9))
- pin assignee-casing static-asset regressions + AUTHOR_MAP ([`08c5b35`](https://github.com/NousResearch/hermes-agent/commit/08c5b35a73d2e4a91782e4032116343ede626620))
- cover task_age safe-int guards + AUTHOR_MAP entry ([`40a4bfa`](https://github.com/NousResearch/hermes-agent/commit/40a4bfa719e13f3e683ef6b1d4665b63ed14da6c))
- broaden plugin API auth coverage + correct stale docstring ([`ae4b09c`](https://github.com/NousResearch/hermes-agent/commit/ae4b09ce10737cff2a556727ed835d272e8a9b04))
- explain auxiliary-model summarization for web_extract (#23211) ([`9cdcf31`](https://github.com/NousResearch/hermes-agent/commit/9cdcf31caef202555446c0e0b68e652bddcc211a))
- add 4 entries from @emmagine79 thread (#23204) ([`3d4297a`](https://github.com/NousResearch/hermes-agent/commit/3d4297a59a8607ed24850524d229f5f42520d087))
- add live-API regression and make picker test deterministic ([`826e717`](https://github.com/NousResearch/hermes-agent/commit/826e7171e97a97215785a517491705f7c695e4f2))
- document ChatGPT Pro entitlement gating ([`9ee9a42`](https://github.com/NousResearch/hermes-agent/commit/9ee9a4297de7998bf64b42dc396c226098e52b27))
- add codex-spark salvage contributors to AUTHOR_MAP ([`6b5e011`](https://github.com/NousResearch/hermes-agent/commit/6b5e0119b3e40bf5afdf941919503e1c49b047f7))
- refresh OpenRouter + Nous fallback lists (#23001) ([`3d2bfc5`](https://github.com/NousResearch/hermes-agent/commit/3d2bfc502e4693e064e06114e5052683a3fb16d7))
- add 18 verified social entries (99 → 117) (#22920) ([`e622504`](https://github.com/NousResearch/hermes-agent/commit/e62250453b4a4b8232722caa4853fe900b6a9a9e))
- assert re-block notification is delivered after unblock cycle ([`dd49d50`](https://github.com/NousResearch/hermes-agent/commit/dd49d50389891134c9f6723bc1351cd41480603f))
- move heavy training skills + outlines to optional-skills (#22912) ([`ded194e`](https://github.com/NousResearch/hermes-agent/commit/ded194eb6aca6c7999589168b19d139d1b785316))
- skip welcome banner on `chat -q` single-query mode (#22904) ([`b67ea7f`](https://github.com/NousResearch/hermes-agent/commit/b67ea7ff474831743b14edefb6c9113cb12216e7))
- stub /proc unavailability in find_gateway_pids fallback test ([`4ca7c21`](https://github.com/NousResearch/hermes-agent/commit/4ca7c2104da006aa0eac8cd8199aad7b5c12851f))
- defer fal_client import to first generation request (#22859) ([`c1cc3d4`](https://github.com/NousResearch/hermes-agent/commit/c1cc3d4ea65bf11dc493f9d81695bab0003b1aa9))
- round 2 audit — messaging, developer-guide, guides, integrations (#22858) ([`fef1a41`](https://github.com/NousResearch/hermes-agent/commit/fef1a41248a9a584f7b945d0a46d57de46d15358))
- document auxiliary.<task>.extra_body for OR routing and Pareto (#22844) ([`0bcc327`](https://github.com/NousResearch/hermes-agent/commit/0bcc327cab9dc9b60d80e6e0e5239149d7a83207))
- defer httpx import to first webhook call (#22831) ([`550f6e2`](https://github.com/NousResearch/hermes-agent/commit/550f6e2efc338e274993747dd66d5a6bed00f6f9))
- cache-first lookup, skip network when disk cache is fresh (#22808) ([`775c0e2`](https://github.com/NousResearch/hermes-agent/commit/775c0e22cf5a0963aceab3fda2f45cbfc3fa1d25))
- deep audit — fix stale config keys, missing commands, and registry drift (#22784) ([`252d68f`](https://github.com/NousResearch/hermes-agent/commit/252d68fd4500d086b6092d6f4306ecf56b70c761))
- defer QQAdapter and YuanbaoAdapter imports via PEP 562 (#22790) ([`ea2d66d`](https://github.com/NousResearch/hermes-agent/commit/ea2d66ddc0ca57d6d11a609699177fd598ed4988))
- regression-guard literal '1k'/'2k' resolution payload ([`dcff23a`](https://github.com/NousResearch/hermes-agent/commit/dcff23a25f30db6fc589ae2194df39b1a9bc606b))
- parallelize API connectivity checks and disable IMDS (#22766) ([`e612c3d`](https://github.com/NousResearch/hermes-agent/commit/e612c3d6f00624868ce3f73bb6beaacfea36337f))
- defer heavy google-cloud imports to first adapter use (#22681) ([`8f83046`](https://github.com/NousResearch/hermes-agent/commit/8f83046f6c4af82a36610c75502351aeb00606a7))
- add nik1t7n to AUTHOR_MAP ([`f6d45e5`](https://github.com/NousResearch/hermes-agent/commit/f6d45e5df49c85c87a3f2ec44f9e92e233019622))
- add KvnGz to AUTHOR_MAP (#22458) ([`5d2a75d`](https://github.com/NousResearch/hermes-agent/commit/5d2a75ddf26cc89f304262fbb8519ddaa2f002de))
- add Zhekinmaksim to AUTHOR_MAP (#22449) ([`b7d8e28`](https://github.com/NousResearch/hermes-agent/commit/b7d8e280e85e27cb356ac25759124f4e25bf4ad1))
- cover kanban_comment author hardening + cross-task policy ([`e3ebaa1`](https://github.com/NousResearch/hermes-agent/commit/e3ebaa19bac666773a01bc4f37ef81a7966d9dc4))
- cover relay-declared sender_type honoring ([`8578f89`](https://github.com/NousResearch/hermes-agent/commit/8578f898cbe6f9c0f6f7c6fab1cb6fffef453f54))
- add uzunkuyruk to AUTHOR_MAP (#22434) ([`4632be1`](https://github.com/NousResearch/hermes-agent/commit/4632be123df5c3f31831ec43dc6ba10c502064f6))
- add leehack to AUTHOR_MAP for PR #22053 salvage (#22409) ([`28b5bd7`](https://github.com/NousResearch/hermes-agent/commit/28b5bd7e93816e1533c41dd38f2e29d7f1baeb52))
- collapse 9 schema-shape tests into 2 invariants ([`8e4f3ba`](https://github.com/NousResearch/hermes-agent/commit/8e4f3ba4da5337e1ad674a876ac4fb8490f0b79c))
- cut ~19s from 'hermes' cold start (skills cache + lazy Feishu + no Nous HTTP) (#22138) ([`0ec052c`](https://github.com/NousResearch/hermes-agent/commit/0ec052ca24476379b0004af800d049abde17323d))
- call out Ctrl+Enter for Windows Terminal users ([`d606df8`](https://github.com/NousResearch/hermes-agent/commit/d606df81263dcd4a791f438031f08f3b5bd639e3))
- skip eager plugin discovery on known built-in subcommands (#22120) ([`5089596`](https://github.com/NousResearch/hermes-agent/commit/5089596685826ef2f63214f2fd184da88cc4cdb7))
- label native Windows support as early beta (#22115) ([`7a4d5c1`](https://github.com/NousResearch/hermes-agent/commit/7a4d5c123a29e60dec647977572116bad2036a13))
- run docker build on PRs + smoke test arm64 ([`93679ef`](https://github.com/NousResearch/hermes-agent/commit/93679ef27d74d7d8430b603acb9d0bdc3b1e7607))
- add blocking uv.lock check ([`758c401`](https://github.com/NousResearch/hermes-agent/commit/758c40135f0f0929ba2ed0a432c8801debe6f056))
- split docker-publish into per-arch native runners ([`bf80508`](https://github.com/NousResearch/hermes-agent/commit/bf80508d65665b91aba43919c9d11efaba5a1e2e))
- remove 50 stale/broken tests to unblock CI (#22098) ([`66320de`](https://github.com/NousResearch/hermes-agent/commit/66320de52e9d77c5afc9767a350447011c8577f1))
- add native Windows guide + install one-liner on landing page (#22089) ([`3299be6`](https://github.com/NousResearch/hermes-agent/commit/3299be6bdb0a604b3730481004d2e0e33d0e83c7))
- add blocking ruff-check + windows-footguns jobs to lint.yml ([`d3120ae`](https://github.com/NousResearch/hermes-agent/commit/d3120aeab064c7d8275cd85d39c567313a93f6b2))
- migrate stale os.kill monkeypatches to gateway.status._pid_exists ([`f5ee780`](https://github.com/NousResearch/hermes-agent/commit/f5ee780124904be1992771cb7c9f7a9263d833e7))
- add Windows-Specific Quirks section to hermes-agent skill + keystroke diagnostic ([`b63f964`](https://github.com/NousResearch/hermes-agent/commit/b63f9645f08af894f2685521ffe4ee55df79d620))
- cron renewal recipe, sidebar wiring, skill rewrite ([`242da9d`](https://github.com/NousResearch/hermes-agent/commit/242da9db965ca5618995c5ff92659171f7aae629))
- meeting summary delivery section + env var reference ([`9680827`](https://github.com/NousResearch/hermes-agent/commit/9680827078c4d73cbbadf3f97674aaa4f9839a7c))
- full user guide for profile distributions (#22017) ([`ea86714`](https://github.com/NousResearch/hermes-agent/commit/ea86714cc0e0b3461a8f69b778116d8bbd3dc61c))
- webhook listener setup page + env var reference ([`474d1e8`](https://github.com/NousResearch/hermes-agent/commit/474d1e812bf3fe1a1f75b2ab06f477c631bf62c3))
- add Azure app registration walkthrough + env var reference ([`cf648a9`](https://github.com/NousResearch/hermes-agent/commit/cf648a9b7e4f3a346451d543648ce76922971e1a))
- move User-Agent to profile.default_headers ([`81928f0`](https://github.com/NousResearch/hermes-agent/commit/81928f03ab5841362e526df011e3eb74159aea8b))
- register triage_specifier in the aux-models enumerations (#21494) ([`cff821e`](https://github.com/NousResearch/hermes-agent/commit/cff821e2dc03e55e5b036d266ea38a8d39a2b938))
- fix AUTHOR_MAP for johnsonblake1@gmail.com → voteblake ([`2214ab1`](https://github.com/NousResearch/hermes-agent/commit/2214ab1073162fd3784c4ca98c518fc4b29690ab))

### 🔧 Other

- docker: split python dep install into cached layer above COPY . . ([`afc186f`](https://github.com/NousResearch/hermes-agent/commit/afc186fa4eed44e0d5e4c5a5f1d2b3b8ac8f0f13))
- auth: use get_default_hermes_root() for shared nous_auth.json path ([`62b4ebb`](https://github.com/NousResearch/hermes-agent/commit/62b4ebb7db4e18fd3628ada0a1a30609ed6a109e))
- lint: enable PLW1514 as a blocking ruff rule ([`3be853a`](https://github.com/NousResearch/hermes-agent/commit/3be853a9b848ad24827cb5d64b66d87f2797b05c))
- codebase: add encoding='utf-8' to all bare open() calls (PLW1514) ([`cbce5e9`](https://github.com/NousResearch/hermes-agent/commit/cbce5e93fcb9a923ab71f45d2a0f0f172dd54967))
- hermes_bootstrap: Windows-only UTF-8 stdio shim for all entry points ([`d94fb47`](https://github.com/NousResearch/hermes-agent/commit/d94fb47717eb6e2c343e1615fdabf436f19b350a))
- execute_code: set PYTHONIOENCODING=utf-8 + PYTHONUTF8=1 in child env ([`107de03`](https://github.com/NousResearch/hermes-agent/commit/107de0321d0e8b9e23a60ec7439fdc50f45d2137))
- tests: skip POSIX-venv-layout tests on Windows ([`e614e87`](https://github.com/NousResearch/hermes-agent/commit/e614e87954638a164c3e6e552408971e231a10f1))
- execute_code: write sandbox files as UTF-8 on Windows ([`da18443`](https://github.com/NousResearch/hermes-agent/commit/da184439db42a6ac6816d31bb0c2fedd18d93c23))
- tests: lock in POSIX-equivalence guard for execute_code env scrubber ([`3b9cd58`](https://github.com/NousResearch/hermes-agent/commit/3b9cd5820898796ead8f7d5913efc42071d2e94a))
- execute_code: pass through Windows OS-essential env vars ([`5c859e5`](https://github.com/NousResearch/hermes-agent/commit/5c859e57165df24aabb0c9b3a01a5b5b6b5276e7))

## [v2026.5.7] — 2026-05-07

_No significant changes._

## [v2026.4.30] — 2026-04-30

_No significant changes._

## [v2026.4.23] — 2026-04-23

_No significant changes._

## [v2026.4.16] — 2026-04-16

_No significant changes._

## [v2026.4.13] — 2026-04-13

_No significant changes._

## [v2026.4.8] — 2026-04-08

_No significant changes._

## [v2026.4.3] — 2026-04-03

_No significant changes._

## [v2026.3.30] — 2026-03-30

_No significant changes._

## [v2026.3.28] — 2026-03-28

_No significant changes._

## [v2026.3.23] — 2026-03-23

_No significant changes._

## [v2026.3.17] — 2026-03-17

_No significant changes._

## [v2026.3.12] — 2026-03-12

_No significant changes._

---
_257 commits processed._