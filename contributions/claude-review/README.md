# 🤖 claude-review — Claude Code PR Review Agent

A lightweight CLI tool that takes a GitHub PR URL, analyzes the diff, and returns a structured Markdown review.

> **Bounty**: [#4 $150](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4)

## ✨ Features

- 🚀 CLI: `python3 review.py <pr_url>`
- 📊 Structured output: Summary → Files → Risks → Improvements → Confidence
- 🔍 Auto-detects: hardcoded secrets, debug prints, code injection, empty exception handlers, large PRs
- ✅ Works with any public GitHub PR

## 🚀 Quick Start

```bash
# Prerequisites: GitHub CLI
gh auth login

# Run
python3 review.py https://github.com/owner/repo/pull/123
```

## 📋 Output Example

```
## 🤖 Claude Code PR Review

### 📋 改动概要
**PR**: Fix login timeout issue
**改动**: +42/-18 行, 3 个文件

### ⚠️ 风险项
- ⚠️ 硬编码凭据风险: auth.py:15
- 🔧 调试输出残留: utils.py:22

### 💡 改进建议
- ✅ 当前改动合理

### 📊 置信度评分：Medium ⚠️
```

## 🔧 Requirements

- Python 3.8+
- GitHub CLI (`gh`)
- Git

## 📄 License

MIT
