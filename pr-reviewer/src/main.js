import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

export function parseArgs(args) {
  const prIndex = args.indexOf('--pr');
  if (prIndex === -1 || !args[prIndex + 1]) {
    return { error: 'Usage: claude-review --pr <github-pr-url>' };
  }
  return { prUrl: args[prIndex + 1] };
}

export function parsePrUrl(prUrl) {
  const m = prUrl.match(/^https:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)(?:\/.*)?$/);
  if (!m) {
    throw new Error('Expected a GitHub PR URL like https://github.com/owner/repo/pull/123');
  }
  return { repo: `${m[1]}/${m[2]}`, number: m[3] };
}

export function renderReview({ pr, diffText, analysis, repo }) {
  const filesChanged = pr.changedFiles ?? pr.files?.length ?? 0;
  return `# PR Review: ${pr.title}\n\n` +
    `**PR:** ${pr.url}\n` +
    `**Repository:** ${repo}\n` +
    `**Author:** ${pr.author?.login ?? 'Unknown'}\n` +
    `**Files changed:** ${filesChanged}\n\n` +
    `## Summary\n${analysis.summary}\n\n` +
    `## Risks\n${analysis.risks.map(x => `- ${x}`).join('\n')}\n\n` +
    `## Improvement Suggestions\n${analysis.suggestions.map(x => `- ${x}`).join('\n')}\n\n` +
    `## Confidence\n${analysis.confidence}\n\n` +
    `---\nGenerated from PR metadata and diff (${Math.min(diffText.length, 12000)} chars analyzed).`;
}

export function heuristicAnalyze(pr, diffText) {
  const additions = pr.additions ?? 0;
  const deletions = pr.deletions ?? 0;
  const changedFiles = pr.files?.map(f => f.path) ?? [];
  const touchedTests = changedFiles.some(x => /test|spec/i.test(x));
  const touchedConfig = changedFiles.some(x => /(package|tsconfig|docker|workflow|config|yml|yaml|json)/i.test(x));
  const touchedDocs = changedFiles.some(x => /readme|docs?\//i.test(x));
  const bigChange = additions + deletions > 400 || changedFiles.length > 12;

  const summaryParts = [];
  summaryParts.push(`This PR updates ${changedFiles.length || 'a small number of'} file(s) with roughly +${additions}/-${deletions} line changes.`);
  if (touchedConfig) summaryParts.push('It touches configuration or automation-related files, which can affect local and CI behavior.');
  else if (touchedDocs) summaryParts.push('A meaningful portion of the change appears documentation-oriented.');
  else summaryParts.push('The diff appears focused on implementation changes rather than repository configuration.');
  if (!touchedTests && !touchedDocs) summaryParts.push('There is no obvious test coverage in the changed paths, so behavior changes may rely on manual verification.');

  const risks = [];
  if (bigChange) risks.push('The change set is relatively broad, increasing review and regression risk.');
  if (!touchedTests) risks.push('No obvious test files were changed, so regressions may slip through if behavior changed.');
  if (touchedConfig) risks.push('Config or workflow changes can break environments in ways that are not obvious from code review alone.');
  if (/TODO|FIXME/.test(diffText)) risks.push('The diff includes TODO/FIXME markers that may indicate incomplete follow-up work.');
  if (risks.length === 0) risks.push('No major structural risks stand out from metadata alone, but logic changes still need scenario-based verification.');

  const suggestions = [];
  if (!touchedTests) suggestions.push('Add or reference tests that exercise the changed behavior.');
  if (touchedConfig) suggestions.push('Document any environment, secret, or CI assumptions introduced by the config changes.');
  suggestions.push('Include before/after behavior notes or screenshots if the PR affects user-facing workflows.');
  suggestions.push('Call out edge cases and rollback considerations in the PR description for easier reviewer validation.');

  let confidence = 'Medium';
  if (bigChange && !touchedTests) confidence = 'Low';
  else if (!bigChange && touchedTests) confidence = 'High';

  return { summary: summaryParts.join(' '), risks, suggestions, confidence };
}

async function ghJson(args, maxBufferMb = 10) {
  const { stdout } = await execFileAsync('gh', args, { maxBuffer: 1024 * 1024 * maxBufferMb });
  return stdout;
}

export async function fetchPr(prUrl) {
  const { repo, number } = parsePrUrl(prUrl);
  try {
    const stdout = await ghJson([
      'pr', 'view', number,
      '--repo', repo,
      '--json', 'title,url,author,additions,deletions,files,body,number,changedFiles'
    ]);
    return { repo, pr: JSON.parse(stdout) };
  } catch (err) {
    throw new Error(`Failed to fetch PR metadata for ${prUrl}: ${err.stderr || err.message}`.trim());
  }
}

export async function fetchDiff(prUrl) {
  const { repo, number } = parsePrUrl(prUrl);
  try {
    const { stdout } = await execFileAsync('gh', ['pr', 'diff', number, '--repo', repo], { maxBuffer: 1024 * 1024 * 20 });
    return stdout;
  } catch (err) {
    throw new Error(`Failed to fetch PR diff for ${prUrl}: ${err.stderr || err.message}`.trim());
  }
}

export async function runCli(args) {
  const parsed = parseArgs(args);
  if (parsed.error) {
    console.error(parsed.error);
    return 1;
  }

  try {
    const { repo, pr } = await fetchPr(parsed.prUrl);
    const diffText = await fetchDiff(parsed.prUrl);
    const analysis = heuristicAnalyze(pr, diffText.slice(0, 12000));
    console.log(renderReview({ pr, diffText, analysis, repo }));
    return 0;
  } catch (err) {
    console.error(err.message || String(err));
    return 1;
  }
}
