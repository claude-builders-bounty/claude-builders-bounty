import Anthropic from '@anthropic-ai/sdk';

interface ReviewOptions {
  apiKey?: string;
  githubToken?: string;
}

interface PRInfo {
  owner: string;
  repo: string;
  number: number;
}

function parsePRUrl(url: string): PRInfo {
  const match = url.match(/github\.com\/([^\/]+)\/([^\/]+)\/pull\/(\d+)/);
  if (!match) {
    throw new Error('Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123');
  }
  return { owner: match[1], repo: match[2], number: parseInt(match[3]) };
}

async function fetchPRDiff(info: PRInfo, token?: string): Promise<string> {
  const headers: Record<string, string> = {
    'Accept': 'application/vnd.github.v3.diff'
  };
  if (token) {
    headers['Authorization'] = `token ${token}`;
  }

  const response = await fetch(
    `https://api.github.com/repos/${info.owner}/${info.repo}/pulls/${info.number}`,
    { headers }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch PR: ${response.status} ${response.statusText}`);
  }

  return response.text();
}

export async function reviewPR(prUrl: string, options: ReviewOptions): Promise<string> {
  if (!options.apiKey) {
    throw new Error('Anthropic API key required. Set ANTHROPIC_API_KEY env var or use --api-key');
  }

  const info = parsePRUrl(prUrl);
  const diff = await fetchPRDiff(info, options.githubToken);

  const anthropic = new Anthropic({ apiKey: options.apiKey });

  const response = await anthropic.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 4096,
    system: `You are a code review assistant. Analyze the PR diff and provide a structured review in Markdown format.

Your review must include:

## Summary
2-3 sentences describing what this PR does.

## Identified Risks
- List potential issues, bugs, or security concerns
- Be specific about code patterns that could cause problems

## Improvement Suggestions
- List specific improvements with line references where possible
- Include best practices or performance optimizations

## Confidence Score
**Confidence: Low / Medium / High**

Explain briefly why you chose this confidence level.`,
    messages: [{
      role: 'user',
      content: `Please review this PR diff from ${info.owner}/${info.repo}#${info.number}:

\`\`\`diff
${diff.slice(0, 100000)}
\`\`\`

Provide a structured Markdown review as specified.`
    }]
  });

  const content = response.content[0];
  if (content.type !== 'text') {
    throw new Error('Unexpected response type from Claude');
  }

  return content.text;
}