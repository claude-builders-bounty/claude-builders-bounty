#!/usr/bin/env bash
# claude-review.sh — Claude Code PR reviewer with structured Markdown output
# 用法: bash claude-review.sh <PR_URL>
# 依赖: gh, curl, jq

set -euo pipefail

PR_URL="${1:?Usage: bash claude-review.sh <PR_URL>}"

# 解析 PR URL: owner/repo/pull/123
if [[ "$PR_URL" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    PR_NUM="${BASH_REMATCH[3]}"
else
    echo "❌ 无效的 PR URL: $PR_URL"
    echo "格式: https://github.com/owner/repo/pull/123"
    exit 1
fi

echo "📋 正在获取 PR #${PR_NUM} 的 diff..." >&2

# 获取 PR 信息
PR_TITLE=$(gh pr view "$PR_NUM" --repo "$OWNER/$REPO" --json title --jq '.title' 2>/dev/null)
PR_BODY=$(gh pr view "$PR_NUM" --repo "$OWNER/$REPO" --json body --jq '.body' 2>/dev/null | head -c 2000)

# 获取 diff
DIFF=$(gh pr diff "$PR_NUM" --repo "$OWNER/$REPO" 2>/dev/null)

if [ -z "$DIFF" ]; then
    echo "❌ 无法获取 PR diff" >&2
    exit 1
fi

# 截断 diff 避免超出 token 限制
DIFF_LEN=${#DIFF}
if [ "$DIFF_LEN" -gt 15000 ]; then
    DIFF="${DIFF:0:15000}

... [diff truncated at 15000 chars — ${DIFF_LEN} total]"
fi

echo "🔍 正在分析 diff (${DIFF_LEN} chars)..." >&2

# 构建 prompt
PROMPT="You are a senior code reviewer. Analyze this PR and return a structured review.

## PR Info
- Repository: ${OWNER}/${REPO}
- PR #${PR_NUM}: ${PR_TITLE}

## PR Description
${PR_BODY}

## Diff
\`\`\`
${DIFF}
\`\`\`

## Required Output Format

Return EXACTLY this Markdown structure (no extra text before or after):

### Summary
[2-3 sentences describing what this PR does]

### Risks
- [risk 1]
- [risk 2]
- [risk N or 'None identified']

### Suggestions
- [suggestion 1]
- [suggestion 2]
- [suggestion N or 'Looks good']

### Confidence
[Low / Medium / High]

Be concise. Focus on real issues, not style nitpicks."

# 调用 Claude API
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "❌ 需要设置 ANTHROPIC_API_KEY 环境变量" >&2
    echo "export ANTHROPIC_API_KEY=sk-ant-..." >&2
    exit 1
fi

RESPONSE=$(curl -s https://api.anthropic.com/v1/messages \
    -H "x-api-key: ${ANTHROPIC_API_KEY}" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d "$(jq -n \
        --arg prompt "$PROMPT" \
        '{
            model: "claude-sonnet-4-20250514",
            max_tokens: 1024,
            messages: [{role: "user", content: $prompt}]
        }'
    )" 2>/dev/null)

# 提取回复内容
REVIEW=$(echo "$RESPONSE" | jq -r '.content[0].text // empty' 2>/dev/null)

if [ -z "$REVIEW" ]; then
    echo "❌ Claude API 调用失败" >&2
    echo "$RESPONSE" | jq '.' 2>/dev/null >&2
    exit 1
fi

# 输出结构化 review
echo "$REVIEW"
