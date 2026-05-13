#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { request } from 'node:https';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(__dirname, '..');
const agentPath = resolve(packageRoot, '.claude', 'agents', 'pr-reviewer.md');

const DEFAULT_MAX_DIFF_BYTES = 180_000;
const CLAUDE_BINARY = process.env.CLAUDE_REVIEW_CLAUDE_BIN || defaultClaudeBinary();

function defaultClaudeBinary() {
  if (process.platform !== 'win32') return 'claude';

  const where = spawnSync('where.exe', ['claude'], {
    encoding: 'utf8',
    windowsHide: true,
  });

  if (where.status === 0 && where.stdout) {
    for (const line of where.stdout.split(/\r?\n/).map((entry) => entry.trim()).filter(Boolean)) {
      const npmInstallCandidate = resolve(
        dirname(line),
        'node_modules',
        '@anthropic-ai',
        'claude-code',
        'bin',
        'claude.exe',
      );
      if (existsSync(npmInstallCandidate)) return npmInstallCandidate;
    }
  }

  return 'claude.exe';
}

function usage() {
  return `Usage:
  claude-review --pr https://github.com/owner/repo/pull/123 [--output review.md]
  claude-review --diff-file ./pr.diff [--output review.md]

Options:
  --pr <url>              GitHub pull request URL to review.
  --diff-file <path>      Local diff file to review instead of fetching from GitHub.
  --output <path>         Write the Markdown review to a file.
  --model <name>          Optional Claude Code model override.
  --max-diff-bytes <n>    Diff budget sent to Claude. Default: ${DEFAULT_MAX_DIFF_BYTES}.
  --print-prompt          Print the assembled Claude input and exit.
  --help                  Show this help text.

Environment:
  GITHUB_TOKEN                 Optional token for fetching private or rate-limited PR diffs.
  CLAUDE_REVIEW_CLAUDE_BIN     Override the Claude Code binary name/path.`;
}

function parseArgs(argv) {
  const args = {
    maxDiffBytes: Number(process.env.CLAUDE_REVIEW_MAX_DIFF_BYTES || DEFAULT_MAX_DIFF_BYTES),
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];

    if (arg === '--help' || arg === '-h') args.help = true;
    else if (arg === '--print-prompt') args.printPrompt = true;
    else if (arg === '--pr') {
      args.pr = requireValue(arg, next);
      i += 1;
    } else if (arg === '--diff-file') {
      args.diffFile = requireValue(arg, next);
      i += 1;
    } else if (arg === '--output' || arg === '-o') {
      args.output = requireValue(arg, next);
      i += 1;
    } else if (arg === '--model') {
      args.model = requireValue(arg, next);
      i += 1;
    } else if (arg === '--max-diff-bytes') {
      args.maxDiffBytes = Number(requireValue(arg, next));
      i += 1;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!Number.isFinite(args.maxDiffBytes) || args.maxDiffBytes < 10_000) {
    throw new Error('--max-diff-bytes must be a number >= 10000.');
  }

  if (!args.help && Boolean(args.pr) === Boolean(args.diffFile)) {
    throw new Error('Provide exactly one of --pr or --diff-file.');
  }

  return args;
}

function requireValue(flag, value) {
  if (!value || value.startsWith('--')) {
    throw new Error(`${flag} requires a value.`);
  }
  return value;
}

function parseGitHubPrUrl(input) {
  let url;
  try {
    url = new URL(input);
  } catch {
    throw new Error(`Invalid PR URL: ${input}`);
  }

  if (url.hostname !== 'github.com') {
    throw new Error('Only github.com pull request URLs are supported.');
  }

  const match = url.pathname.match(/^\/([^/]+)\/([^/]+)\/pull\/(\d+)\/?$/);
  if (!match) {
    throw new Error('Expected a GitHub PR URL like https://github.com/owner/repo/pull/123.');
  }

  const [, owner, repo, number] = match;
  return {
    owner,
    repo,
    number,
    url: `https://github.com/${owner}/${repo}/pull/${number}`,
    apiDiffUrl: `https://api.github.com/repos/${owner}/${repo}/pulls/${number}`,
  };
}

async function fetchPrDiff(prUrl) {
  const pr = parseGitHubPrUrl(prUrl);
  const headers = {
    Accept: 'application/vnd.github.v3.diff',
    'User-Agent': 'claude-review-agent',
  };

  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }

  const attempts = 3;
  let lastError;

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await requestText(pr.apiDiffUrl, headers);
      if (response.status >= 200 && response.status < 300) {
        return {
          source: pr.url,
          diff: response.body,
        };
      }

      lastError = new Error(`${response.status} ${response.statusMessage}`);
      if (response.status < 500 || attempt === attempts) break;
    } catch (error) {
      lastError = error;
      if (attempt === attempts) break;
    }

    await delay(1000 * attempt);
  }

  throw new Error(`Failed to fetch PR diff from ${pr.apiDiffUrl} after ${attempts} attempts: ${lastError.message}`);
}

function delay(ms) {
  return new Promise((resolveDelay) => setTimeout(resolveDelay, ms));
}

function requestText(url, headers, redirectsRemaining = 5) {
  return new Promise((resolveRequest, rejectRequest) => {
    const req = request(url, { headers, timeout: 60_000 }, (res) => {
      const status = res.statusCode || 0;
      const location = res.headers.location;

      if ([301, 302, 303, 307, 308].includes(status) && location && redirectsRemaining > 0) {
        res.resume();
        const redirectedUrl = new URL(location, url).toString();
        requestText(redirectedUrl, headers, redirectsRemaining - 1).then(resolveRequest, rejectRequest);
        return;
      }

      let body = '';
      res.setEncoding('utf8');
      res.on('data', (chunk) => {
        body += chunk;
      });
      res.on('end', () => {
        resolveRequest({
          status,
          statusMessage: res.statusMessage || '',
          body,
        });
      });
    });

    req.on('timeout', () => {
      req.destroy(new Error('Request timed out after 60000 ms'));
    });
    req.on('error', rejectRequest);
    req.end();
  });
}

function readLocalDiff(diffFile) {
  const resolved = resolve(diffFile);
  if (!existsSync(resolved)) {
    throw new Error(`Diff file not found: ${resolved}`);
  }

  return {
    source: resolved,
    diff: readFileSync(resolved, 'utf8'),
  };
}

function stripAgentFrontmatter(agentSource) {
  if (!agentSource.startsWith('---')) return agentSource.trim();
  const closingIndex = agentSource.indexOf('\n---', 3);
  if (closingIndex === -1) return agentSource.trim();
  return agentSource.slice(closingIndex + '\n---'.length).trim();
}

function truncateDiff(diff, maxBytes) {
  const bytes = Buffer.byteLength(diff, 'utf8');
  if (bytes <= maxBytes) {
    return { diff, truncated: false, originalBytes: bytes, sentBytes: bytes };
  }

  const headBytes = Math.floor(maxBytes * 0.65);
  const tailBytes = maxBytes - headBytes;
  const head = Buffer.from(diff, 'utf8').subarray(0, headBytes).toString('utf8');
  const tail = Buffer.from(diff, 'utf8').subarray(bytes - tailBytes).toString('utf8');
  const notice = [
    '',
    '[Diff truncated by claude-review]',
    `Original diff size: ${bytes} bytes.`,
    `Sent budget: ${maxBytes} bytes.`,
    'Review the visible sections and lower confidence because middle content is omitted.',
    '',
  ].join('\n');

  return {
    diff: `${head}${notice}${tail}`,
    truncated: true,
    originalBytes: bytes,
    sentBytes: Buffer.byteLength(`${head}${notice}${tail}`, 'utf8'),
  };
}

function buildClaudeInput({ source, diff, truncation }) {
  const truncationNote = truncation.truncated
    ? `The diff was truncated from ${truncation.originalBytes} bytes to ${truncation.sentBytes} bytes. Mention this in confidence.`
    : `The complete diff was provided (${truncation.originalBytes} bytes).`;

  return [
    `Pull request source: ${source}`,
    `Fetched/reviewed at: ${new Date().toISOString()}`,
    truncationNote,
    '',
    'Review this diff and return the structured Markdown comment requested by the agent instructions.',
    '',
    '```diff',
    diff,
    '```',
    '',
  ].join('\n');
}

function runClaude({ input, model }) {
  const agentSource = readFileSync(agentPath, 'utf8');
  const agentPrompt = stripAgentFrontmatter(agentSource);
  const agents = {
    'pr-reviewer': {
      description: 'Reviews a GitHub pull request diff and returns a structured Markdown review comment.',
      prompt: agentPrompt,
      tools: [],
    },
  };

  const claudeArgs = [
    '--bare',
    '--agents',
    JSON.stringify(agents),
    '--agent',
    'pr-reviewer',
    '--print',
    '--output-format',
    'text',
    '--max-turns',
    '1',
  ];

  if (model) {
    claudeArgs.push('--model', model);
  }

  claudeArgs.push('Review the pull request diff supplied on stdin.');

  const result = spawnSync(CLAUDE_BINARY, claudeArgs, {
    input,
    encoding: 'utf8',
    maxBuffer: 20 * 1024 * 1024,
    windowsHide: true,
  });

  if (result.error) {
    if (result.error.code === 'ENOENT') {
      throw new Error(`Claude Code CLI not found. Install it with: npm install -g @anthropic-ai/claude-code`);
    }
    throw result.error;
  }

  if (result.status !== 0) {
    const stderr = result.stderr?.trim() || '(no stderr)';
    throw new Error(`Claude Code exited with status ${result.status}: ${stderr}`);
  }

  return normalizeReviewOutput(result.stdout.trimEnd()) + '\n';
}

function normalizeReviewOutput(output) {
  return output
    .replace(/[\u2013\u2014]/g, '-')
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201c\u201d]/g, '"')
    .replace(/\u00a0/g, ' ');
}

function writeOutput(target, content) {
  const resolved = resolve(target);
  mkdirSync(dirname(resolved), { recursive: true });
  writeFileSync(resolved, content, 'utf8');
  return resolved;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    process.stdout.write(`${usage()}\n`);
    return;
  }

  const { source, diff } = args.pr ? await fetchPrDiff(args.pr) : readLocalDiff(args.diffFile);
  const truncation = truncateDiff(diff, args.maxDiffBytes);
  const input = buildClaudeInput({ source, diff: truncation.diff, truncation });

  if (args.printPrompt) {
    process.stdout.write(input);
    return;
  }

  const review = runClaude({ input, model: args.model });

  if (args.output) {
    const resolved = writeOutput(args.output, review);
    process.stderr.write(`Wrote review to ${resolved}\n`);
  } else {
    process.stdout.write(review);
  }
}

main().catch((error) => {
  process.stderr.write(`claude-review: ${error.message}\n`);
  process.exit(1);
});
