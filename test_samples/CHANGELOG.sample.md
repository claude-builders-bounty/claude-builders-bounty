# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [sample-hermes] - 2026-05-20

### Added
- feat(firecrawl): add integration tag for Hermes usage in browser and web providers (`273ff5c` by Erik Engervall)
- feat: show names of user-modified skills in bundled skill sync summary (`58591d9` by zccyman)
- feat(update): syntax-validate critical files post-pull, auto-rollback on failure (#28669) (`aedb8ac` by Teknium)
- feat(signal): add require_mention filter for group chats (`7f40767` by jdelmerico)
- feat(telegram): skip-STT audio path + 2GB cap via local Bot API server (`ad2531b` by Albert G)
- feat(telegram): pin incoming user message for duration of agent turn (`a724c3b` by Indigo Karasu)
- feat(telegram): ignore_root_dm with system command lobby (`c931dad` by ai-hana-ai)
- feat(telegram): support quick-command-only menus (`b1acf80` by stevehq26-bot)
- feat(telegram): add disable_topic_auto_rename gateway flag (`9d789f3` by B0Tch1)
- feat(send_message): auto-detect @username mentions and create Telegram entities (`cf814c9` by fonhal)
- feat(kanban): drag-to-delete trash zone + bulk delete for task cards (`dfcf48b` by Jpalmer95)
- feat(kanban): add scheduled status for delayed follow-ups (`e382365` by roycepersonalassistant)
- feat(skills): add skill bundles — alias /<name> loads multiple skills (#28373) (`b5c1fe7` by Teknium)
- feat(kanban): configure worktree paths and branches (`1733cb3` by aqilaziz)
- feat(kanban): show dashboard cron jobs across profiles (`1a51727` by SerenityTn)
- feat(kanban): add respawn guard to block repeat worker storms (`264e85b` by fardoche6)
- feat(kanban): filter tasks by workflow fields and runs by status/outcome (`341912c` by nehaaprasaad)
- feat(kanban): stale detection for running tasks in dispatcher (`e286e68` by thewillhuang)
- feat(kanban): wire dispatcher to dispatch review agents from review column (`f55d94a` by thewillhuang)
- feat(kanban): stamp originating ACP session_id on tasks (`31fe229` by awizemann)
- feat(kanban): add optional board parameter to all MCP tools (`8e193cf` by nnnet)
- feat(cli): add kanban swarm topology helper (`3ee7a55` by Niraven)
- feat(kanban): surface per-task model_override in show + tool output (`79f6654` by loicnico96)
- feat(kanban): worker visibility endpoints (workers/active, runs/{id}, inspect) (`02efad7` by Interstellar-code)
- feat(kanban): add --sort option to 'hermes kanban list' (`a846e50` by LizerAIDev)
- feat(kanban): add max_in_progress config to cap concurrent running tasks (`5fdcfd8` by SimbaKingjoe)
- feat(kanban): add initial-status for human-ops cards (`fb96208` by shunsuke-hikiyama)
- feat(kanban): allow trimmed task comments (`a5c2836` by ACR27)
- feat(kanban): add board-level default workdir (#25430) (`fe5e0bf` by zccyman)
- feat: per-task model override for kanban workers (`f01ee0b` by hongchen1993)
