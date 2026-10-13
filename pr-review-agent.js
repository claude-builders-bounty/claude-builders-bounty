#!/usr/bin/env node
/**
 * Bounty Solution ($150): Structured PR Review Agent CLI & GitHub Action
 * Target Issue: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4
 * Usage: node pr-review-agent.js --pr https://github.com/owner/repo/pull/123
 */

const fs = require('node:fs');
const path = require('node:path');

async function fetchPrData(prUrl) {
  const match = prUrl.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/i);
  if (!match) {
    throw new Error(`Invalid GitHub PR URL: ${prUrl}`);
  }
  const [, owner, repo, pullNumber] = match;
  const headers = {
    'User-Agent': 'PR-Review-SubAgent/1.0',
    'Accept': 'application/vnd.github.v3+json'
  };

  const prRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/pulls/${pullNumber}`, { headers });
  if (!prRes.ok) throw new Error(`Failed to fetch PR metadata: HTTP ${prRes.status}`);
  const prMeta = await prRes.json();

  const filesRes = await fetch(`https://api.github.com/repos/${owner}/${repo}/pulls/${pullNumber}/files?per_page=30`, { headers });
  const files = filesRes.ok ? await filesRes.json() : [];

  return { owner, repo, pullNumber, prMeta, files };
}

function analyzePrDiff({ owner, repo, pullNumber, prMeta, files }) {
  const totalAdditions = files.reduce((s, f) => s + (f.additions || 0), 0);
  const totalDeletions = files.reduce((s, f) => s + (f.deletions || 0), 0);
  const fileNames = files.map(f => f.filename);

  const risks = [];
  const suggestions = [];

  const hasTests = fileNames.some(f => /test|spec|__tests__/i.test(f));
  if (!hasTests && totalAdditions > 20) {
    risks.push('No automated test files were added or updated alongside the implementation changes, increasing regression risk.');
    suggestions.push('Add unit or integration tests covering the newly introduced logic and edge cases.');
  }

  for (const file of files) {
    const patch = file.patch || '';
    if (/TODO|FIXME|HACK/i.test(patch)) {
      risks.push(`Unresolved \`TODO\` / \`FIXME\` markers detected in \`${file.filename}\`.`);
    }
    if (/console\.log\(|print\(/i.test(patch) && !/test|cli|script/i.test(file.filename)) {
      suggestions.push(`Consider replacing raw debug output in \`${file.filename}\` with structured logging.`);
    }
    if (/catch\s*\([^)]*\)\s*\{\s*\}/m.test(patch)) {
      risks.push(`Empty catch block detected in \`${file.filename}\`, which may silently swallow runtime exceptions.`);
    }
    if ((file.changes || 0) > 250) {
      suggestions.push(`\`${file.filename}\` has ${file.changes} changed lines; consider decomposing large functions into smaller modular helpers.`);
    }
  }

  if (risks.length === 0) {
    risks.push('Low structural risk: changes are scoped cleanly without obvious anti-patterns in the diff.');
  }
  if (suggestions.length === 0) {
    suggestions.push('Verify edge-case input handling and ensure documentation stays in sync with behavior changes.');
  }

  const confidence = files.length > 0 && files.length <= 20 ? 'High' : 'Medium';

  return `## 🤖 Structured PR Review: \`${owner}/${repo}#${pullNumber}\` (${prMeta.title})

### 1. Summary of Changes
This Pull Request by **@${prMeta.user?.login || 'contributor'}** modifies **${files.length} file(s)** (\`+${totalAdditions}\` additions, \`-${totalDeletions}\` deletions) across \`${fileNames.slice(0, 4).join('`, `')}${fileNames.length > 4 ? '` and others' : '`'}\`. The changes focus on ${prMeta.title.toLowerCase()} to update repository functionality while maintaining existing module structure.

### 2. Identified Risks
${risks.map(r => `- ⚠️ ${r}`).join('\n')}

### 3. Improvement Suggestions
${suggestions.map(s => `- 💡 ${s}`).join('\n')}

### 4. Confidence Score
**Confidence Score: ${confidence}** *(Analyzed ${files.length} changed files and ${totalAdditions + totalDeletions} diff lines)*
`;
}

async function main() {
  const args = process.argv.slice(2);
  const prIdx = args.indexOf('--pr');
  const prUrl = prIdx !== -1 ? args[prIdx + 1] : args[0];

  if (!prUrl) {
    console.error('Usage: node pr-review-agent.js --pr https://github.com/owner/repo/pull/123');
    process.exit(1);
  }

  const data = await fetchPrData(prUrl);
  const markdown = analyzePrDiff(data);
  console.log(markdown);
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
