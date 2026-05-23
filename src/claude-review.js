const MAX_DIFF_CHARS = 120_000

export function parseArgs(args) {
  const options = {}
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index]
    if (arg === '--help' || arg === '-h') options.help = true
    else if (arg === '--post') options.post = true
    else if (arg === '--pr') options.pr = requireValue(args, ++index, '--pr')
    else if (arg === '--diff') options.diff = requireValue(args, ++index, '--diff')
    else if (arg === '--mode') options.mode = requireValue(args, ++index, '--mode')
    else if (arg === '--title') options.title = requireValue(args, ++index, '--title')
    else throw new Error(`Unknown argument: ${arg}`)
  }
  if (options.mode && !['auto', 'claude', 'heuristic'].includes(options.mode)) {
    throw new Error('--mode must be one of: auto, claude, heuristic')
  }
  return options
}

function requireValue(args, index, flag) {
  const value = args[index]
  if (!value || value.startsWith('--')) throw new Error(`${flag} requires a value`)
  return value
}

export function parsePullRequestUrl(url) {
  const match = /^https:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)(?:[/?#].*)?$/.exec(url)
  if (!match) throw new Error(`Invalid GitHub PR URL: ${url}`)
  return { owner: match[1], repo: match[2], number: Number(match[3]) }
}

export async function fetchPullRequestDiff(prUrl) {
  const { owner, repo, number } = parsePullRequestUrl(prUrl)
  const response = await fetch(`https://github.com/${owner}/${repo}/pull/${number}.diff`, {
    headers: { 'User-Agent': 'claude-review-cli' },
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch PR diff (${response.status}): ${await response.text()}`)
  }
  return response.text()
}

export function buildPrompt({ prUrl, title, diff }) {
  return `You are a Claude Code sub-agent acting as a senior code reviewer.
Review this pull request diff and return ONLY structured Markdown with these exact sections:

## Summary
2-3 concise sentences explaining the change.

## Identified risks
- Bullet list of concrete risks, edge cases, or regressions. If none, say "No major risks identified."

## Improvement suggestions
- Bullet list of actionable suggestions. If none, say "No immediate improvements suggested."

## Confidence
Low / Medium / High, with one short reason.

Context:
${title ? `Title: ${title}\n` : ''}${prUrl ? `PR: ${prUrl}\n` : ''}
Diff:
\`\`\`diff
${truncateDiff(diff)}
\`\`\`
`
}

export function heuristicReview({ prUrl, title, diff }) {
  const stats = summarizeDiff(diff)
  const risks = detectRisks(diff, stats)
  const suggestions = detectSuggestions(diff, stats)
  const confidence = confidenceFor(stats, risks)
  const files = stats.files.slice(0, 8).join(', ') || 'no changed files detected'

  return `## Summary
${title ? `${title}. ` : ''}This PR changes ${stats.files.length} file${stats.files.length === 1 ? '' : 's'} (${files}) with ${stats.added} added line${stats.added === 1 ? '' : 's'} and ${stats.removed} removed line${stats.removed === 1 ? '' : 's'}. The diff appears to be ${stats.primaryKind}, based on the changed paths and content.

## Identified risks
${formatBullets(risks)}

## Improvement suggestions
${formatBullets(suggestions)}

## Confidence
${confidence.level} — ${confidence.reason}${prUrl ? `\n\nReviewed PR: ${prUrl}` : ''}`
}

function summarizeDiff(diff) {
  const files = []
  let added = 0
  let removed = 0
  for (const line of diff.split('\n')) {
    if (line.startsWith('diff --git ')) {
      const match = /^diff --git a\/(.*?) b\/(.*)$/.exec(line)
      files.push(match?.[2] ?? line.replace('diff --git ', ''))
    } else if (line.startsWith('+') && !line.startsWith('+++')) added += 1
    else if (line.startsWith('-') && !line.startsWith('---')) removed += 1
  }
  const primaryKind = classify(files)
  return { files: [...new Set(files)], added, removed, primaryKind }
}

function classify(files) {
  if (files.length === 0) return 'empty or metadata-only'
  if (files.every((file) => /(^|\/)(readme|docs?|\.md$)/i.test(file))) return 'documentation-focused'
  if (files.some((file) => /test|spec|__tests__/i.test(file))) return 'test-related'
  if (files.some((file) => /package(-lock)?\.json|pnpm-lock|yarn\.lock|bun\.lock/i.test(file))) return 'dependency or packaging related'
  if (files.some((file) => /src|lib|app|server|client/i.test(file))) return 'application code related'
  return 'general code or configuration related'
}

function detectRisks(diff, stats) {
  const risks = []
  if (stats.files.length === 0) risks.push('The diff did not expose changed files, so the review may miss implementation-specific risks.')
  if (stats.added + stats.removed > 800) risks.push('Large diff size increases the chance of missed regressions and warrants focused maintainer review.')
  if (/password|secret|token|api[_-]?key/i.test(diff)) risks.push('The diff contains credential-like terms; verify no secrets or sensitive values are committed.')
  if (/eval\(|Function\(|child_process|exec\(|spawn\(/.test(diff)) risks.push('The change touches dynamic execution or subprocess behavior; validate inputs and error handling carefully.')
  if (/DROP TABLE|DELETE FROM|ALTER TABLE|migration/i.test(diff)) risks.push('Database or migration-related changes can be hard to roll back; check migration safety and data compatibility.')
  if (/auth|permission|role|admin|session|cookie|csrf/i.test(diff)) risks.push('Authentication or authorization paths appear affected; verify access-control and session edge cases.')
  if (/TODO|FIXME|HACK/.test(diff)) risks.push('New TODO/FIXME/HACK markers may indicate unfinished behavior that should be resolved before merge.')
  if (risks.length === 0) risks.push('No major risks identified from the diff alone.')
  return risks
}

function detectSuggestions(diff, stats) {
  const suggestions = []
  const docsOnly = stats.files.length > 0 && stats.files.every((file) => /(^|\/)(README|docs?|.*\.md$)/i.test(file))
  const markupOnly = stats.files.length > 0 && stats.files.every((file) => /\.(html|md|mdx|css)$/i.test(file))
  if (!docsOnly && !markupOnly && !/test|spec|assert|expect\(/i.test(diff)) {
    suggestions.push('Add or update tests that exercise the changed behavior, especially edge cases and failure paths.')
  }
  if (docsOnly) suggestions.push('Preview the rendered Markdown to verify formatting, links, and examples.')
  if (markupOnly && !docsOnly) suggestions.push('Preview the rendered page to verify visual output and accessibility basics.')
  if (stats.files.some((file) => /README|docs?/i.test(file)) && stats.files.some((file) => /src|lib|app/i.test(file))) {
    suggestions.push('Confirm the documentation examples match the final runtime/API behavior.')
  }
  if (/catch\s*\([^)]*\)\s*{\s*}/.test(diff)) suggestions.push('Avoid swallowing errors silently; log, rethrow, or return a useful failure response.')
  if (/console\.log/.test(diff)) suggestions.push('Remove debug logging or replace it with the project’s structured logging approach before merge.')
  if (stats.added + stats.removed > 250) suggestions.push('Consider splitting independent changes into smaller PRs if the feature and refactor pieces can be reviewed separately.')
  if (suggestions.length === 0) suggestions.push('No immediate improvements suggested; validate with the project’s normal test and lint commands.')
  return suggestions
}

function confidenceFor(stats, risks) {
  if (stats.files.length === 0) return { level: 'Low', reason: 'the diff could not be inspected in enough detail.' }
  if (stats.added + stats.removed > 800 || risks.length > 4) return { level: 'Low', reason: 'the change is large or high-risk for an automated review.' }
  if (stats.added + stats.removed > 250 || risks.length > 2) return { level: 'Medium', reason: 'the diff is moderate in size or includes notable risk areas.' }
  return { level: 'High', reason: 'the diff is small enough for a focused automated review.' }
}

function formatBullets(items) {
  return items.map((item) => `- ${item}`).join('\n')
}

function truncateDiff(diff) {
  if (diff.length <= MAX_DIFF_CHARS) return diff
  return `${diff.slice(0, MAX_DIFF_CHARS)}\n\n...diff truncated to ${MAX_DIFF_CHARS} characters...`
}
