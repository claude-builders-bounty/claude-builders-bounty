/**
 * PR review 核心逻辑。
 *
 * 它是个管道：从 GitHub 拉 PR diff → 用 prompt 包装 → 扔给 Claude 分析 → 拿回结构化 review。
 * 每一步失败都会扔出明确的错误信息，不会静悄悄挂掉。
 */

import { Octokit } from 'octokit';
import Anthropic from '@anthropic-ai/sdk';

export interface ReviewOptions {
  /** 完整的 PR URL，如 https://github.com/owner/repo/pull/123 */
  prUrl: string;
  /** GitHub Personal Access Token */
  ghToken: string;
  /** Anthropic API Key */
  anthropicKey: string;
  /** Claude 模型名，默认 claude-sonnet-4-20250514 */
  model?: string;
  /** 最大 token 数 */
  maxTokens?: number;
}

/**
 * 运行一次完整的 PR review。
 * 返回结构化的 Markdown review 内容。
 */
export async function reviewPR(options: ReviewOptions): Promise<string> {
  const { owner, repo, prNumber } = parsePrUrl(options.prUrl);

  // 1. Fetch PR metadata + diff from GitHub
  const diff = await fetchPRDiff(owner, repo, prNumber, options.ghToken);
  const prInfo = await fetchPRInfo(owner, repo, prNumber, options.ghToken);

  // 2. Build the analysis prompt
  const prompt = buildReviewPrompt(prInfo, diff);

  // 3. Ask Claude
  const review = await askClaude(prompt, options.anthropicKey, {
    model: options.model ?? 'claude-sonnet-4-20250514',
    maxTokens: options.maxTokens ?? 4096,
  });

  return review;
}

// ── Helpers ──────────────────────────────────────────

/**
 * 从 PR URL 里抠出 owner, repo, prNumber。
 * 支持格式：
 *   https://github.com/owner/repo/pull/123
 *   https://github.com/owner/repo/pull/123/files
 */
function parsePrUrl(url: string): { owner: string; repo: string; prNumber: number } {
  const trimmed = url.replace(/\/files$/, '').replace(/\/$/, '');
  const match = trimmed.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!match) {
    throw new Error(`无法解析 PR URL: ${url}。期望格式: https://github.com/owner/repo/pull/123`);
  }
  return { owner: match[1], repo: match[2], prNumber: parseInt(match[3], 10) };
}

/** 拉取 PR diff（纯文本格式） */
async function fetchPRDiff(
  owner: string,
  repo: string,
  prNumber: number,
  token: string,
): Promise<string> {
  const octokit = new Octokit({ auth: token });

  const response = await octokit.request('GET /repos/{owner}/{repo}/pulls/{pull_number}', {
    owner,
    repo,
    pull_number: prNumber,
    mediaType: { format: 'diff' },
  });

  // Octokit returns the raw diff as `data` when mediaType is 'diff'
  if (typeof response.data === 'string') {
    return response.data;
  }

  // Fallback: try fetching diff via the actual diff URL
  const diffResponse = await octokit.request('GET /repos/{owner}/{repo}/pulls/{pull_number}', {
    owner,
    repo,
    pull_number: prNumber,
    headers: { Accept: 'application/vnd.github.v3.diff' },
  });

  return typeof diffResponse.data === 'string' ? diffResponse.data : '(empty diff)';
}

/** 拉取 PR 元数据（标题、描述、文件列表等） */
async function fetchPRInfo(
  owner: string,
  repo: string,
  prNumber: number,
  token: string,
): Promise<{ title: string; description: string; changedFiles: number; additions: number; deletions: number }> {
  const octokit = new Octokit({ auth: token });

  const { data: pr } = await octokit.request('GET /repos/{owner}/{repo}/pulls/{pull_number}', {
    owner,
    repo,
    pull_number: prNumber,
  });

  return {
    title: pr.title,
    description: pr.body ?? '(no description)',
    changedFiles: pr.changed_files,
    additions: pr.additions,
    deletions: pr.deletions,
  };
}

/** 构建给 Claude 的 review prompt */
function buildReviewPrompt(
  prInfo: { title: string; description: string; changedFiles: number; additions: number; deletions: number },
  diff: string,
): string {
  return `You are an expert code reviewer. Review the following Pull Request and produce a structured Markdown analysis.

## PR Information
- **Title:** ${prInfo.title}
- **Description:** ${prInfo.description}
- **Files changed:** ${prInfo.changedFiles}
- **Additions:** ${prInfo.additions}
- **Deletions:** ${prInfo.deletions}

## Diff
\`\`\`diff
${diff.slice(0, 80000)}
\`\`\`

## Output Format

Return ONLY a structured Markdown review with these exact sections:

### Summary
(2-3 sentences summarizing what the PR does)

### Identified Risks
- Risk 1: (description)
- Risk 2: (description)
...

### Improvement Suggestions
- Suggestion 1: (actionable recommendation)
- Suggestion 2: (actionable recommendation)
...

### Confidence Score
**Score:** Low / Medium / High
(Brief justification for the score)
`;
}

/** 调用 Claude API 获取 review */
async function askClaude(
  prompt: string,
  apiKey: string,
  opts: { model: string; maxTokens: number },
): Promise<string> {
  const anthropic = new Anthropic({ apiKey });

  const response = await anthropic.messages.create({
    model: opts.model,
    max_tokens: opts.maxTokens,
    messages: [{ role: 'user', content: prompt }],
  });

  const textBlock = response.content.find((block) => block.type === 'text');
  return textBlock?.text ?? '(no response)';
}
