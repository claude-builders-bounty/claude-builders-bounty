'use strict';

const fs = require('node:fs');
const { spawnSync } = require('node:child_process');

const REVIEW_MARKER = '<!-- claude-review-agent -->';

function usage() {
  return `claude-review

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
  claude-review --fixture ./fixtures/example.diff --pr https://github.com/owner/repo/pull/123

Options:
  --pr <url>              GitHub pull request URL to review.
  --output <file>         Write the Markdown review to a file instead of stdout.
  --fixture <file>        Use a local .diff fixture instead of fetching from GitHub.
  --max-diff-chars <n>    Maximum diff characters to analyze. Default: 120000.
  --provider <name>       static or claude-cli. Default: static.
  --token <token>         GitHub token. Defaults to GITHUB_TOKEN or GH_TOKEN.
  --help                  Show this help.

Environment:
  GITHUB_TOKEN            Raises GitHub API limits for public/private PRs.
  CLAUDE_REVIEW_PROVIDER  static or claude-cli.
`;
}

function parseArgs(argv) {
  const args = {
    maxDiffChars: 120000,
    provider: process.env.CLAUDE_REVIEW_PROVIDER || 'static'
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--help' || arg === '-h') {
      args.help = true;
      continue;
    }
    if (arg === '--pr') {
      args.pr = nextValue(argv, ++index, arg);
      continue;
    }
    if (arg === '--output' || arg === '-o') {
      args.output = nextValue(argv, ++index, arg);
      continue;
    }
    if (arg === '--fixture') {
      args.fixture = nextValue(argv, ++index, arg);
      continue;
    }
    if (arg === '--max-diff-chars') {
      args.maxDiffChars = Number.parseInt(nextValue(argv, ++index, arg), 10);
      if (!Number.isFinite(args.maxDiffChars) || args.maxDiffChars < 1000) {
        throw new Error('--max-diff-chars must be an integer >= 1000');
      }
      continue;
    }
    if (arg === '--provider') {
      args.provider = nextValue(argv, ++index, arg);
      continue;
    }
    if (arg === '--token') {
      args.token = nextValue(argv, ++index, arg);
      continue;
    }
    throw new Error(`unknown argument: ${arg}`);
  }

  if (!args.help && !args.pr) {
    throw new Error('missing required --pr <github pull request url>');
  }
  return args;
}

function nextValue(argv, index, flag) {
  const value = argv[index];
  if (!value || value.startsWith('--')) {
    throw new Error(`${flag} requires a value`);
  }
  return value;
}

function parsePullRequestUrl(prUrl) {
  let url;
  try {
    url = new URL(prUrl);
  } catch {
    throw new Error(`invalid PR URL: ${prUrl}`);
  }

  if (url.hostname !== 'github.com') {
    throw new Error('only github.com pull request URLs are supported');
  }

  const parts = url.pathname.split('/').filter(Boolean);
  if (parts.length < 4 || parts[2] !== 'pull' || !/^\d+$/.test(parts[3])) {
    throw new Error('expected PR URL format: https://github.com/owner/repo/pull/123');
  }

  return {
    owner: parts[0],
    repo: parts[1],
    number: Number.parseInt(parts[3], 10),
    url: `https://github.com/${parts[0]}/${parts[1]}/pull/${parts[3]}`
  };
}

async function buildReviewFromPullRequest(args) {
  const pr = parsePullRequestUrl(args.pr);
  const maxDiffChars = args.maxDiffChars || 120000;
  const provider = args.provider || 'static';

  const [metadata, diffSource] = await Promise.all([
    args.fixture ? fallbackMetadata(pr) : fetchPullRequestMetadata(pr, args.token),
    args.fixture ? readFixture(args.fixture) : fetchPullRequestDiff(pr, args.token)
  ]);

  const truncated = diffSource.length > maxDiffChars;
  const diff = truncated ? diffSource.slice(0, maxDiffChars) : diffSource;
  const parsedDiff = parseUnifiedDiff(diff);
  const staticReview = analyzeDiff({ pr, metadata, parsedDiff, diff, truncated });

  if (provider === 'claude-cli') {
    const claudeReview = tryClaudeCliReview({ pr, metadata, parsedDiff, diff, staticReview });
    if (claudeReview) {
      return claudeReview;
    }
  } else if (provider !== 'static') {
    throw new Error(`unsupported provider: ${provider}`);
  }

  return staticReview;
}

function readFixture(filePath) {
  return fs.readFileSync(filePath, 'utf8');
}

async function fetchPullRequestMetadata(pr, token) {
  const endpoint = `https://api.github.com/repos/${pr.owner}/${pr.repo}/pulls/${pr.number}`;
  const response = await fetch(endpoint, {
    headers: githubHeaders(token, 'application/vnd.github+json')
  });

  if (!response.ok) {
    throw new Error(`failed to fetch PR metadata: ${response.status} ${response.statusText}`);
  }

  const json = await response.json();
  return {
    title: json.title || `Pull request #${pr.number}`,
    author: json.user && json.user.login ? json.user.login : 'unknown',
    base: json.base && json.base.ref ? json.base.ref : 'unknown',
    head: json.head && json.head.ref ? json.head.ref : 'unknown',
    additions: Number.isFinite(json.additions) ? json.additions : 0,
    deletions: Number.isFinite(json.deletions) ? json.deletions : 0,
    changedFiles: Number.isFinite(json.changed_files) ? json.changed_files : 0
  };
}

async function fetchPullRequestDiff(pr, token) {
  const endpoint = `https://api.github.com/repos/${pr.owner}/${pr.repo}/pulls/${pr.number}`;
  const response = await fetch(endpoint, {
    headers: githubHeaders(token, 'application/vnd.github.v3.diff')
  });

  if (!response.ok) {
    throw new Error(`failed to fetch PR diff: ${response.status} ${response.statusText}`);
  }

  return response.text();
}

function githubHeaders(token, accept) {
  const headers = {
    Accept: accept,
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': 'claude-review-agent'
  };
  const githubToken = token || process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  if (githubToken) {
    headers.Authorization = `Bearer ${githubToken}`;
  }
  return headers;
}

function fallbackMetadata(pr) {
  return {
    title: `Pull request #${pr.number}`,
    author: 'unknown',
    base: 'unknown',
    head: 'unknown',
    additions: 0,
    deletions: 0,
    changedFiles: 0
  };
}

function parseUnifiedDiff(diff) {
  const files = [];
  let current = null;
  let currentHunk = null;

  for (const line of diff.split(/\r?\n/)) {
    if (line.startsWith('diff --git ')) {
      current = {
        oldPath: '',
        newPath: '',
        additions: 0,
        deletions: 0,
        hunks: [],
        addedLines: [],
        removedLines: [],
        header: line
      };
      files.push(current);
      currentHunk = null;
      continue;
    }

    if (!current) {
      continue;
    }

    if (line.startsWith('--- ')) {
      current.oldPath = cleanDiffPath(line.slice(4));
      continue;
    }

    if (line.startsWith('+++ ')) {
      current.newPath = cleanDiffPath(line.slice(4));
      continue;
    }

    if (line.startsWith('@@')) {
      currentHunk = { header: line, additions: 0, deletions: 0 };
      current.hunks.push(currentHunk);
      continue;
    }

    if (line.startsWith('+') && !line.startsWith('+++')) {
      current.additions += 1;
      current.addedLines.push(line.slice(1));
      if (currentHunk) {
        currentHunk.additions += 1;
      }
      continue;
    }

    if (line.startsWith('-') && !line.startsWith('---')) {
      current.deletions += 1;
      current.removedLines.push(line.slice(1));
      if (currentHunk) {
        currentHunk.deletions += 1;
      }
    }
  }

  return files.map((file) => ({
    ...file,
    path: file.newPath && file.newPath !== '/dev/null' ? file.newPath : file.oldPath
  })).filter((file) => file.path);
}

function cleanDiffPath(pathValue) {
  if (pathValue === '/dev/null') {
    return pathValue;
  }
  return pathValue.replace(/^[ab]\//, '');
}

function analyzeDiff({ pr, metadata, parsedDiff, diff, truncated }) {
  const stats = buildStats(metadata, parsedDiff, diff, truncated);
  const risks = identifyRisks(stats, parsedDiff, diff);
  const suggestions = identifySuggestions(stats, parsedDiff, risks);
  const confidence = scoreConfidence(stats, risks);

  return {
    marker: REVIEW_MARKER,
    pr,
    metadata,
    stats,
    summary: buildSummary(metadata, stats),
    risks,
    suggestions,
    confidence
  };
}

function buildStats(metadata, files, diff, truncated) {
  const changedFiles = metadata.changedFiles || files.length;
  const additions = metadata.additions || sum(files, 'additions');
  const deletions = metadata.deletions || sum(files, 'deletions');
  const filePaths = files.map((file) => file.path);
  const dependencyFiles = files.filter(isDependencyChange);
  const extensionCounts = countBy(filePaths.map(extensionForPath));
  const topDirectories = topEntries(countBy(filePaths.map(topDirectoryForPath)), 3);

  return {
    changedFiles,
    additions,
    deletions,
    parsedFiles: files.length,
    totalChangedLines: additions + deletions,
    diffCharacters: diff.length,
    truncated,
    filePaths,
    extensionCounts,
    topDirectories,
    hasTests: filePaths.some(isTestPath),
    touchesCi: filePaths.some(isCiPath),
    touchesDependencies: dependencyFiles.length > 0,
    touchesDatabase: filePaths.some(isDatabasePath),
    touchesSecurity: filePaths.some(isSecurityPath),
    touchesDocs: filePaths.some(isDocsPath),
    touchesApi: filePaths.some(isApiPath)
  };
}

function identifyRisks(stats, files, diff) {
  const risks = [];
  const addedText = files.flatMap((file) => file.addedLines).join('\n');

  if (stats.truncated) {
    risks.push('The diff was truncated before analysis, so later files may contain unreviewed behavior changes.');
  }

  if (stats.changedFiles >= 12 || stats.totalChangedLines >= 900) {
    risks.push(`Large change surface (${stats.changedFiles} files, +${stats.additions}/-${stats.deletions}) increases the chance of hidden regressions and makes reviewer coverage harder.`);
  }

  if (!stats.hasTests && stats.totalChangedLines > 20) {
    risks.push('No test files were detected in the diff, so behavior changes may not be protected by automated regression coverage.');
  }

  if (stats.touchesDependencies) {
    risks.push('Dependency or lockfile changes can introduce supply-chain, licensing, or runtime-version drift if not pinned and audited.');
  }

  if (stats.touchesCi) {
    risks.push('CI or GitHub Actions changes can affect secrets exposure, permissions, and release automation beyond the application code.');
  }

  if (stats.touchesDatabase) {
    risks.push('Database or migration changes may need rollback planning and compatibility checks for already-deployed data.');
  }

  if (stats.touchesSecurity || containsSecuritySensitiveCode(addedText)) {
    risks.push('Security-sensitive code paths are touched, so authorization, input validation, and secret-handling assumptions need focused review.');
  }

  if (stats.touchesApi) {
    risks.push('API-facing files changed, which can break callers if request/response contracts or error semantics shifted.');
  }

  if (containsNetworkWithoutErrorHandling(addedText)) {
    risks.push('New network or async calls were added; failures, timeouts, and partial responses may not be handled consistently.');
  }

  if (containsSecretLikeValue(addedText)) {
    risks.push('The added lines include strings that look like tokens, credentials, or private keys and should be checked before merge.');
  }

  if (risks.length === 0) {
    risks.push('No high-risk patterns were obvious from the diff, but the review is limited to static patch analysis.');
  }

  return unique(risks).slice(0, 7);
}

function identifySuggestions(stats, files, risks) {
  const suggestions = [];
  const addedText = files.flatMap((file) => file.addedLines).join('\n');

  if (!stats.hasTests && stats.totalChangedLines > 20) {
    suggestions.push('Add or update focused tests around the changed behavior, especially for edge cases and failure paths.');
  }

  if (stats.touchesDependencies) {
    suggestions.push('Document why dependency changes are needed and confirm the lockfile was regenerated with the intended package manager.');
  }

  if (stats.touchesCi) {
    suggestions.push('Keep workflow permissions minimal and verify the action works for forked PRs without exposing privileged secrets.');
  }

  if (stats.touchesDatabase) {
    suggestions.push('Include migration rollback notes plus a compatibility check for old application versions reading new data.');
  }

  if (stats.touchesApi) {
    suggestions.push('Call out any API contract changes in the PR description and add compatibility tests for existing callers.');
  }

  if (stats.totalChangedLines >= 900) {
    suggestions.push('Consider splitting mechanical, generated, or formatting-only changes from functional changes to simplify review.');
  }

  if (containsUserInputHandling(addedText)) {
    suggestions.push('Validate and normalize user-controlled input at the boundary before it reaches business logic or persistence.');
  }

  if (risks.some((risk) => risk.includes('static patch analysis'))) {
    suggestions.push('Run the project test suite and include the command output in the PR before requesting final review.');
  }

  if (suggestions.length === 0) {
    suggestions.push('Keep the PR description aligned with the changed files and include the test command used to validate the patch.');
  }

  return unique(suggestions).slice(0, 7);
}

function buildSummary(metadata, stats) {
  const title = metadata.title || 'this pull request';
  const dirs = stats.topDirectories.length > 0
    ? stats.topDirectories.map(([name]) => name).join(', ')
    : 'the repository root';
  const testPhrase = stats.hasTests ? 'The diff includes test changes' : 'No test files were detected';
  const focus = [
    stats.touchesApi ? 'API-facing code' : null,
    stats.touchesDatabase ? 'database/migration code' : null,
    stats.touchesCi ? 'CI configuration' : null,
    stats.touchesDependencies ? 'dependency metadata' : null,
    stats.touchesDocs ? 'documentation' : null
  ].filter(Boolean);
  const focusText = focus.length > 0 ? ` Notable areas include ${joinHuman(focus)}.` : '';

  return [
    `This review covers "${title}", which changes ${stats.changedFiles} file${plural(stats.changedFiles)} with +${stats.additions}/-${stats.deletions} lines across ${dirs}.`,
    `${testPhrase}, and the static diff scan parsed ${stats.parsedFiles} file${plural(stats.parsedFiles)}.${focusText}`
  ];
}

function scoreConfidence(stats, risks) {
  if (stats.truncated || stats.parsedFiles === 0 || stats.diffCharacters > 100000) {
    return 'Low';
  }
  if (stats.totalChangedLines > 900 || stats.changedFiles > 15 || risks.length >= 5) {
    return 'Medium';
  }
  return 'High';
}

function tryClaudeCliReview({ pr, metadata, diff, staticReview }) {
  const prompt = [
    'You are a Claude Code PR review sub-agent.',
    'Review the following GitHub PR diff and return only structured Markdown with these sections:',
    '## Summary, ## Identified Risks, ## Improvement Suggestions, ## Confidence Score.',
    'The summary must be 2-3 sentences and confidence must be Low, Medium, or High.',
    '',
    `PR: ${pr.url}`,
    `Title: ${metadata.title}`,
    '',
    'Diff:',
    '```diff',
    diff.slice(0, 50000),
    '```'
  ].join('\n');

  const result = spawnSync('claude', ['-p', prompt], {
    encoding: 'utf8',
    maxBuffer: 1024 * 1024 * 4,
    timeout: 120000
  });

  if (result.error || result.status !== 0 || !result.stdout.trim()) {
    return null;
  }

  return {
    ...staticReview,
    provider: 'claude-cli',
    claudeMarkdown: normalizeClaudeMarkdown(result.stdout.trim())
  };
}

function normalizeClaudeMarkdown(markdown) {
  if (markdown.includes(REVIEW_MARKER)) {
    return markdown;
  }
  return `${REVIEW_MARKER}\n${markdown}\n`;
}

function formatReviewMarkdown(review) {
  if (review.claudeMarkdown) {
    return review.claudeMarkdown;
  }

  const lines = [
    review.marker,
    `# Claude PR Review`,
    '',
    `**PR:** [${review.pr.owner}/${review.pr.repo}#${review.pr.number}](${review.pr.url})`,
    `**Author:** @${review.metadata.author}`,
    `**Base <- Head:** \`${review.metadata.base}\` <- \`${review.metadata.head}\``,
    '',
    '## Summary',
    review.summary.join(' '),
    '',
    '## Identified Risks',
    ...review.risks.map((risk) => `- ${risk}`),
    '',
    '## Improvement Suggestions',
    ...review.suggestions.map((suggestion) => `- ${suggestion}`),
    '',
    '## Confidence Score',
    `**${review.confidence}**`,
    '',
    '<sub>Generated by `claude-review` from the pull request diff.</sub>'
  ];

  return `${lines.join('\n')}\n`;
}

function extensionForPath(filePath) {
  const match = filePath.match(/\.([^.\/]+)$/);
  return match ? `.${match[1].toLowerCase()}` : '[none]';
}

function topDirectoryForPath(filePath) {
  const first = filePath.split('/')[0];
  return first && first !== filePath ? first : '[root]';
}

function isTestPath(filePath) {
  return /(^|\/)(__tests__|tests?|spec|fixtures?|testdata)(\/|$)/i.test(filePath)
    || /\.(test|spec)\.[cm]?[jt]sx?$/i.test(filePath)
    || /(_test\.go|Test\.java|Tests\.cs)$/i.test(filePath);
}

function isCiPath(filePath) {
  return /^\.github\/workflows\//.test(filePath)
    || /(^|\/)(circleci|buildkite|jenkins|gitlab-ci|azure-pipelines)/i.test(filePath)
    || /(Dockerfile|docker-compose\.ya?ml)$/i.test(filePath);
}

function isDependencyPath(filePath) {
  return /(^|\/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb|Cargo\.lock|go\.sum|poetry\.lock|Pipfile\.lock|requirements.*\.txt|Gemfile\.lock|composer\.lock)$/i.test(filePath)
    || /(^|\/)(package\.json|Cargo\.toml|go\.mod|pyproject\.toml|pom\.xml|build\.gradle|composer\.json|Gemfile)$/i.test(filePath);
}

function isDependencyChange(file) {
  if (/lock/i.test(file.path) || /(requirements.*\.txt|go\.sum)$/i.test(file.path)) {
    return isDependencyPath(file.path);
  }

  if (!isDependencyPath(file.path)) {
    return false;
  }

  const changedText = file.addedLines.concat(file.removedLines).join('\n');
  return /"dependencies"|"devDependencies"|\[[^\]]*dependencies\]|^\s*(require|import)\s|^\s*[\w@./-]+[=<>~^]/im.test(changedText);
}

function isDatabasePath(filePath) {
  return /(^|\/)(migrations?|schema|seeds?|db|database)(\/|$)/i.test(filePath)
    || /\.(sql|prisma)$/i.test(filePath);
}

function isSecurityPath(filePath) {
  return /(^|\/)(auth|oauth|session|sessions|security|permissions?|policies|crypto|jwt)(\/|$)/i.test(filePath);
}

function isDocsPath(filePath) {
  return /\.(md|mdx|rst|adoc)$/i.test(filePath) || /(^|\/)docs\//i.test(filePath);
}

function isApiPath(filePath) {
  return /(^|\/)(api|routes?|controllers?|handlers?|graphql|proto|openapi|swagger)(\/|$)/i.test(filePath)
    || /\.(proto|graphql|ya?ml)$/i.test(filePath) && /(openapi|swagger|api)/i.test(filePath);
}

function containsSecuritySensitiveCode(text) {
  return /\b(auth|authorize|permission|role|jwt|token|secret|password|encrypt|decrypt|session|cookie)\b/i.test(text);
}

function containsNetworkWithoutErrorHandling(text) {
  const network = /\b(fetch|axios|http\.|https\.|request\(|urllib|requests\.|URLSession|grpc|WebClient)\b/i.test(text);
  const handling = /\b(catch|try|timeout|retry|AbortController|except|rescue)\b/i.test(text);
  return network && !handling;
}

function containsSecretLikeValue(text) {
  return /(api[_-]?key|secret|private[_-]?key|access[_-]?token)\s*[:=]\s*['"][^'"]{12,}/i.test(text)
    || /-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----/.test(text);
}

function containsUserInputHandling(text) {
  return /\b(req\.body|req\.query|request\.json|request\.args|params|FormData|input|argv|process\.env)\b/i.test(text);
}

function countBy(values) {
  return values.reduce((acc, value) => {
    acc[value] = (acc[value] || 0) + 1;
    return acc;
  }, {});
}

function topEntries(counts, limit) {
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, limit);
}

function sum(items, key) {
  return items.reduce((total, item) => total + (item[key] || 0), 0);
}

function unique(values) {
  return Array.from(new Set(values));
}

function plural(count) {
  return count === 1 ? '' : 's';
}

function joinHuman(items) {
  if (items.length <= 1) {
    return items.join('');
  }
  if (items.length === 2) {
    return `${items[0]} and ${items[1]}`;
  }
  return `${items.slice(0, -1).join(', ')}, and ${items[items.length - 1]}`;
}

module.exports = {
  REVIEW_MARKER,
  analyzeDiff,
  buildReviewFromPullRequest,
  formatReviewMarkdown,
  parseArgs,
  parsePullRequestUrl,
  parseUnifiedDiff,
  usage
};
