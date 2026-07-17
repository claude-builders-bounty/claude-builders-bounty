const RISK_RULES = [
  {
    label: 'Deletes or renames existing code paths; verify callers, migrations, and release notes.',
    test: (diff) => /^deleted file mode|^rename from /m.test(diff)
  },
  {
    label: 'Touches authentication, tokens, or secrets; confirm no sensitive values are logged or exposed.',
    test: (diff) => /auth|token|secret|password|credential|session/i.test(diff)
  },
  {
    label: 'Changes persistence or schema-related code; check migration and rollback behavior.',
    test: (diff) => /migration|schema|database|db\.|sql|prisma|typeorm/i.test(diff)
  },
  {
    label: 'Adds network or process execution behavior; validate inputs and failure handling.',
    test: (diff) => /fetch\(|axios|child_process|spawn\(|exec\(|http\.request|https\.request/i.test(diff)
  },
  {
    label: 'Includes test snapshot or lockfile churn; confirm it is intentional and reproducible.',
    test: (diff) => /(^diff --git .*\.snap\b)|(^diff --git .*lock)/m.test(diff)
  }
];

export function parseGitHubPullRequestUrl(url) {
  const match = String(url).match(/^https:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)(?:[/?#].*)?$/);
  if (!match) return null;
  return { owner: match[1], repo: match[2], pullNumber: Number(match[3]) };
}

export function parseDiffStats(diff) {
  const files = [];
  let additions = 0;
  let deletions = 0;

  for (const line of diff.split('\n')) {
    if (line.startsWith('diff --git ')) {
      const file = line.split(' b/')[1] || line.replace('diff --git ', '');
      files.push(file.trim());
      continue;
    }
    if (line.startsWith('+') && !line.startsWith('+++')) additions += 1;
    if (line.startsWith('-') && !line.startsWith('---')) deletions += 1;
  }

  return { files, additions, deletions };
}

function summarize(stats) {
  const fileList = stats.files.slice(0, 5).join(', ') || 'the submitted diff';
  const overflow = stats.files.length > 5 ? ` and ${stats.files.length - 5} more file(s)` : '';
  return [
    `This PR updates ${stats.files.length || 'unknown'} file(s): ${fileList}${overflow}.`,
    `The diff contains ${stats.additions} added line(s) and ${stats.deletions} removed line(s), so the main review focus should be behavior changes and regression coverage around the touched paths.`
  ];
}

function risksFor(diff, stats) {
  const risks = RISK_RULES.filter((rule) => rule.test(diff)).map((rule) => rule.label);
  if (stats.files.length > 12) {
    risks.push('Broad file coverage increases review surface; split or document scope if changes are unrelated.');
  }
  if (risks.length === 0) {
    risks.push('No obvious high-risk patterns detected from the diff text; still verify behavior manually.');
  }
  return risks;
}

function suggestionsFor(diff, stats) {
  const suggestions = [];
  const hasTests = stats.files.some((file) => /test|spec|__tests__/i.test(file));
  const hasDocs = stats.files.some((file) => /readme|docs?\//i.test(file));

  if (!hasTests) suggestions.push('Add or update automated tests for the changed behavior.');
  if (!hasDocs) suggestions.push('Update README or usage docs when user-facing behavior changes.');
  if (/TODO|FIXME|console\.log/i.test(diff)) {
    suggestions.push('Resolve temporary TODO/FIXME notes or debug logging before merge.');
  }
  suggestions.push('Include the exact local verification commands and results in the PR description.');
  return suggestions;
}

function confidenceFor(stats, risks) {
  if (stats.files.length === 0) return 'Low';
  if (risks.length >= 4 || stats.files.length > 15) return 'Medium';
  return 'High';
}

export function analyzeDiff(diff, options = {}) {
  if (!diff || !diff.trim()) {
    throw new Error('Diff is empty.');
  }
  const stats = parseDiffStats(diff);
  const risks = risksFor(diff, stats);
  return {
    source: options.source || 'unknown',
    summary: summarize(stats),
    risks,
    suggestions: suggestionsFor(diff, stats),
    confidence: confidenceFor(stats, risks),
    stats
  };
}

export function formatReview(review) {
  return `## Claude Review\n\n### Summary\n${review.summary.map((line) => `- ${line}`).join('\n')}\n\n### Identified Risks\n${review.risks.map((line) => `- ${line}`).join('\n')}\n\n### Improvement Suggestions\n${review.suggestions.map((line) => `- ${line}`).join('\n')}\n\n### Confidence\n${review.confidence}\n`;
}
