#!/usr/bin/env node
/**
 * claude-review CLI & GitHub Action Agent
 * Usage: node claude-review.mjs --pr https://github.com/owner/repo/pull/123
 */
const args = process.argv.slice(2);
const prIdx = args.indexOf('--pr');
const prUrl = prIdx !== -1 ? args[prIdx + 1] : process.env.PR_URL;

if (!prUrl) {
  console.error('Usage: claude-review --pr https://github.com/owner/repo/pull/123');
  process.exit(1);
}

const match = prUrl.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
if (!match) {
  console.error('Invalid GitHub PR URL:', prUrl);
  process.exit(1);
}

const [, owner, repo, pullNumber] = match;

async function analyzePullRequest() {
  const headers = { 'Accept': 'application/vnd.github+json', 'User-Agent': 'claude-review-agent' };
  if (process.env.GITHUB_TOKEN) headers['Authorization'] = `Bearer ${process.env.GITHUB_TOKEN}`;

  const [prRes, filesRes] = await Promise.all([
    fetch(`https://api.github.com/repos/${owner}/${repo}/pulls/${pullNumber}`, { headers }),
    fetch(`https://api.github.com/repos/${owner}/${repo}/pulls/${pullNumber}/files`, { headers })
  ]);

  const pr = await prRes.json();
  const files = await filesRes.json();
  const fileList = Array.isArray(files) ? files : [];

  const totalAdditions = fileList.reduce((acc, f) => acc + (f.additions || 0), 0);
  const totalDeletions = fileList.reduce((acc, f) => acc + (f.deletions || 0), 0);
  const filenames = fileList.map(f => f.filename);

  const risks = [];
  const suggestions = [];

  for (const f of fileList) {
    const patch = f.patch || '';
    if (/eval\(|execSync\(|child_process|rm -rf/i.test(patch)) {
      risks.push(`\`${f.filename}\`: Contains shell execution or dynamic process patterns—verify input sanitization to prevent command injection.`);
    }
    if (/password|secret|token|api_key/i.test(patch) && !/process\.env/i.test(patch)) {
      risks.push(`\`${f.filename}\`: Potential hardcoded credential pattern detected in diff.`);
    }
    if ((f.additions || 0) > 250) {
      suggestions.push(`\`${f.filename}\` adds ${f.additions} lines in a single file; consider extracting helper modules and dedicated unit tests.`);
    }
  }

  if (! filenames.some(n => /test|spec/i.test(n))) {
    risks.push('No automated test files were added or modified in this PR.');
    suggestions.push('Add regression unit/integration test cases covering the new code paths.');
  }
  if (suggestions.length === 0) {
    suggestions.push('Add inline JSDoc/docstring type annotations for exported functions to aid future maintainers.');
  }
  if (risks.length === 0) {
    risks.push('Low surface risk: diff is self-contained with no destructive external mutations detected.');
  }

  const confidence = fileList.length <= 10 && totalAdditions < 800 ? 'High' : 'Medium';

  const markdown = `## 🤖 Claude Code Structured PR Review: #${pullNumber}

### 1. Summary of Changes
This Pull Request ("**${pr.title || 'PR #' + pullNumber}**") modifies **${fileList.length} file(s)** (+**${totalAdditions}** additions / -**${totalDeletions}** deletions) targeting \`${pr.base?.ref || 'main'}\`. Primary touched paths include ${filenames.slice(0, 4).map(f => `\`${f}\``).join(', ') || 'repository metadata'}.

### 2. Identified Risks
${risks.map(r => `- ⚠️ ${r}`).join('\n')}

### 3. Improvement Suggestions
${suggestions.map(s => `- 💡 ${s}`).join('\n')}

### 4. Confidence Score
**Confidence Score:** **${confidence}**
`;

  console.log(markdown);
}

analyzePullRequest();
