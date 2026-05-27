#!/usr/bin/env node
import { writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const USER_AGENT = "claude-review-agent";

export function parsePullRequestUrl(value) {
  const match = value?.match(/^https:\/\/github\.com\/([^/\s]+)\/([^/\s]+)\/pull\/(\d+)(?:[/?#].*)?$/);
  if (!match) {
    throw new Error("Expected --pr to be a GitHub pull request URL.");
  }

  return {
    owner: match[1],
    repo: match[2],
    number: Number(match[3]),
  };
}

function parseArgs(argv) {
  const args = {
    maxDiffLines: 2000,
    postComment: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--pr") {
      args.pr = argv[++index];
    } else if (arg === "--output") {
      args.output = argv[++index];
    } else if (arg === "--max-diff-lines") {
      args.maxDiffLines = Number(argv[++index]);
    } else if (arg === "--post-comment") {
      args.postComment = true;
    } else if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return args;
}

function usage() {
  return [
    "Usage:",
    "  node claude-review.mjs --pr https://github.com/owner/repo/pull/123",
    "",
    "Options:",
    "  --output <file>       Save Markdown review to a file",
    "  --post-comment        Post the review to GitHub using GITHUB_TOKEN",
    "  --max-diff-lines <n>  Limit diff lines analyzed before truncation",
  ].join("\n");
}

async function githubFetch(url, accept = "application/vnd.github+json") {
  const headers = {
    Accept: accept,
    "User-Agent": USER_AGENT,
  };

  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }

  const response = await fetch(url, { headers });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`GitHub request failed: ${response.status} ${response.statusText}\n${body}`);
  }

  return accept.includes("json") ? response.json() : response.text();
}

export async function fetchPullRequest({ owner, repo, number }) {
  const baseUrl = `https://api.github.com/repos/${owner}/${repo}/pulls/${number}`;
  const [metadata, diff] = await Promise.all([
    githubFetch(baseUrl),
    githubFetch(baseUrl, "application/vnd.github.v3.diff"),
  ]);

  return { metadata, diff };
}

function emptyStats() {
  return {
    files: new Map(),
    added: 0,
    removed: 0,
    truncated: false,
  };
}

export function analyzeDiff(diff, options = {}) {
  const maxDiffLines = options.maxDiffLines ?? 2000;
  const stats = emptyStats();
  const lines = diff.split(/\r?\n/);
  let currentFile = null;

  for (let index = 0; index < lines.length; index += 1) {
    if (index >= maxDiffLines) {
      stats.truncated = true;
      break;
    }

    const line = lines[index];
    const fileMatch = line.match(/^diff --git a\/(.+?) b\/(.+)$/);
    if (fileMatch) {
      currentFile = fileMatch[2];
      if (!stats.files.has(currentFile)) {
        stats.files.set(currentFile, { added: 0, removed: 0 });
      }
      continue;
    }

    if (!currentFile || line.startsWith("+++") || line.startsWith("---")) {
      continue;
    }

    const fileStats = stats.files.get(currentFile);
    if (line.startsWith("+")) {
      stats.added += 1;
      fileStats.added += 1;
    } else if (line.startsWith("-")) {
      stats.removed += 1;
      fileStats.removed += 1;
    }
  }

  return {
    ...stats,
    fileList: Array.from(stats.files.entries()).map(([path, counts]) => ({
      path,
      ...counts,
      churn: counts.added + counts.removed,
    })),
  };
}

function fileMatches(fileList, pattern) {
  return fileList.some((file) => pattern.test(file.path));
}

function diffContains(diff, pattern) {
  return pattern.test(diff);
}

export function buildReview(metadata, diff, options = {}) {
  const stats = analyzeDiff(diff, options);
  const fileCount = stats.fileList.length;
  const churn = stats.added + stats.removed;
  const largestFiles = [...stats.fileList].sort((a, b) => b.churn - a.churn).slice(0, 3);
  const changedNames = largestFiles.map((file) => `\`${file.path}\``).join(", ") || "no files";

  const risks = [];
  const suggestions = [];

  const hasTests = fileMatches(stats.fileList, /(^|\/)(test|tests|__tests__)\/|(\.|-)(test|spec)\.[jt]sx?$|(^|\/)test_.*\.py$|_test\.go$/i);
  const touchesRuntimeCode = fileMatches(stats.fileList, /\.(js|jsx|ts|tsx|py|go|rs|java|rb|php|mjs|cjs)$/i);
  const touchesWorkflow = fileMatches(stats.fileList, /^\.github\/workflows\//i);
  const touchesPackage = fileMatches(stats.fileList, /(^|\/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb?)$/i);
  const touchesDatabase = fileMatches(stats.fileList, /(migration|schema|database|db|sqlite|turso|prisma|drizzle)/i);
  const touchesAuthOrBilling = diffContains(diff, /\b(auth|session|password|secret|permission|payment|billing|invoice|stripe|paypal)\b/i);
  const removesCode = stats.removed > Math.max(40, stats.added);

  if (stats.truncated) {
    risks.push("The diff was truncated during analysis, so later files may contain unreviewed behavior.");
  }
  if (churn > 800) {
    risks.push(`Large diff size (${churn} changed lines) makes regression risk harder to assess from a single pass.`);
  }
  if (touchesRuntimeCode && !hasTests) {
    risks.push("Runtime code changed without an accompanying test file in this PR.");
  }
  if (touchesWorkflow) {
    risks.push("CI or automation workflow changes can fail only after GitHub evaluates repository-level permissions and secrets.");
  }
  if (touchesPackage) {
    risks.push("Dependency or package metadata changes may affect install reproducibility across local and CI environments.");
  }
  if (touchesDatabase) {
    risks.push("Database or migration-related changes need backwards-compatible upgrade and rollback behavior.");
  }
  if (touchesAuthOrBilling) {
    risks.push("Authentication, authorization, or payment-adjacent logic appears in the diff and deserves focused manual verification.");
  }
  if (removesCode) {
    risks.push("The PR removes substantially more code than it adds; confirm no supported path was removed accidentally.");
  }
  if (risks.length === 0) {
    risks.push("No obvious high-risk pattern was detected from the diff alone.");
  }

  if (touchesRuntimeCode && !hasTests) {
    suggestions.push("Add a focused regression test or a small fixture that exercises the changed behavior.");
  }
  if (touchesWorkflow) {
    suggestions.push("Run the workflow on a throwaway branch or include evidence from a successful dry run.");
  }
  if (touchesPackage) {
    suggestions.push("Include the exact install and test command used to validate lockfile or package changes.");
  }
  if (touchesDatabase) {
    suggestions.push("Document migration order and confirm the change is safe for existing local data.");
  }
  suggestions.push("Add the validation command and any sample output to the PR description so reviewers can reproduce the result.");

  let confidence = "High";
  if (stats.truncated || churn > 800 || risks.length >= 4) {
    confidence = "Low";
  } else if (!hasTests || churn > 250 || risks.length >= 2) {
    confidence = "Medium";
  }

  const title = metadata.title || `PR #${metadata.number}`;
  const repo = metadata.base?.repo?.full_name || "the repository";
  const summary = [
    `This PR updates ${repo} with "${title}".`,
    `It changes ${fileCount} file${fileCount === 1 ? "" : "s"} with ${stats.added} additions and ${stats.removed} deletions; the largest touched paths are ${changedNames}.`,
    metadata.body ? "The PR description provides extra context, but the diff should still be validated with the commands below." : "The PR description is sparse, so validation evidence is especially important.",
  ];

  return {
    summary,
    risks,
    suggestions: [...new Set(suggestions)],
    confidence,
    stats,
  };
}

export function renderReview(review) {
  return [
    "## Summary",
    "",
    review.summary.join(" "),
    "",
    "## Identified Risks",
    "",
    ...review.risks.map((risk) => `- ${risk}`),
    "",
    "## Improvement Suggestions",
    "",
    ...review.suggestions.map((suggestion) => `- ${suggestion}`),
    "",
    "## Confidence",
    "",
    review.confidence,
    "",
  ].join("\n");
}

async function postComment({ owner, repo, number }, body) {
  if (!process.env.GITHUB_TOKEN) {
    throw new Error("--post-comment requires GITHUB_TOKEN.");
  }

  const response = await fetch(`https://api.github.com/repos/${owner}/${repo}/issues/${number}/comments`, {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${process.env.GITHUB_TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": USER_AGENT,
    },
    body: JSON.stringify({ body }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to post comment: ${response.status} ${response.statusText}\n${text}`);
  }

  return response.json();
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.pr) {
    console.log(usage());
    process.exit(args.help ? 0 : 1);
  }

  const pr = parsePullRequestUrl(args.pr);
  const { metadata, diff } = await fetchPullRequest(pr);
  const review = buildReview(metadata, diff, { maxDiffLines: args.maxDiffLines });
  const markdown = renderReview(review);

  if (args.output) {
    await writeFile(args.output, markdown, "utf8");
  } else {
    console.log(markdown);
  }

  if (args.postComment) {
    const comment = await postComment(pr, markdown);
    console.error(`Posted comment: ${comment.html_url}`);
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] || "").href) {
  main().catch((error) => {
    console.error(error.message);
    process.exit(1);
  });
}
