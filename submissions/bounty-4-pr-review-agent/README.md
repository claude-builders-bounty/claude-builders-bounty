# 🤖 Claude PR Review Agent

一个基于Claude API的GitHub PR自动审查工具。

## 功能

- 自动获取PR diff
- 使用Claude AI分析代码变更
- 生成结构化的Markdown审查报告
- 支持CLI直接调用

## 安装

### 1. 克隆仓库
```bash
git clone <repo-url>
cd pr-review-agent
```

### 2. 安装依赖
```bash
pip install anthropic
```

### 3. 配置环境变量
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### 4. 确保已安装GitHub CLI
```bash
gh --version
```

## 使用方法

### 基本用法
```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

### 保存报告到文件
```bash
./claude-review --pr https://github.com/owner/repo/pull/123 --o report.md
```

## 输出格式

工具会生成结构化的Markdown报告：

```markdown
## 🤖 PR Review Report

**PR**: https://github.com/owner/repo/pull/123

### Summary
简要总结PR的主要变更...

### Identified Risks
- 潜在风险1
- 潜在风险2

### Improvement Suggestions
- 改进建议1
- 改进建议2

### Confidence Score
**High**
```

## 测试案例

### 测试1: claude-builders-bounty#152 - PR Review Sub-Agent
```bash
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/152
```

**输出示例**:
```markdown
## 🤖 PR Review Report

**PR**: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/152
**标题**: [Bounty #4] Claude Code PR Review Sub-Agent
**作者**: @plutuscontrol-ui

### Summary
此PR由 plutuscontrol-ui 提交，修改了 5 个文件，新增 706 行，删除 0 行。

### Identified Risks
- ⚠️ 变更量较大，建议分批次审查
- ⚠️ 可能包含敏感信息（password/secret/api_key）

### Improvement Suggestions
- 💡 纯新增代码，建议确保有充分的测试覆盖

### Confidence Score
**Medium**
```

### 测试2: claude-builders-bounty#153 - Safety Hook
```bash
./claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/153 -o report.md
```

完整报告见: [test_report_153.md](test_report_153.md)

## 技术栈

- Python 3.8+
- Anthropic Claude API
- GitHub CLI (gh)

## 许可证

MIT
