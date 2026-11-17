---
name: learning-capture
version: "1.0.0"
description: "Capture learnings, errors, and corrections for continuous improvement. Auto-promotes recurring patterns to skills. Integrates with memory-local and auto-skill-distill cron."
author: Hermes Agent
tags: [learning, self-improving, error-tracking, skill-distillation]
requires:
  - python: ">=3.10"
  - pip: ["pyyaml"]
---

# Learning Capture 🧠

**让 Hermes 越用越聪明** — 捕获对话中的修正/报错/洞见 → 自动去重/归类 → 定期蒸馏成可复用 Skill。

---

## 核心流程

```
对话中触发学习
      │
      ▼
┌─────────────┐     即时写入 .learnings/      ┌──────────────┐
│ 用户说:      │  ─────────────────────────▶  │ LEARNINGS.md │
│ "不对,应该   │                              │ ERRORS.md    │
│  是..."      │                              │ FEATURES.md  │
└─────────────┘                              └──────────────┘
      │                                             │
      │         每日 04:00 auto-skill-distill       │
      └────────────────────────────────────────────▶│
                                                    ▼
                                           ┌──────────────┐
                                           │ 识别高频模式  │
                                           │ 生成/更新Skill│
                                           └──────────────┘
```

---

## 自动捕获的触发词（在 `agent:end` hook 里检测）

| 类别 | 触发词示例 | 写入文件 |
|------|------------|----------|
| **纠正** | "不对"、"其实是"、"应该是"、"更正"、"错了" | `LEARNINGS.md` (category: correction) |
| **洞见** | "注意"、"关键是"、"核心在于"、"经验是"、"发现了" | `LEARNINGS.md` (category: insight) |
| **知识盲区** | "不知道"、"没见过"、"不熟悉"、"第一次" | `LEARNINGS.md` (category: knowledge_gap) |
| **最佳实践** | "最好"、"推荐"、"标准做法"、"规范" | `LEARNINGS.md` (category: best_practice) |
| **报错/失败** | "报错"、"failed"、"error"、"exception"、"崩了" | `ERRORS.md` |
| **需求新能力** | "能不能"、"有没有办法"、"想要"、"缺个" | `FEATURES.md` |

---

## 文件格式

### `.learnings/LEARNINGS.md`
```markdown
# Learnings

**Categories**: correction | insight | knowledge_gap | best_practice

---

## 2026-08-25 14:32 — correction
**Trigger**: "不对，应该用 patch 不要用 sed"
**Context**: 批量修改配置文件
**Learning**: Hermes 环境用 patch 工具替代 sed/awk，抗干扰更强
**Source**: user_correction
**Status**: active

## 2026-08-25 15:10 — insight
**Trigger**: "关键是要先验证再执行"
**Context**: 运行危险命令前
**Learning**: 所有 destructive 操作必须先 dry-run/预览，再确认执行
**Source**: user_guidance
**Status**: active
```

### `.learnings/ERRORS.md`
```markdown
# Errors

---

## 2026-08-25 16:00 — terminal command failed
**Command**: `pip install xxx`
**Error**: `externally-managed-environment`
**Fix**: 使用 `/home/user01/.hermes/hermes-agent/venv/bin/pip` 或 `uv pip`
**Status**: resolved
**Frequency**: 3
```

### `.learnings/FEATURES.md`
```markdown
# Feature Requests

---

## 2026-08-25 16:30
**Request**: "能不能自动把重复的操作变成脚本"
**Context**: 手动跑了 3 次相同的数据清洗流程
**Proposed Skill**: `data-cleanup-pipeline`
**Priority**: high
**Status**: pending
```

---

## 技能蒸馏规则（auto-skill-distill 每日跑）

| 条件 | 动作 |
|------|------|
| 同一 `category` + 相似 `Context` 出现 ≥ 3 次 | 生成 Skill 草稿 → `~/.hermes/skills/auto-generated/<name>/SKILL.md` |
| 同一 `Error` 出现 ≥ 2 次且 `Status=resolved` | 生成故障排查 Skill / 更新现有 Skill 的 `故障排查` 章节 |
| `FEATURES.md` 中 `Priority=high` + `Status=pending` ≥ 1 周 | 创建 Skill 骨架，标记需人工完善 |

---

## 手动命令

```bash
# 记录一个学习
hermes skill run learning-capture log \
  --type correction \
  --trigger "用户说不对" \
  --context "修改配置文件" \
  --learning "用 patch 替代 sed"

# 记录一个报错
hermes skill run learning-capture error \
  --cmd "pip install xxx" \
  --err "externally-managed-environment" \
  --fix "用 venv 里的 pip"

# 查看统计
hermes skill run learning-capture stats

# 手动触发蒸馏（生成 skill 草稿）
hermes skill run learning-capture distill
```

---

## 与现有系统集成

| 组件 | 集成方式 |
|------|----------|
| `memory-local` | 学习条目也写入向量记忆（`type=learning`），语义检索可召回 |
| `auto-skill-distill` cron | 读取 `.learnings/` 三个文件，按规则生成/更新 skill |
| `proactive-hermes` | 审计时检查 `.learnings/` 是否定期清理/归档 |
| `verify-hermes-setup` | 检查 `.learnings/` 目录存在且可写 |

---

## 文件结构

```
~/.hermes/skills/learning-capture/
├── SKILL.md
├── scripts/
│   ├── capture.py      # 核心：解析触发词、写入 .learnings/
│   ├── distill.py      # 蒸馏逻辑：聚类 → 生成 skill 草稿
│   └── cli.py          # CLI 入口
├── references/
│   └── distillation-rules.md
└── templates/
    ├── LEARNINGS.md.template
    ├── ERRORS.md.template
    └── FEATURES.md.template
```

---

## 快速开始

```bash
# 1. 初始化 .learnings 目录（首次自动）
mkdir -p ~/.learnings
# 模板会自动创建

# 2. 在 memory-local hook 里集成捕获逻辑
# 编辑 ~/.hermes/hooks/memory-local/handler.py
# 在 on_turn_end() 里调用 capture.parse_and_save(context)

# 3. 验证
hermes skill run learning-capture stats
```