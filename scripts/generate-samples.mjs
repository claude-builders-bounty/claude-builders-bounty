import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { fetchPullRequestInput } from '../src/github.mjs';
import { reviewInput } from '../src/reviewer.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const samples = [
  {
    url: 'https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2281',
    file: 'sample-outputs/claude-builders-2281.md',
  },
  {
    url: 'https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2271',
    file: 'sample-outputs/claude-builders-2271.md',
  },
];

for (const sample of samples) {
  process.stderr.write(`Reviewing ${sample.url} ...\n`);
  const input = await fetchPullRequestInput(sample.url, {
    token: process.env.GITHUB_TOKEN,
    maxDiffChars: 120_000,
  });
  const result = await reviewInput(input, { model: process.env.CLAUDE_REVIEW_MODEL });
  const header = `# Sample review\n\n- Source PR: ${sample.url}\n- Diff truncated: ${input.diffTruncated ? 'yes' : 'no'}\n- Generated with: Claude Code \`pr-reviewer\` agent\n\n---\n\n`;
  await fs.writeFile(path.join(root, sample.file), `${header}${result.markdown}\n`, 'utf8');
  process.stderr.write(`Wrote ${sample.file}\n`);
}
