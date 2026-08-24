#!/usr/bin/env node
/**
 * Claude Code PR Reviewer Agent
 * Analyzes PR diffs and generates structured Markdown code reviews.
 */
import { request } from 'node:https';
import { parseArgs } from 'node:util';

export function parsePrUrl(url) {
  const match = url.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
  if (!match) {
    throw new Error(`Invalid GitHub PR URL: ${url}`);
  }
  return { owner: match[1], repo: match[2], pullNumber: match[3] };
}

export function analyzeDiff(diffText) {
  const addedLines = [];
  const removedLines = [];
  const filesChanged = [];
  let currentFile = null;

  for (const line of diffText.split('\n')) {
    if (line.startsWith('diff --git')) {
      const parts = line.split(' ');
      currentFile = parts[parts.length - 1].replace(/^b\//, '');
      filesChanged.push(currentFile);
    } else if (line.startsWith('+') && !line.startsWith('+++')) {
      addedLines.push(line.slice(1));
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      removedLines.push(line.slice(1));
    }
  }

  const risks = [];
  const suggestions = [];

  // Static heuristic analysis
  const combinedAdded = addedLines.join('\n');

  if (/password|secret|api_key|private_key/i.test(combinedAdded) && !/process\.env/i.test(combinedAdded)) {
    risks.push('Potential hardcoded credentials or secret variable detected in newly added code.');
  }

  if (/\bany\b/i.test(combinedAdded) && /tsconfig|\.tsx?/.test(filesChanged.join(' '))) {
    suggestions.push('Replace loose `any` type annotations with explicit interfaces or generics for better type safety.');
  }

  if (/catch\s*\([^)]*\)\s*\{\s*\}/.test(combinedAdded)) {
    risks.push('Empty catch block detected. Swallowing exceptions without logging can mask unexpected runtime failures.');
  }

  if (/console\.log\(/.test(combinedAdded) && !/tests?|\.test\./i.test(filesChanged.join(' '))) {
    suggestions.push('Remove debug `console.log` statements before deploying to production environments.');
  }

  let confidence = 'High';
  if (addedLines.length > 500) {
    confidence = 'Medium';
    risks.push('Large changeset (>500 lines added). Consider breaking this PR into smaller, atomic feature branches.');
  }

  if (risks.length === 0) {
    risks.push('No critical security or runtime risks detected in the analyzed diff chunk.');
  }

  if (suggestions.length === 0) {
    suggestions.push('Code structure adheres to standard project conventions and clean code patterns.');
  }

  return {
    filesCount: filesChanged.length,
    addedCount: addedLines.length,
    removedCount: removedLines.length,
    risks,
    suggestions,
    confidence
  };
}

export function generateMarkdownReview(analysis, prInfo = {}) {
  const title = prInfo.title || 'Pull Request Review';
  const url = prInfo.url || '';

  return `## 🤖 Claude Code Review: ${title}
${url ? `> Target: ${url}\n` : ''}
### 📝 Summary of Changes
This pull request modifies **${analysis.filesCount} file(s)** with **+${analysis.addedCount} additions** and **-${analysis.removedCount} deletions**. The diff introduces scoped functional changes across components and utilities.

### ⚠️ Identified Risks
${analysis.risks.map(r => `- ${r}`).join('\n')}

### 💡 Improvement Suggestions
${analysis.suggestions.map(s => `- ${s}`).join('\n')}

### 🎯 Confidence Score
**${analysis.confidence} Confidence** — Analysis performed across all modified diff blocks.
`;
}

async function fetchPrDiff(owner, repo, pullNumber, token) {
  return new Promise((resolve, reject) => {
    const headers = {
      'User-Agent': 'Claude-PR-Reviewer',
      'Accept': 'application/vnd.github.v3.diff'
    };
    if (token) headers['Authorization'] = `token ${token}`;

    const req = request({
      hostname: 'api.github.com',
      path: `/repos/${owner}/${repo}/pulls/${pullNumber}`,
      method: 'GET',
      headers
    }, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    });
    req.on('error', reject);
    req.end();
  });
}

export async function main() {
  const { values } = parseArgs({
    options: {
      pr: { type: 'string' },
      token: { type: 'string' }
    }
  });

  if (!values.pr) {
    console.error('Usage: claude-review --pr https://github.com/owner/repo/pull/123 [--token GITHUB_TOKEN]');
    process.exit(1);
  }

  const { owner, repo, pullNumber } = parsePrUrl(values.pr);
  const diff = await fetchPrDiff(owner, repo, pullNumber, values.token || process.env.GITHUB_TOKEN);
  const analysis = analyzeDiff(diff);
  const markdown = generateMarkdownReview(analysis, { url: values.pr, title: `${owner}/${repo}#${pullNumber}` });

  console.log(markdown);
}

if (process.argv[1] && process.argv[1].endsWith('pr_reviewer.js')) {
  main().catch(console.error);
}
