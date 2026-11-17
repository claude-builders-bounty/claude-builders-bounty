---
name: hermes-skill-pruning-optimization
description: "Disable unused skills to reduce token bloat."
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, pruning, optimization, token-budget, cleanup]
    related_skills: [auto-skill-distill, hermes-agent-skill-authoring, session-librarian]
---

# Hermes Skill Pruning & Optimization

Audit enabled skills, disable unused categories to reduce token overhead, prevent [SKILL_PRUNED] data loss from compression, and improve model routing accuracy.

## When to Use

- After `hermes-full-health-check` reports >50 enabled skills
- When experiencing token budget pressure or slow skill loading
- After adding many skills via `auto-skill-distill`
- When [SKILL_PRUNED] markers appear frequently
- Periodic skill library maintenance (quarterly)

## Prerequisites

- Hermes CLI functional (`hermes skills list` works)
- Understanding of which skill categories are actively used
- Backup of current skill list (for rollback)

## How to Run

```bash
# Audit current skills
hermes skill run hermes-skill-pruning-optimization --audit

# Disable unused categories (non-interactive, uses config API)
hermes skill run hermes-skill-pruning-optimization --disable-unused

# Apply recommended profile (keeps: devops, github, autonomous-ai-agents core, software-development, research, memory, learning-capture, proactive-hermes, web-content-fetcher)
hermes skill run hermes-skill-pruning-optimization --apply-recommended

# Re-enable if needed (edit config.yaml skills.disabled list)
hermes skill run hermes-skill-pruning-optimization --enable <skill-name>
```

## Quick Reference

| Task | Command |
|------|---------|
| Audit skills | `hermes skill run hermes-skill-pruning-optimization --audit` |
| Disable unused | `hermes skill run hermes-skill-pruning-optimization --disable-unused` |
| Apply recommended | `hermes skill run hermes-skill-pruning-optimization --apply-recommended` |
| List enabled | `hermes skills list --enabled-only` |
| **Disable single (non-interactive)** | `hermes config set skills.disabled '[\"skill1\", \"skill2\"]'` |
| **Enable single (non-interactive)** | `hermes config set skills.disabled '[\"remaining\", \"skills\"]'` |

> ⚠️ **重要**：`hermes skills disable/enable` 子命令**不存在**（Hermes 0.20.5 实测）。`hermes skills config --disable` **需要 TTY 交互**，非交互式不可用。  
> 正确的非交互式方式：**`hermes config set skills.disabled '[\"skill1\", \"skill2\", ...]'`（传完整列表、覆盖写入）**。  
> 重新启用 = 从列表中移除该技能名，再次写入完整列表。

## Procedure

### 1. Audit Current Skill State
```bash
# Count enabled skills
hermes skills list --enabled-only | wc -l

# List by category
hermes skills list --enabled-only | awk '{print $2}' | sort | uniq -c | sort -rn

# Check for pruned markers
grep -r "SKILL_PRUNED" ~/.hermes/skills/ 2>/dev/null | wc -l
```
**Completion criterion:** Baseline metrics captured (total count, by category, pruned count).

### 2. Identify Unused Categories
```bash
# Recommended KEEP categories (core operational):
# - devops (22 skills: config, systemd, memory, scripts, health, etc.)
# - github (6 skills: repo, PR, issue, review, auth)
# - autonomous-ai-agents (core: claude-code, codex, opencode, hermes-agent, merge-reconciler)
# - software-development (8 skills: debug, TDD, plan, spike, simplify, code-review, node-inspect, python-debugpy)
# - research (8 skills: arxiv, blocked-page, blogwatcher, competitor-news, grounded-citations, llm-wiki, platform-compliance, automation-opportunity)
# - memory (1 skill: memory-local)
# - learning-capture (1 skill: learning-capture)
# - proactive-hermes (1 skill: proactive-hermes)
# - web-content-fetcher (1 skill: web-content-fetcher)
# Total recommended: ~49 skills

# Categories to DISABLE (rarely/never used):
# - creative (21 skills: ascii, diagram, video, design, music, etc.)
# - media (3 skills: gif, songsee, youtube)
# - smart-home (1 skill: openhue)
# - game-modding (1 skill: mo2)
# - modding (1 skill: skyrim-mo2)
# - social-media (1 skill: xurl)
# - email (2 skills: inbox-triage, himalaya)
# - mlops (4 skills: huggingface, llama-cpp, vllm, wandb)
# - mlops/evaluation (2 skills)
# - mlops/inference (2 skills)
# - productivity (15 skills: airtable, box, docx, gworkspace, maps, meeting, nano-pdf, notion, ocr, pdf, pptx, price-monitor, session-librarian, teams, weekly, xlsx)
# - note-taking (1 skill: obsidian)
# Total to disable: ~53 skills
```
**Completion criterion:** Clear keep/disable list documented.

### 3. Disable Unused Categories (非交互式批量禁用)

> **关键**：使用 `hermes config set skills.disabled '[...]'` 一次性写入完整禁用列表。
> 以下脚本先生成完整禁用列表，再写入。

```bash
# 生成完整禁用列表（约 83 个），写入 config.yaml
hermes config set skills.disabled '[
  "architecture-diagram",
  "ascii-art",
  "ascii-video",
  "baoyu-infographic",
  "claude-design",
  "comfyui",
  "design-md",
  "excalidraw",
  "humanizer",
  "manim-video",
  "p5js",
  "popular-web-designs",
  "pretext",
  "sketch",
  "songwriting-and-ai-music",
  "touchdesigner-mcp",
  "claude-code",
  "codex",
  "opencode",
  "merge-reconciler",
  "imperial-multi-agent-orchestration",
  "batch-install-skills",
  "configure-hermes-memory-provider",
  "configure-mcp-servers",
  "configure-messaging-gateway",
  "configure-modelscope-vision",
  "configure-nvidia-fallback",
  "configure-ollama-wsl",
  "install-chromadb-wsl",
  "playwright-chromium-china-mirror",
  "email-inbox-triage",
  "himalaya",
  "mo2-mod-management",
  "skyrim-mo2-mod-management",
  "gif-search",
  "songsee",
  "youtube-content",
  "evaluating-llms-harness",
  "huggingface-hub",
  "llama-cpp",
  "serving-llms-vllm",
  "weights-and-biases",
  "obsidian",
  "airtable",
  "box",
  "document-to-action-items",
  "docx",
  "google-workspace",
  "maps",
  "meeting-action-items",
  "nano-pdf",
  "notion",
  "ocr-and-documents",
  "pdf",
  "powerpoint",
  "product-price-monitor",
  "session-librarian",
  "teams-meeting-pipeline",
  "weekly-review-planning",
  "xlsx",
  "automation-opportunity-vetting",
  "blocked-page-recovery",
  "blogwatcher",
  "competitor-news-monitor",
  "grounded-citations",
  "llm-wiki",
  "platform-compliance-vetting",
  "research-paper-writing",
  "openhue",
  "xurl",
  "inspecting-hermes-desktop-dom",
  "node-inspect-debugger"
]'
```

**⚠️ 必须剔除的技能（用户在用的自建技能，不可禁用）**：
- albion-transport-trading
- uumit-autonomous-earning
- uumit-market-autobid-deployment
- imperial-multi-agent-orchestration (自建版)
- openclaw-imperial-orchestration
- configure-feishu-gateway
- configure-hermes-memory-provider
- configure-mcp-servers
- configure-messaging-gateway
- configure-modelscope-vision
- configure-nvidia-fallback
- configure-ollama-wsl
- install-chromadb-wsl
- scope-recall-vector-migration
- verify-hermes-setup
- proactive-hermes
- learning-capture
- multi-profile-gateway-management
- novel-memory-ingestion-pipeline
- rp-character-crafter
- web-content-fetcher
- auto-skill-distill
- browser-exec-web-scraping
- cross-platform-text-processing
- debug-wsl-windows-network
- edit-config-files-wsl
- fix-feishu-credentials-sync
- hermes-full-health-check
- hermes-memory-provider-setup
- hermes-script-library-safety
- hermes-skill-pruning-optimization
- hermes-systemd-timers-setup
- inspect-android-emulator
- manage-python-venv-wsl
- manage-systemd-services-wsl
- multi-session-creative-workflow
- novel-download-12kanshu
- novel-to-sillytavern-pipeline
- openclaw-imperial-orchestration
- playwright-chromium-china-mirror
- poe2-build-planning-agent
- proactive-health-patrol
- troubleshoot-hermes-config
- watchdog-cron-patterns
- wsl-readonly-mount-enforcement
- wsl2-windows-interop-automation
- wsl-hermes-system-health

**Completion criterion:** `hermes skills list --enabled-only | wc -l` shows ~35 skills.

### 4. Verify Optimization
```bash
# Count enabled
hermes skills list --enabled-only | wc -l
# Should be ~35 (down from 118)

# Check pruned markers reduced
grep -r "SKILL_PRUNED" ~/.hermes/skills/ 2>/dev/null | wc -l
# Should be lower (fewer skills = less compression pressure)

# Test skill loading
hermes skill view verify-hermes-setup >/dev/null && echo "Core skill loads"
hermes skill view proactive-hermes >/dev/null && echo "Core skill loads"
```
**Completion criterion:** Enabled count ~35, core skills load, pruned markers reduced.

### 5. Rollback Plan (if needed)
```bash
# Re-enable a category: 从禁用列表移除该技能，重新写入完整列表
# 例：重新启用 creative 类
hermes config get skills.disabled > /tmp/current_disabled.json
# 编辑 /tmp/current_disabled.json 移除要启用的技能
hermes config set skills.disabled "$(cat /tmp/current_disabled.json)"

# Or restore all (清空禁用列表)
hermes config set skills.disabled '[]'
```
**Completion criterion:** Rollback tested and documented.

## Pitfalls

- **Session cache**: Disabled skills still appear in current session until restart.
- **Dependency chains**: Some skills list others in `related_skills`; disabling may cause validation warnings (harmless).
- **User-specific needs**: Adjust keep/disable list based on actual usage patterns.
- **Auto-skill-distill**: May create new skills in disabled categories; monitor and move or re-enable as needed.
- **Profile isolation**: Skills disabled in `default` profile don't affect `empress` profile.

## Verification

```bash
# 1. Enabled count near target
COUNT=$(hermes skills list --enabled-only | wc -l)
[ $COUNT -lt 55 ] && echo "PASS: $COUNT skills" || echo "FAIL: $COUNT skills"

# 2. Core categories present
for cat in devops github autonomous-ai-agents software-development research memory learning-capture proactive-hermes web-content-fetcher; do
  hermes skills list --enabled-only | grep -q "$cat" && echo "KEEP: $cat" || echo "MISSING: $cat"
done

# 3. Pruned markers reduced
PRUNED=$(grep -r "SKILL_PRUNED" ~/.hermes/skills/ 2>/dev/null | wc -l)
echo "Pruned markers: $PRUNED"
```

---

*Skill distilled from session 20260908_042140_65b6a3aa (health check SKILLS-001: 110 skills all enabled, token bloat, [SKILL_PRUNED] data loss). Pattern threshold met via recurring optimization need.*