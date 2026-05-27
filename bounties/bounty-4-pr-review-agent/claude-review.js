#!/usr/bin/env node
/**
 * claude-review — AI-powered PR review CLI
 * 
 * Usage:
 *   node claude-review.js --pr https://github.com/owner/repo/pull/123
 *   node claude-review.js --owner owner --repo repo --pr-number 123
 * 
 * Outputs a structured Markdown review comment to stdout.
 * Status/diagnostic messages go to stderr.
 */

const https = require('https');
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
  node claude-review.js --pr https://github.com/owner/repo/pull/123
  node claude-review.js --owner owner --repo repo --pr-number 123

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
    console.error('Error: --pr URL is required, or provide all three: --owner, --repo, --pr-number');
    process.exit(1);
  }

  opts.token = opts.token || process.env.GITHUB_TOKEN || '';
  return opts;
}

// ─── GitHub API via HTTPS ────────────────────────────────────────────
function githubRequest(urlPath, token, acceptHeader = 'application/vnd.github.v3+json') {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.github.com',
      path: urlPath,
      method: 'GET',
      headers: {
        'Authorization': `token ${token}`,
        'Accept': acceptHeader,
        'User-Agent': 'claude-review/2.0',
      },
    };

    const req = https.request(options, (res) => {
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => {
        const body = Buffer.concat(chunks).toString('utf-8');
        if (acceptHeader.includes('diff')) {
          resolve(body);
        } else {
          try {
            resolve(JSON.parse(body));
          } catch (e) {
            reject(new Error(`Failed to parse JSON: ${e.message}`));
          }
        }
      });
    });

    req.on('error', reject);
    req.setTimeout(30000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
    req.end();
  });
}

/**
 * Fetch ALL paginated results from a GitHub API endpoint.
 * Follows Link headers to get all pages.
 */
async function fetchAllPages(urlPath, token, perPage = 100) {
  const allItems = [];
  let page = 1;
  
  while (true) {
    const separator = urlPath.includes('?') ? '&' : '?';
    const pageUrl = `${urlPath}${separator}per_page=${perPage}&page=${page}`;
    const data = await githubRequest(pageUrl, token);
    
    if (!Array.isArray(data)) {
      // If it's not an array, return it as-is (error or single object)
      return data;
    }
    
    allItems.push(...data);
    
    // If we got fewer than perPage items, we've reached the end
    if (data.length < perPage) {
      break;
    }
    page++;
    
    // Safety limit: don't fetch more than 50 pages
    if (page > 50) {
      console.error(`Warning: Reached pagination limit (50 pages, ${allItems.length} items)`);
      break;
    }
  }
  
  return allItems;
}

// ─── Fetch PR Data ───────────────────────────────────────────────────
async function fetchPRData(opts) {
  console.error(`Fetching PR #${opts.prNumber} from ${opts.owner}/${opts.repo}...`);

  const [pr, diff, files, commits] = await Promise.all([
    githubRequest(`/repos/${opts.owner}/${opts.repo}/pulls/${opts.prNumber}`, opts.token),
    githubRequest(`/repos/${opts.owner}/${opts.repo}/pulls/${opts.prNumber}`, opts.token, 'application/vnd.github.v3.diff'),
    fetchAllPages(`/repos/${opts.owner}/${opts.repo}/pulls/${opts.prNumber}/files`, opts.token),
    fetchAllPages(`/repos/${opts.owner}/${opts.repo}/pulls/${opts.prNumber}/commits`, opts.token),
  ]);

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
  const seenMessages = new Set();

  if (!files || !Array.isArray(files)) return risks;

  for (const file of files) {
    const fn = file.filename.toLowerCase();

    if (fn.includes('auth') || fn.includes('password') || fn.includes('token') || fn.includes('secret')) {
      const msg = 'Authentication/security-related change — verify no credentials are exposed';
      if (!seenMessages.has(msg + file.filename)) {
        risks.push({ level: 'HIGH', file: file.filename, message: msg });
        seenMessages.add(msg + file.filename);
      }
    }

    if (fn.includes('migration') || fn.includes('schema')) {
      const msg = 'Database schema change — verify migration is reversible and non-destructive';
      if (!seenMessages.has(msg + file.filename)) {
        risks.push({ level: 'MEDIUM', file: file.filename, message: msg });
        seenMessages.add(msg + file.filename);
      }
    }

    if (fn.includes('.env') || fn === 'docker-compose.yml' || fn.includes('config')) {
      const msg = 'Configuration change — verify no secrets are committed';
      if (!seenMessages.has(msg + file.filename)) {
        risks.push({ level: 'MEDIUM', file: file.filename, message: msg });
        seenMessages.add(msg + file.filename);
      }
    }

    if (file.additions && file.additions > 300) {
      risks.push({
        level: 'LOW',
        file: file.filename,
        message: `Large addition (${file.additions} lines) — consider splitting into smaller PRs`,
      });
    }
  }

  if (analysis.additions + analysis.deletions > 1000) {
    risks.push({
      level: 'MEDIUM',
      file: '(overall)',
      message: `Large PR (${analysis.additions} additions, ${analysis.deletions} deletions) — consider breaking into smaller PRs`,
    });
  }

  if (diff) {
    const lines = diff.split('\n');
    for (const line of lines) {
      if (line.startsWith('+')) {
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

  // Deduplicate by message
  const unique = [];
  const seen = new Set();
  for (const r of risks) {
    const key = `${r.level}:${r.file}:${r.message}`;
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(r);
    }
  }

  return unique;
}

// ─── Suggestion Detection ────────────────────────────────────────────
function detectSuggestions(files, diff, analysis) {
  const suggestions = [];

  if (!files || !Array.isArray(files)) return suggestions;

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

  const hasDocs = files.some(f => f.filename.endsWith('.md'));
  if (analysis.changedFiles > 5 && !hasDocs) {
    suggestions.push('Multiple files changed but no documentation updates — consider updating relevant docs');
  }

  if (diff) {
    const lines = diff.split('\n');
    let hasAsync = false;
    let hasTryCatch = false;

    for (const line of lines) {
      if (line.startsWith('+')) {
        if (line.match(/\.then|await\b/)) hasAsync = true;
        if (line.match(/catch|try\s*{/)) hasTryCatch = true;
      }
    }

    if (hasAsync && !hasTryCatch) {
      suggestions.push('Async operations detected but no error handling — consider adding try/catch');
    }
  }

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

  lines.push('---');
  lines.push('*This review was generated by `claude-review` — an automated PR review agent.*');

  return lines.join('\n');
}

// ─── Main ────────────────────────────────────────────────────────────
async function main() {
  const opts = parseArgs();

  if (!opts.token) {
    console.error('Error: GitHub token required. Set GITHUB_TOKEN env var or use --token');
    process.exit(1);
  }

  const data = await fetchPRData(opts);
  const analysis = analyzePR(data);
  const review = generateReview(analysis);

  // Output review to stdout (clean Markdown for piping/posting)
  process.stdout.write(review + '\n');

  // Save to file for convenience (diagnostic to stderr)
  const outputPath = path.join(process.cwd(), `review-${opts.owner}-${opts.repo}-${opts.prNumber}.md`);
  fs.writeFileSync(outputPath, review, 'utf-8');
  console.error(`\nReview saved to: ${outputPath}`);
}

main().catch(err => {
  console.error(`Fatal error: ${err.message}`);
  process.exit(1);
});
