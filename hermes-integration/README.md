# OpenClaw / Hermes Workflow Integration

A Claude Code skill that integrates with OpenClaw and Hermes workflow systems.

## Overview

This skill enables Claude Code to interact with OpenClaw sessions, cron jobs, and Hermes-style workflow orchestration.

## Features

- Session management (list, send, spawn)
- Cron job scheduling and monitoring
- Cross-session messaging
- Workflow state tracking

## Installation

```bash
# Add to your project
cp SKILL.md ~/.claude/skills/openclaw-integration/
```

## Usage

```bash
# List active sessions
openclaw sessions list

# Send message to session
openclaw sessions send --key <session-key> --message "Hello"

# Create cron job
openclaw cron add --name "daily-review" --schedule "0 9 * * *"

# Spawn sub-agent
openclaw sessions spawn --task "Review PR #123"
```

## Configuration

Set these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENCLAW_HOME` | OpenClaw home directory | `~/.openclaw` |
| `HERMES_API_KEY` | Hermes workflow API key | - |
| `WORKFLOW_URL` | Hermes workflow endpoint | - |

## Architecture

```
Claude Code → openclaw CLI → Gateway API → Sessions/Cron/Sub-agents
                         → Hermes API → Workflow Engine
```

## Acceptance Criteria

- [x] Can list and interact with OpenClaw sessions
- [x] Can create and manage cron jobs
- [x] Can spawn sub-agents for parallel work
- [x] Can send messages between sessions
- [x] Supports Hermes workflow integration via API

## Files

- `SKILL.md` — Skill definition
- `README.md` — This documentation
- `src/integration.ts` — Core integration logic
- `test/workflow.test.ts` — Integration tests
