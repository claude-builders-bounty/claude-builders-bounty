## Review: https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4455

### Summary
该 PR 新增了一个基于关键词/正则的 PR diff 审查脚本 claude_review.py，并配套了一个位于 agents/claude-pr-review/.github/workflows/claude-pr-review.yml 的 GitHub Actions 工作流。 该工作流文件路径不在仓库根目录的 .github/workflows/ 下，因此按 diff 所示位置不会被 GitHub Actions 实际触发，与 README 中'自动审查 PR'的说法不符。 脚本本身仅做字符串/正则统计（如文件路径关键词匹配、eval(/password= 等模式检测），并未调用任何 Claude 或 LLM 能力，与 README 中'Claude PR Review Agent'及'sub-agent for Claude Code'的描述存在功能落差；此外文件名解析逻辑存在 lstrip 误用的 bug。

### Risks
- **Medium** `agents/claude-pr-review/.github/workflows/claude-pr-review.yml`: 工作流文件位于 agents/claude-pr-review/.github/workflows/claude-pr-review.yml，而非仓库根目录的 .github/workflows/ 下，GitHub Actions 只会加载仓库根目录 .github/workflows/ 中的工作流文件，按此位置该工作流不会被触发，README 中"Auto-review incoming PRs"的说明与实际代码位置不符。
- **Medium** `agents/claude-pr-review/claude_review.py`: claude_review.py 的 analyze_diff 函数仅通过路径关键词匹配和简单正则（如 eval(、password=）做启发式判断，并未接入任何 Claude/LLM 分析能力，但 README 描述其为"Claude PR Review Agent"、"sub-agent for Claude Code"并宣称能检测"security regressions"等，功能与文档描述存在明显落差，可能误导使用者高估其审查能力。
- **Low** `agents/claude-pr-review/claude_review.py（parse file_path 处，约第 97 行附近）`: file_path = parts[3].lstrip("b/") 使用了 str.lstrip，该方法会从字符串开头移除所有属于字符集合 {'b','/'} 的字符，而非精确去除前缀 "b/"。例如路径 b/backend/x.js 会被错误地处理成 ackend/x.js，导致展示的文件名被破坏，也可能影响后续 test/敏感路径关键词匹配的准确性。
- **Low** `agents/claude-pr-review/claude_review.py（analyze_diff 函数中 potential_risks.append 循环处）`: potential_risks 列表在遍历每一行新增代码时，只要匹配到 eval(/exec(/password=/api_key=/secret= 等模式就会重复 append 相同的风险描述，没有去重逻辑，当 diff 中存在多处匹配时会在最终 Markdown 输出中产生重复的风险条目。

### Improvement suggestions
- 将 workflow 文件从 agents/claude-pr-review/.github/workflows/claude-pr-review.yml 移动到仓库根目录的 .github/workflows/ 下，以确保其能被 GitHub Actions 实际触发，或在 README 中明确说明当前示例的局限性/需要用户自行复制到根目录。
- 将 README 中关于"Claude PR Review Agent"、"分析安全回归"等描述与脚本实际的关键词/正则启发式实现对齐，避免过度宣称其分析能力，或者后续接入真实的 LLM 调用以匹配文档描述。
- 修复 parts[3].lstrip("b/") 的用法，改为 parts[3].removeprefix("b/")（或等效的字符串切片方式），避免误删非 'b/' 前缀之外的字符。
- 对 potential_risks 列表在 append 前做去重处理，避免同一类风险因多行匹配而在最终评论中重复出现。

**Confidence:** High
