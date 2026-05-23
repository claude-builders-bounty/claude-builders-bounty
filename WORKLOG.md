# Claude Builders Bounty #4 工作记录

## 目标
Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4
Bounty: $150 Opire
任务: Claude Code PR Review Agent，CLI 读取 PR diff，输出结构化 Markdown review；可选 GitHub Action。

## 验收标准
- CLI: `claude-review --pr https://github.com/owner/repo/pull/123`
- 或 GitHub Action/workflow YAML
- Markdown 包含：Summary、Identified risks、Improvement suggestions、Confidence score: Low/Medium/High
- 至少 2 个真实 GitHub PR 测试输出
- README setup/usage

## 竞品侦察 2026-05-23
主仓库 main 当前几乎为空：README.md + LICENSE。提交形态基本是新增独立 agent/tool。

强相关 PR:
- #1990 hikali123456789: 447 additions, 5 files。根目录 `claude-review` + GitHub workflow + README，偏 stdlib heuristic，混入 hooks/pre-tool-use，疑似不够聚焦。
- #1988 sureshchouksey8: 897 additions, 17 files。`agents/pr-reviewer` 但混入多个其他 bounty（destructive hook/changelog/template），PR 不干净。
- #1973 0xN404T: 263 additions, 5 files。CLI + optional --post + action example + two samples，比较干净但实现规模较小。
- #1961 kebanks2: 652 additions, 8 files。含 `.claude/agents/pr-reviewer.md`、CLI wrapper、GitHub Action 示例、samples、tests。当前最接近“正经 Claude Code sub-agent”的强竞品。
- #1945 Terrajlz: CLI + Action + litellm samples，需要 anthropic，较常规。
- #1933 ai-hustle-bro: Anthropic SDK + gh CLI，README 包 workflow YAML，较常规。

## 差异化方向
不要只做 checklist。要做成“模型后端可切换 + Claude Code agent 定义 + 可复现样例 + 测试”的精品提交。

拟定交付:
- 目录: `agents/claude-review-multimodel/`
- CLI wrapper: `agents/claude-review-multimodel/claude-review`
- Python CLI: `agents/claude-review-multimodel/claude_review.py`
- Claude Code sub-agent: `.claude/agents/pr-reviewer.md`
- GitHub Action 示例: `agents/claude-review-multimodel/github-action/claude-review.yml`
- README
- tests
- examples/ 两个真实 PR 输出
- 可选: docs/benchmark.md 记录多后端测试结果

核心卖点:
1. Backends: `claude-cli` 优先，`anthropic` API 可选，`heuristic` fallback。必要时支持 `--backend auto|claude-cli|anthropic|heuristic`。
2. 输入: PR URL、owner/repo#num、本地 diff 文件。
3. 大 diff 处理: 文件级摘要 + 字符预算截断，避免模型上下文爆。
4. 输出: 固定 Markdown section + Confidence rationale。
5. `--post-comment` 可将 review 发回 PR（需要 GITHUB_TOKEN）。
6. `--model` 参数用于多模型/多后端测试。

## 复盘点
最终无论是否合并，记录：
- 维护者是否反馈偏好 Claude CLI / API / Action 哪种形态
- 哪些 PR 被关闭或合并
- 我们的差异化是否被认可
- 多模型输出中哪类 prompt 最稳
