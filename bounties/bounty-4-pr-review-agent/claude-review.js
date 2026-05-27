#!/usr/bin/env node
/**
 * claude-review — AI-powered PR review CLI
 * 
 * Usage:
 *   claude-review --pr https://github.com/owner/repo/pull/123
 *   claude-review --owner owner --repo repo --pr-number 123
 * 
 * Outputs a structured Markdown review comment.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ─── Argument Parsing ────────────────────────────────────────────────
function parseArgs() {
  const args = process.argv.slice(2);
  const opts = { owner: '', repo: '', prNumber: '', token: '' };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--pr': {
        const url = args[++i];
        const match = url.match(/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/);
        if (!match) {
          console.error('Invalid PR URL. Expected: https://github.com/owner/repo/pull/123');
          process.exit(1);
        }
        opts.owner = match[1];
        opts.repo = match[2];
        opts.prNumber = match[3];
        break;
      }
      case '--owner': opts.owner = args[++i]; break;
      case '--repo': opts.repo = args[++i]; break;
      case '--pr-number': opts.prNumber = args[++i]; break;
      case '--token': opts.token = args[++i]; break;
      case '--help':
        console.log(`
claude-review — AI-powered PR review

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --owner owner --repo repo --pr-number 123

Options:
  --pr URL         PR URL (e.g. https://github.com/owner/repo/pull/123)
  --owner OWNER    Repository owner
  --repo REPO      Repository name
  --pr-number NUM  PR number
  --token TOKEN    GitHub token (or set GITHUB_TOKEN env var)
  --help           Show this help
`);
        process.exit(0);
      default:
        console.error(`Unknown option: ${args[i]}`);
        process.exit(1);
    }
  }

  if (!opts.owner || !opts.repo || !opts.prNumber) {
    console.error('Error: --pr URL is required (or --owner/--repo/--pr-number)');
    process.exit(1);
  }

  opts.token = opts.token || process.env.GITHUB_TOKEN || '';
  return opts;
}

// ─── GitHub API Helper ───────────────────────────────────────────────
function githubApi(url, token, method = 'GET', body = null) {
  const cmd = [
    'curl', '-s',
    '-X', method,
    '-H', `"Authorization: token ${token}"`,
    '-H', '"Accept: application/vnd.github.v3+json"',
    '-H', '"Content-Type: application/json"',
  ];

  if (body) {
    const tmpFile = path.join(require('os').tmpdir(), `gh-review-body-${Date.now()}.json`);
    fs.writeFileSync(tmpFile, JSON.stringify(body));
    cmd.push('-d', `@${tmpFile}`);
  }

  cmd.push(`"https://api.github.com${url}"`);

  const result = execSync(cmd.join(' '), { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 });
  return JSON.parse(result);
}

// ─── Fetch PR Data ───────────────────────────────────────────────────
function fetchPRData(opts) {
  console.log(`Fetching PR #${opts.prNumber} from ${opts.owner}/${opts.repo}...`);

  // Get PR details
  const pr = githubApi(`/repos/${opts.owner}/${opts.repo}/pulls/${opts.prNumber}`, opts.token);
  
  // Get PR diff
  const diffCmd = [
    'curl', '-s',
    '-H', `"Authorization: token ${opts.token}"`,
    '-H', '"Accept: application/vnd.github.v3.diff"',
    `"https://api.github.com/repos/${opts.owner}/${opts.repo}/pulls/${opts.prNumber}"`,
  ];
  const diff = execSync(diffCmd.join(' '), { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 });

  // Get changed files
  const files = githubApi(
    `/repos/${opts.owner}/${opts.repo}/pulls/${opts.prNumber}/files?per_page=100`,
    opts.token
  );

  // Get commits
  const commits = githubApi(
    `/repos/${opts.owner}/${opts.repo}/pulls/${opts.prNumber}/commits?per_page=100`,
    opts.token
  );

  return { pr, diff, files, commits };
}

// ─── Analyze PR ──────────────────────────────────────────────────────
function analyzePR(data) {
  const { pr, diff, files, commits } = data;

  const analysis = {
    title: pr.title || '',
    author: (pr.user && pr.user.login) || 'unknown',
    additions: pr.additions || 0,
    deletions: pr.deletions || 0,
    changedFiles: (files && files.length) || 0,
    fileNames: (files || []).map(f => f.filename),
    commitCount: (commits && commits.length) || 0,
    baseBranch: (pr.base && pr.base.ref) || 'main',
    headBranch: (pr.head && pr.head.ref) || 'unknown',
    body: pr.body || '',
  };

  // Analyze file types
  analysis.fileTypes = {};
  for (const f of files || []) {
    const ext = path.extname(f.filename).toLowerCase();
    analysis.fileTypes[ext] = (analysis.fileTypes[ext] || 0) + 1;
  }

  // Risk analysis
  analysis.risks = detectRisks(files, diff, analysis);

  // Improvement suggestions
  analysis.suggestions = detectSuggestions(files, diff, analysis);

  return analysis;
}

// ─── Risk Detection ──────────────────────────────────────────────────
function detectRisks(files, diff, analysis) {
  const risks = [];

  if (!files || !Array.isArray(files)) return risks;

  for (const file of files) {
    const fn = file.filename.toLowerCase();

    // Security-sensitive files
    if (fn.includes('auth') || fn.includes('password') || fn.includes('token') || fn.includes('secret')) {
      risks.push({
        level: 'HIGH',
        file: file.filename,
        message: 'Authentication/security-related change — verify no credentials are exposed',
      });
    }

    // Database migrations
    if (fn.includes('migration') || fn.includes('schema')) {
      risks.push({
        level: 'MEDIUM',
        file: file.filename,
        message: 'Database schema change — verify migration is reversible and non-destructive',
      });
    }

    // Configuration files
    if (fn.includes('.env') || fn === 'docker-compose.yml' || fn.includes('config')) {
      risks.push({
        level: 'MEDIUM',
        file: file.filename,
        message: 'Configuration change — verify no secrets are committed',
      });
    }

    // Large files
    if (file.additions && file.additions > 300) {
      risks.push({
        level: 'LOW',
        file: file.filename,
        message: `Large addition (${file.additions} lines) — consider splitting into smaller PRs`,
      });
    }
  }

  // Overall PR size risk
  if (analysis.additions + analysis.deletions > 1000) {
    risks.push({
      level: 'MEDIUM',
      file: '(overall)',
      message: `Large PR (${analysis.additions} additions, ${analysis.deletions} deletions) — consider breaking into smaller PRs for easier review`,
    });
  }

  // Check diff for common risky patterns
  if (diff) {
    const lines = diff.split('\n');
    for (const line of lines) {
      if (line.startsWith('+')) {
        // Check for common risky patterns
        if (line.match(/eval\s*\(/)) {
          risks.push({ level: 'HIGH', file: '(diff)', message: '`eval()` usage detected — security risk' });
        }
        if (line.match(/innerHTML/)) {
          risks.push({ level: 'HIGH', file: '(diff)', message: '`innerHTML` usage detected — XSS risk' });
        }
        if (line.match(/console\.log/)) {
          risks.push({ level: 'LOW', file: '(diff)', message: '`console.log` found — remove before merging' });
        }
        if (line.match(/TODO|FIXME|HACK/)) {
          risks.push({ level: 'LOW', file: '(diff)', message: 'TODO/FIXME/HACK comment found — ensure it is tracked' });
        }
      }
    }
  }

  return risks;
}

// ─── Suggestion Detection ────────────────────────────────────────────
function detectSuggestions(files, diff, analysis) {
  const suggestions = [];

  if (!files || !Array.isArray(files)) return suggestions;

  // Check for missing tests
  const hasTests = files.some(f => 
    f.filename.includes('.test.') || f.filename.includes('.spec.') || f.filename.includes('__tests__')
  );
  const hasCode = files.some(f => 
    !f.filename.includes('.test.') && !f.filename.includes('.spec.') &&
    (f.filename.endsWith('.ts') || f.filename.endsWith('.js') || f.filename.endsWith('.py'))
  );
  if (hasCode && !hasTests) {
    suggestions.push('No test files found in this PR — consider adding tests for new functionality');
  }

  // Check for missing documentation
  const hasDocs = files.some(f => f.filename.endsWith('.md'));
  if (analysis.changedFiles > 5 && !hasDocs) {
    suggestions.push('Multiple files changed but no documentation updates — consider updating relevant docs');
  }

  // Check diff for patterns
  if (diff) {
    const lines = diff.split('\n');
    let hasErrorHandling = false;
    let hasTryCatch = false;
    
    for (const line of lines) {
      if (line.startsWith('+')) {
        if (line.match(/catch|\.catch|try\s*{/)) hasTryCatch = true;
        if (line.match(/\.then|await/)) hasErrorHandling = true;
      }
    }

    if (hasErrorHandling && !hasTryCatch) {
      suggestions.push('Async operations detected but no error handling — consider adding try/catch');
    }
  }

  // Large PR suggestion
  if (analysis.changedFiles > 15) {
    suggestions.push(`${analysis.changedFiles} files changed — consider grouping related changes into separate PRs`);
  }

  return suggestions;
}

// ─── Generate Review Comment ─────────────────────────────────────────
function generateReview(analysis) {
  const lines = [];

  lines.push('## 🤖 Automated PR Review');
  lines.push('');
  lines.push(`**PR**: ${analysis.title}`);
  lines.push(`**Author**: @${analysis.author}`);
  lines.push(`**Branch**: \`${analysis.headBranch}\` → \`${analysis.baseBranch}\``);
  lines.push('');

  // Summary
  lines.push('### 📋 Summary');
  lines.push('');
  
  const totalChanges = analysis.additions + analysis.deletions;
  let summary = `This PR makes ${totalChanges} line changes across ${analysis.changedFiles} file(s)`;
  summary += ` (${analysis.additions} additions, ${analysis.deletions} deletions)`;
  summary += ` in ${analysis.commitCount} commit(s).`;
  lines.push(summary);
  lines.push('');

  if (analysis.fileNames.length > 0 && analysis.fileNames.length <= 10) {
    lines.push('**Changed files**: ' + analysis.fileNames.map(f => `\`${f}\``).join(', '));
    lines.push('');
  } else if (analysis.fileNames.length > 10) {
    lines.push('**Changed files** (first 10): ' + 
      analysis.fileNames.slice(0, 10).map(f => `\`${f}\``).join(', ') + 
      ` and ${analysis.fileNames.length - 10} more`);
    lines.push('');
  }

  // File type breakdown
  if (Object.keys(analysis.fileTypes).length > 0) {
    lines.push('**File types**: ' + 
      Object.entries(analysis.fileTypes).map(([ext, count]) => `${ext || 'none'} (${count})`).join(', '));
    lines.push('');
  }

  // Risks
  lines.push('### ⚠️ Identified Risks');
  lines.push('');
  
  if (analysis.risks.length === 0) {
    lines.push('No significant risks identified.');
  } else {
    const highRisks = analysis.risks.filter(r => r.level === 'HIGH');
    const medRisks = analysis.risks.filter(r => r.level === 'MEDIUM');
    const lowRisks = analysis.risks.filter(r => r.level === 'LOW');

    if (highRisks.length > 0) {
      lines.push('**🔴 High Priority**');
      for (const r of highRisks) {
        lines.push(`- [ ] \`${r.file}\`: ${r.message}`);
      }
      lines.push('');
    }
    if (medRisks.length > 0) {
      lines.push('**🟡 Medium Priority**');
      for (const r of medRisks) {
        lines.push(`- [ ] \`${r.file}\`: ${r.message}`);
      }
      lines.push('');
    }
    if (lowRisks.length > 0) {
      lines.push('**🟢 Low Priority**');
      for (const r of lowRisks) {
        lines.push(`- [ ] \`${r.file}\`: ${r.message}`);
      }
      lines.push('');
    }
  }

  // Suggestions
  lines.push('### 💡 Improvement Suggestions');
  lines.push('');
  
  if (analysis.suggestions.length === 0) {
    lines.push('No specific suggestions — the PR looks clean!');
  } else {
    for (const s of analysis.suggestions) {
      lines.push(`- ${s}`);
    }
  }
  lines.push('');

  // Confidence score
  lines.push('### 🎯 Confidence Score');
  lines.push('');
  
  let confidence = 'High';
  let reason = 'Small, focused PR with clear changes.';
  
  if (analysis.risks.filter(r => r.level === 'HIGH').length > 0) {
    confidence = 'Low';
    reason = 'High-priority risks detected that need attention.';
  } else if (analysis.risks.filter(r => r.level === 'MEDIUM').length > 1) {
    confidence = 'Medium';
    reason = 'Multiple medium-priority risks detected.';
  } else if (analysis.additions + analysis.deletions > 500) {
    confidence = 'Medium';
    reason = 'Large PR — harder to review thoroughly.';
  }
  
  lines.push(`**${confidence}** — ${reason}`);
  lines.push('');

  // Footer
  lines.push('---');
  lines.push('*This review was generated by `claude-review` — an automated PR review agent.*');

  return lines.join('\n');
}

// ─── Main ────────────────────────────────────────────────────────────
function main() {
  const opts = parseArgs();

  if (!opts.token) {
    console.error('Error: GitHub token required. Set GITHUB_TOKEN env var or use --token');
    process.exit(1);
  }

  const data = fetchPRData(opts);
  const analysis = analyzePR(data);
  const review = generateReview(analysis);

  console.log('\n' + review);

  // Optionally save to file
  const outputPath = path.join(process.cwd(), `review-${opts.owner}-${opts.repo}-${opts.prNumber}.md`);
  fs.writeFileSync(outputPath, review, 'utf-8');
  console.log(`\n📄 Review saved to: ${outputPath}`);
}

main();
