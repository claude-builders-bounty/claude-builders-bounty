#!/usr/bin/env node
import { spawnSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import process from 'node:process'
import {
  buildPrompt,
  fetchPullRequestDiff,
  heuristicReview,
  parseArgs,
  parsePullRequestUrl,
} from '../src/claude-review.js'

async function main() {
  const options = parseArgs(process.argv.slice(2))

  if (options.help) {
    console.log(`claude-review

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123 [--post]
  claude-review --diff ./pr.diff [--title "PR title"]

Options:
  --pr <url>          GitHub pull request URL to review
  --diff <path>       Local unified diff file to review instead of fetching GitHub
  --mode <mode>       claude | heuristic | auto (default: auto)
  --post              Post the review as a GitHub PR comment (requires GITHUB_TOKEN)
  --title <title>     Optional title/context included in the prompt
  --help              Show this message

Output is structured Markdown with summary, risks, suggestions, and confidence.`)
    return
  }

  if (!options.pr && !options.diff) {
    throw new Error('Provide either --pr <GitHub PR URL> or --diff <path>.')
  }

  const diff = options.diff
    ? readFileSync(options.diff, 'utf8')
    : await fetchPullRequestDiff(options.pr)

  const review = await createReview({ ...options, diff })
  console.log(review)

  if (options.post) {
    if (!options.pr) throw new Error('--post requires --pr')
    await postGithubComment(options.pr, review)
    console.error('Posted review comment to GitHub.')
  }
}

async function createReview(options) {
  const mode = options.mode ?? 'auto'
  if (mode !== 'heuristic' && commandExists('claude')) {
    const prompt = buildPrompt({ prUrl: options.pr, title: options.title, diff: options.diff })
    const result = spawnSync('claude', ['--print'], {
      input: prompt,
      encoding: 'utf8',
      maxBuffer: 10 * 1024 * 1024,
    })
    if (result.status === 0 && result.stdout.trim()) {
      return ensureStructuredReview(result.stdout.trim())
    }
    if (mode === 'claude') {
      throw new Error(`Claude CLI failed: ${result.stderr || result.stdout}`)
    }
  }
  return heuristicReview({ prUrl: options.pr, title: options.title, diff: options.diff })
}

function commandExists(command) {
  const result = spawnSync('sh', ['-lc', `command -v ${JSON.stringify(command)} >/dev/null 2>&1`])
  return result.status === 0
}

function ensureStructuredReview(review) {
  const required = ['## Summary', '## Identified risks', '## Improvement suggestions', '## Confidence']
  const missing = required.filter((heading) => !review.includes(heading))
  if (missing.length === 0) return review
  return `${review}\n\n---\n\n${missing.map((heading) => `${heading}\n- Not provided by the model.`).join('\n\n')}`
}

async function postGithubComment(prUrl, body) {
  const token = process.env.GITHUB_TOKEN
  if (!token) throw new Error('GITHUB_TOKEN is required for --post.')
  const { owner, repo, number } = parsePullRequestUrl(prUrl)
  const response = await fetch(`https://api.github.com/repos/${owner}/${repo}/issues/${number}/comments`, {
    method: 'POST',
    headers: {
      Accept: 'application/vnd.github+json',
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      'User-Agent': 'claude-review-cli',
      'X-GitHub-Api-Version': '2022-11-28',
    },
    body: JSON.stringify({ body }),
  })
  if (!response.ok) {
    throw new Error(`GitHub comment failed (${response.status}): ${await response.text()}`)
  }
}

main().catch((error) => {
  console.error(`claude-review: ${error.message}`)
  process.exitCode = 1
})
