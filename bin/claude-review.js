#!/usr/bin/env node

/**
 * claude-review — a Claude Code sub-agent that reviews PR diffs
 * 
 * Usage: claude-review --pr <pr-url>
 *   claude-review --pr https://github.com/owner/repo/pull/123
 *
 * Works both as a standalone CLI (basic analysis)
 * and as a Claude Code sub-agent (pipeline to Claude for deep review).
 */

import { execSync } from 'child_process';
import { readFileSync, existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PKG = existsSync(resolve(__dirname, '..', 'package.json'))
  ? JSON.parse(readFileSync(resolve(__dirname, '..', 'package.json'), 'utf-8'))
  : { version: '1.0.0' };

// ── Helpers ──────────────────────────────────────────────

function parsePrUrl(url) {
  const match = url.match(/github\.com\/([^\/]+)\/([^\/]+)\/(?:pull|pulls)\/(\d+)/);
  if (!match) throw new Error("Can't parse PR URL: " + url);
  return { owner: match[1], repo: match[2], pr: match[3] };
}

function run(cmd, silent = true) {
  try {
    const out = execSync(cmd, { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 });
    return out.trim();
  } catch (e) {
    if (!silent) throw e;
    return '';
  }
}

function extractAuthor(authorField) {
  if (!authorField) return 'unknown';
  if (typeof authorField === 'string') return authorField;
  if (typeof authorField === 'object') {
    return authorField.login || authorField.name || JSON.stringify(authorField);
  }
  return String(authorField);
}

// ── GitHub data fetching ─────────────────────────────────

function fetchPrDiff(owner, repo, pr) {
  // Try gh CLI first (most reliable, includes richer data)
  const diff = run(
    'gh pr view ' + pr + ' --repo ' + owner + '/' + repo +
    ' --json body,title,headRefName,baseRefName,additions,deletions,files,' +
    'changedFiles,state,author,createdAt,mergedAt,isDraft,labels,reviews,comments'
  );
  if (diff) {
    const data = JSON.parse(diff);
    // gh returns files as array, ensure we process patches
    if (data.files && Array.isArray(data.files)) {
      // files from gh have path, additions, deletions but not patch by default
      // Let's get the diff separately
      data.files = data.files.map(f => ({
        path: f.path,
        status: f.status || 'modified',
        additions: f.additions || 0,
        deletions: f.deletions || 0,
        patch: f.patch || ''
      }));
    }
    return data;
  }

  // Fallback: fetch via HTTP
  const url = 'https://api.github.com/repos/' + owner + '/' + repo + '/pulls/' + pr;
  const result = run('curl -sL -H "Accept: application/vnd.github.v3+json" "' + url + '"');
  if (!result) throw new Error("Failed to fetch PR #" + pr + " from " + owner + "/" + repo);

  const data = JSON.parse(result);
  const filesRaw = run('curl -sL -H "Accept: application/vnd.github.v3+json" "' + url + '/files"');
  const filesData = filesRaw ? JSON.parse(filesRaw) : [];

  return {
    title: data.title || '',
    body: data.body || '',
    headRefName: data.head?.ref,
    baseRefName: data.base?.ref,
    additions: data.additions || 0,
    deletions: data.deletions || 0,
    changedFiles: data.changed_files || 0,
    state: data.state || 'open',
    author: data.user?.login || 'unknown',
    files: (filesData || []).map(f => ({
      path: f.filename,
      status: f.status,
      additions: f.additions || 0,
      deletions: f.deletions || 0,
      patch: f.patch || ''
    }))
  };
}

// ── Analysis engine ──────────────────────────────────────

function analyzeDiff(data) {
  const files = data.files || [];
  const warnings = [];
  const suggestions = [];
  const positives = [];

  // Author 
  const author = extractAuthor(data.author);

  // Size analysis
  const totalChanged = files.length;
  const bigFiles = files.filter(f => f.additions + f.deletions > 200);
  const isLargePr = data.additions > 1000 || data.deletions > 500;

  if (isLargePr) {
    warnings.push(
      "Large PR: " + data.additions + "+ / " + data.deletions + "- lines across " +
      totalChanged + " files. Consider splitting into smaller, focused PRs."
    );
  }

  if (bigFiles.length > 0) {
    warnings.push(
      "Large files that could benefit from splitting: " +
      bigFiles.map(f => f.path).join(', ')
    );
  }

  // File type analysis
  const jsFiles = files.filter(f => {
    const ext = f.path.split('.').pop();
    return ['js', 'jsx', 'ts', 'tsx'].includes(ext);
  });

  if (jsFiles.length > 0) {
    const hasTests = jsFiles.some(f =>
      f.path.includes('test') || f.path.includes('spec') || f.path.includes('__tests__')
    );
    if (!hasTests && jsFiles.some(f => f.path.match(/^src\//))) {
      suggestions.push(
        'No test files detected in this PR. Consider adding tests for the changed logic.'
      );
    }
  }

  // Pattern checks in diff patches
  for (const file of files) {
    const patch = file.patch || '';
    if (!patch) continue;

    // console.log detection
    const consoleLogs = (patch.match(/console\.(log|warn|error)\(/g) || []).length;
    if (consoleLogs > 2) {
      suggestions.push(
        "Found " + consoleLogs + " console statements in " + file.path +
        ". Consider removing debug logging before merging."
      );
    }

    // TODO/FIXME detection
    const todos = (patch.match(/\b(TODO|FIXME|HACK|XXX)\b/g) || []).length;
    if (todos > 0) {
      warnings.push(
        "Found " + todos + " TODO/FIXME marker(s) in " + file.path +
        ". These should be addressed before merge."
      );
    }

    // Hardcoded secrets detection
    const secrets = patch.match(
      /(?:api[_-]?key|secret|password|token)\s*[:=]\s*['"][^'"]+['"]/gi
    );
    if (secrets) {
      warnings.push(
        "⚠️ POTENTIAL SECRET LEAK in " + file.path +
        ": hardcoded credentials detected. Use env vars or a secrets manager."
      );
    }

    // Positive: small, focused change
    if (file.additions + file.deletions < 30 && file.additions > 0) {
      positives.push(
        "👍 " + file.path + ": clean, focused change (" +
        file.additions + "+ / " + file.deletions + "-)"
      );
    }
  }

  // Branch name convention
  const branchName = data.headRefName || '';
  if (branchName && !branchName.match(/^(feature|fix|chore|refactor|docs|test|hotfix)\//)) {
    suggestions.push(
      'Branch name "' + branchName + '" doesn\'t follow convention. ' +
      'Consider: feature/xxx, fix/xxx, chore/xxx, refactor/xxx'
    );
  }

  return {
    summary: "This PR (" + data.baseRefName + " ← " + data.headRefName +
      ") changes " + totalChanged + " file(s) with " + data.additions +
      " additions and " + data.deletions + " deletions.",
    risks: warnings.length > 0 ? warnings : ['No significant risks identified.'],
    suggestions: suggestions.length > 0
      ? suggestions
      : ['No improvement suggestions for this diff.'],
    positives: positives.length > 0
      ? positives
      : ['Change scope is reasonable.'],
    stats: {
      filesChanged: totalChanged,
      additions: data.additions,
      deletions: data.deletions,
      author: author
    }
  };
}

function determineConfidence(analysis) {
  const isLowRisk = analysis.risks.length <= 1 &&
    analysis.risks[0] === 'No significant risks identified.';
  const hasSuggestions = analysis.suggestions.length > 1 ||
    (analysis.suggestions.length === 1 &&
     analysis.suggestions[0] !== 'No improvement suggestions for this diff.');

  if (isLowRisk && !hasSuggestions) return 'High';
  if (isLowRisk && hasSuggestions) return 'Medium';
  return 'Low';
}

function renderMarkdown(data, analysis, confidence) {
  const author = analysis.stats.author;
  return [
    '## 🔍 PR Review',
    '',
    '**PR**: [' + data.title + '](' + (data.url || '') + ')',
    '**Author**: ' + author,
    '**Branch**: ' + data.baseRefName + ' ← ' + data.headRefName,
    '**Status**: ' + analysis.stats.filesChanged + ' files | ' +
      analysis.stats.additions + ' ✚ | ' + analysis.stats.deletions + ' ✖',
    '',
    '---',
    '',
    '### 📋 Summary',
    '',
    analysis.summary,
    '',
    '---',
    '',
    '### ⚠️ Identified Risks',
    '',
    analysis.risks.map(r => '- ' + r).join('\n'),
    '',
    '---',
    '',
    '### 💡 Improvement Suggestions',
    '',
    analysis.suggestions.map(s => '- ' + s).join('\n'),
    '',
    '---',
    '',
    '### ✅ What Looks Good',
    '',
    analysis.positives.map(p => '- ' + p).join('\n'),
    '',
    '---',
    '',
    '### 📊 Confidence Score: **' + confidence + '**',
    '',
    '_Generated by claude-review v' + PKG.version + '_'
  ].join('\n');
}

// ── Claude Code agent output (machine-readable) ──────────

function renderAgentOutput(data, analysis, confidence, prUrl) {
  return JSON.stringify({
    tool: 'claude-review',
    version: PKG.version,
    prUrl: prUrl,
    title: data.title,
    baseRef: data.baseRefName,
    headRef: data.headRefName,
    stats: analysis.stats,
    analysis: {
      summary: analysis.summary,
      risks: analysis.risks,
      suggestions: analysis.suggestions,
      positives: analysis.positives,
      confidence: confidence
    },
    timestamp: new Date().toISOString()
  }, null, 2);
}

// ── CLI ──────────────────────────────────────────────────

function printHelp() {
  console.log([
    '',
    'claude-review v' + PKG.version,
    '',
    'A Claude Code sub-agent that reviews pull request diffs.',
    '',
    'USAGE:',
    '  claude-review --pr <pr-url>           Review a PR',
    '  claude-review --pr <pr-url> --json    Output as JSON (agent pipeline)',
    '  claude-review --version               Show version',
    '  claude-review --help                  Show this help',
    '',
    'EXAMPLES:',
    '  claude-review --pr https://github.com/owner/repo/pull/123',
    '  claude-review --pr https://github.com/owner/repo/pull/123 --json',
    ''
  ].join('\n'));
}

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h') || args.length === 0) {
    printHelp();
    process.exit(0);
  }

  if (args.includes('--version') || args.includes('-v')) {
    console.log(PKG.version);
    process.exit(0);
  }

  const prIndex = args.findIndex(a => a === '--pr');
  if (prIndex === -1) {
    console.error('❌ Missing --pr flag. Use --help for usage.');
    process.exit(1);
  }

  const prUrl = args[prIndex + 1];
  if (!prUrl) {
    console.error('❌ Missing PR URL after --pr');
    process.exit(1);
  }

  const outputJson = args.includes('--json');

  try {
    const { owner, repo, pr } = parsePrUrl(prUrl);

    // Fetch PR data
    const data = fetchPrDiff(owner, repo, pr);
    data.url = prUrl;

    // Analyze
    const analysis = analyzeDiff(data);
    const confidence = determineConfidence(analysis);

    // Output
    if (outputJson) {
      console.log(renderAgentOutput(data, analysis, confidence, prUrl));
    } else {
      console.log(renderMarkdown(data, analysis, confidence));
    }
  } catch (err) {
    console.error('❌ Error: ' + err.message);
    process.exit(1);
  }
}

main();