import Anthropic from '@anthropic-ai/sdk';
import { PRInfo, PRDiff, ReviewResult, ReviewConfig } from './types.js';

const SYSTEM_PROMPT = `You are an expert software engineer reviewing a pull request.
Analyze the provided PR metadata and code diff.

Your output must be a valid JSON object matching this schema exactly:
{
  "summary": "2-3 sentences summarizing the changes",
  "risks": [
    {
      "description": "string",
      "severity": "low|medium|high|critical",
      "file": "string (optional)",
      "line": "number (optional)"
    }
  ],
  "suggestions": [
    {
      "description": "string",
      "priority": "low|medium|high",
      "file": "string (optional)",
      "codeSnippet": "string (optional)"
    }
  ],
  "securityNotes": ["string"],
  "confidence": "Low|Medium|High"
}

Ensure the response is ONLY raw JSON. Do not include markdown formatting or extra text.`;

export async function reviewPR(
  pr: PRInfo,
  diff: PRDiff,
  config: ReviewConfig,
  apiKey: string
): Promise<ReviewResult> {
  const anthropic = new Anthropic({ apiKey });

  let depthPrompt = '';
  switch (config.depth) {
    case 'quick':
      depthPrompt = 'Focus only on a brief summary and major risks. Ignore minor suggestions.';
      break;
    case 'deep':
      depthPrompt = 'Perform a deep, line-by-line analysis. Provide detailed code snippets for suggestions.';
      break;
    case 'standard':
    default:
      depthPrompt = 'Perform a standard code review focusing on correctness, performance, and best practices.';
      break;
  }

  const userPrompt = `
Pull Request: ${pr.title}
Branch: ${pr.headBranch} -> ${pr.baseBranch}
Description:
${pr.description}

Files Changed: ${diff.files}
Additions: ${diff.additions}
Deletions: ${diff.deletions}

${depthPrompt}

Diff:
\`\`\`diff
${diff.rawDiff}
\`\`\`
`;

  let retries = 3;
  let delay = 1000;

  while (retries > 0) {
    try {
      const response = await anthropic.messages.create({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 4096,
        system: SYSTEM_PROMPT,
        messages: [{ role: 'user', content: userPrompt }],
      });

      const text = response.content.find(block => block.type === 'text')?.text;
      if (!text) {
        throw new Error('No text returned from Claude');
      }

      // Try to extract JSON if Claude wrapped it in markdown
      let jsonStr = text;
      const jsonMatch = text.match(/\`\`\`(?:json)?\s*([\s\S]*?)\s*\`\`\`/);
      if (jsonMatch) {
        jsonStr = jsonMatch[1];
      }

      return JSON.parse(jsonStr) as ReviewResult;
    } catch (error) {
      retries--;
      if (retries === 0) {
        throw error;
      }
      await new Promise(res => setTimeout(res, delay));
      delay *= 2;
    }
  }

  throw new Error('Failed to analyze PR after retries');
}
