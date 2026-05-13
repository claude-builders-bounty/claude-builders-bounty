#!/usr/bin/env node

import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

const TEST_FILE_PATTERN =
  /(^|\/)(__tests__|test|tests|spec|specs)\/|(\.|-)(test|spec)\.[cm]?[jt]sx?$|\.snap$/i;
const DOC_FILE_PATTERN = /(^|\/)(README|CHANGELOG|docs\/)|\.(md|mdx|rst)$/i;
const CONFIG_FILE_PATTERN =
  /(^|\/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|requirements\.txt|Cargo\.toml|Cargo\.lock|go\.mod|go\.sum|Dockerfile|docker-compose\.ya?ml|\.github\/workflows\/)/i;
const SECURITY_PATTERN =
  /(auth|token|secret|password|credential|permission|role|jwt|oauth|cors|csrf|xss|sql|encrypt|signature|private[-_]?key)/i;

function usage() {
  return `Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --diff-file ./change.diff

Options:
  --pr <url>          GitHub pull request URL
  --diff-file <path>  Local diff file to review
  --output <path>     Write Markdown review to a file
  --help             Show this help
`;
}

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--help' || arg === '-h') {
      args.help = true;
    } else if (arg === '--pr') {
      args.pr = argv[++i];
    } else if (arg === '--diff-file') {
      args.diffFile = argv[++i];
    } else if (arg === '--output') {
      args.output = argv[++i];
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }
  return args;
}

function parsePullRequestUrl(value) {
  const match = value.match(/^https:\/\/github\.com\/([^/\s]+)\/([^/\s]+)\/pull\/(\d+)\/?$/);
  if (!match) {
    throw new Error(`Invalid GitHub PR URL: ${value}`);
  }
  return {
    owner: match[1],
    repo: match[2],
    number: match[3],
    diffUrl: `${value.replace(/\/$/, '')}.diff`,
  };
}

async function fetchDiff(url) {
  let lastError;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const response = await fetch(url, {
        headers: {
          Accept: 'application/vnd.github.v3.diff',
          'User-Agent': 'claude-pr-reviewer/0.1.0',
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.text();
    } catch (error) {
      lastError = error;
      if (attempt < 3) {
        await new Promise((resolve) => setTimeout(resolve, attempt * 500));
      }
    }
  }
  const message = lastError instanceof Error ? lastError.message : String(lastError);
  throw new Error(`Failed to fetch PR diff from ${url}: ${message}`);
}

function parseDiff(diff) {
  const files = [];
  let current = null;

  for (const line of diff.split('\n')) {
    const fileMatch = line.match(/^diff --git a\/(.+?) b\/(.+)$/);
    if (fileMatch) {
      current = {
        oldPath: fileMatch[1],
        path: fileMatch[2],
        additions: 0,
        deletions: 0,
        hunks: 0,
      };
      files.push(current);
      continue;
    }

    if (!current) continue;
    if (line.startsWith('@@')) {
      current.hunks += 1;
    } else if (line.startsWith('+') && !line.startsWith('+++')) {
      current.additions += 1;
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      current.deletions += 1;
    }
  }

  const additions = files.reduce((sum, file) => sum + file.additions, 0);
  const deletions = files.reduce((sum, file) => sum + file.deletions, 0);
  const hunks = files.reduce((sum, file) => sum + file.hunks, 0);

  return { files, additions, deletions, hunks };
}

function fileGroups(files) {
  return {
    tests: files.filter((file) => TEST_FILE_PATTERN.test(file.path)),
    docs: files.filter((file) => DOC_FILE_PATTERN.test(file.path)),
    config: files.filter((file) => CONFIG_FILE_PATTERN.test(file.path)),
    security: files.filter((file) => SECURITY_PATTERN.test(file.path)),
  };
}

function summarizeChanges(stats, groups) {
  const fileCount = stats.files.length;
  const touched = stats.files.slice(0, 5).map((file) => `\`${file.path}\``).join(', ');
  const scope =
    fileCount === 1
      ? `This PR changes one file: ${touched}.`
      : `This PR changes ${fileCount} files, including ${touched}${fileCount > 5 ? ', ...' : ''}.`;
  const size = `The diff contains ${stats.additions} additions and ${stats.deletions} deletions across ${stats.hunks} hunks.`;
  const coverage =
    groups.tests.length > 0
      ? `It includes test-related changes in ${groups.tests.length} file(s), which improves review confidence.`
      : 'No test file changes were detected in the diff, so behavior coverage should be checked manually.';
  return [scope, size, coverage];
}

function identifyRisks(stats, groups) {
  const risks = [];
  const totalChanges = stats.additions + stats.deletions;

  if (stats.files.length === 0) {
    risks.push('No file-level diff was detected; verify the PR URL or diff input.');
  }
  if (totalChanges > 600 || stats.files.length > 20) {
    risks.push('Large diff size increases the chance that behavioral changes are missed in review.');
  }
  if (groups.tests.length === 0) {
    risks.push('No tests changed, so regressions may slip through unless existing tests cover the path.');
  }
  if (groups.config.length > 0) {
    risks.push('Configuration or dependency files changed; check installation, CI, and lockfile consistency.');
  }
  if (groups.security.length > 0 || stats.files.some((file) => SECURITY_PATTERN.test(file.path))) {
    risks.push('Security-sensitive paths or names appear in the diff; review auth, token, and permission behavior closely.');
  }
  if (stats.files.some((file) => file.deletions > file.additions * 3 && file.deletions > 20)) {
    risks.push('One or more files remove substantially more code than they add; verify that behavior was not dropped unintentionally.');
  }

  return risks.length ? risks : ['No obvious structural risks were detected from the diff metadata.'];
}

function improvementSuggestions(stats, groups) {
  const suggestions = [];

  if (groups.tests.length === 0) {
    suggestions.push('Add or reference targeted tests that exercise the changed behavior.');
  } else {
    suggestions.push('Run the targeted test files touched by this PR and include the command output in the PR description.');
  }
  if (groups.docs.length === 0 && stats.files.length > 1) {
    suggestions.push('Consider whether README or usage docs need a short update for the changed behavior.');
  }
  if (groups.config.length > 0) {
    suggestions.push('Confirm generated lockfiles and CI workflow changes are intentional and minimal.');
  }
  suggestions.push('Ask the author to document any edge cases that are not covered by automated tests.');

  return suggestions;
}

function confidenceScore(stats, groups, risks) {
  const totalChanges = stats.additions + stats.deletions;
  let score = 2;
  if (groups.tests.length > 0) score += 1;
  if (totalChanges > 600 || stats.files.length > 20) score -= 1;
  if (groups.security.length > 0) score -= 1;
  if (risks.length > 2) score -= 1;

  if (score >= 3) return 'High';
  if (score <= 0) return 'Low';
  return 'Medium';
}

export function createReview(diff, source = 'local diff') {
  const stats = parseDiff(diff);
  const groups = fileGroups(stats.files);
  const summary = summarizeChanges(stats, groups);
  const risks = identifyRisks(stats, groups);
  const suggestions = improvementSuggestions(stats, groups);
  const confidence = confidenceScore(stats, groups, risks);

  return `## PR Review

Source: ${source}

### Summary of Changes
${summary.map((item) => `- ${item}`).join('\n')}

### Identified Risks
${risks.map((item) => `- ${item}`).join('\n')}

### Improvement Suggestions
${suggestions.map((item) => `- ${item}`).join('\n')}

### Confidence Score
${confidence}
`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    process.stdout.write(usage());
    return;
  }
  if (!args.pr && !args.diffFile) {
    throw new Error('Provide either --pr or --diff-file.\n\n' + usage());
  }
  if (args.pr && args.diffFile) {
    throw new Error('Use only one input: --pr or --diff-file.');
  }

  let diff;
  let source;
  if (args.pr) {
    const pr = parsePullRequestUrl(args.pr);
    diff = await fetchDiff(pr.diffUrl);
    source = `${pr.owner}/${pr.repo}#${pr.number}`;
  } else {
    const diffPath = path.resolve(args.diffFile);
    diff = await fs.readFile(diffPath, 'utf8');
    source = diffPath;
  }

  const review = createReview(diff, source);
  if (args.output) {
    await fs.writeFile(args.output, review, 'utf8');
  } else {
    process.stdout.write(review);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
