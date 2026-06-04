#!/usr/bin/env node

const fs = require("fs");
const https = require("https");

const HELP = `Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --post
  claude-review --pr https://github.com/owner/repo/pull/123 --diff-file ./pr.diff --no-fetch

Options:
  --pr <url>          GitHub pull request URL to review.
  --diff-file <path>  Read a local diff instead of fetching it.
  --post             Post the generated review as a PR comment. Requires GITHUB_TOKEN.
  --no-fetch         Do not fetch from GitHub. Requires --diff-file.
  --help             Show this help text.
`;

function parseArgs(argv) {
  const args = { post: false, noFetch: false };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") args.help = true;
    else if (arg === "--post") args.post = true;
    else if (arg === "--no-fetch") args.noFetch = true;
    else if (arg === "--pr") args.pr = argv[++i];
    else if (arg === "--diff-file") args.diffFile = argv[++i];
    else throw new Error(`Unknown argument: ${arg}`);
  }

  if (!args.help && !args.pr) {
    throw new Error("Missing required --pr <url> argument.");
  }

  if (args.noFetch && !args.diffFile) {
    throw new Error("--no-fetch requires --diff-file.");
  }

  return args;
}

function parsePullRequestUrl(url) {
  const match = String(url).match(
    /^https:\/\/github\.com\/([^/\s]+)\/([^/\s]+)\/pull\/(\d+)\/?$/
  );

  if (!match) {
    throw new Error("Expected --pr to be a GitHub pull request URL.");
  }

  return {
    owner: match[1],
    repo: match[2],
    number: Number(match[3]),
  };
}

function request(url, options = {}, body) {
  return new Promise((resolve, reject) => {
    const req = https.request(url, options, (res) => {
      let data = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => {
        data += chunk;
      });
      res.on("end", () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(data);
          return;
        }

        reject(
          new Error(
            `GitHub request failed (${res.statusCode}): ${data.slice(0, 300)}`
          )
        );
      });
    });

    req.on("error", reject);
    if (body) req.write(body);
    req.end();
  });
}

function fetchDiff(pr) {
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  const headers = {
    "User-Agent": "claude-review-cli",
    Accept: "application/vnd.github.v3.diff",
    "X-GitHub-Api-Version": "2022-11-28",
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const url = `https://api.github.com/repos/${pr.owner}/${pr.repo}/pulls/${pr.number}`;
  return request(url, {
    headers,
  });
}

function parseDiff(diff) {
  const files = [];
  let current = null;

  for (const line of diff.split(/\r?\n/)) {
    if (line.startsWith("diff --git ")) {
      const match = line.match(/^diff --git a\/(.+) b\/(.+)$/);
      current = {
        oldPath: match ? match[1] : "unknown",
        path: match ? match[2] : "unknown",
        additions: 0,
        deletions: 0,
        hunks: 0,
        binary: false,
      };
      files.push(current);
      continue;
    }

    if (!current) continue;
    if (line.startsWith("+++ b/")) current.path = line.slice(6);
    else if (line.startsWith("@@")) current.hunks += 1;
    else if (line.startsWith("Binary files ")) current.binary = true;
    else if (line.startsWith("+") && !line.startsWith("+++")) current.additions += 1;
    else if (line.startsWith("-") && !line.startsWith("---")) current.deletions += 1;
  }

  return files;
}

function classifyPath(path) {
  if (/(\b|\/)(test|tests|spec|__tests__)(\/|\.|$)/i.test(path)) return "tests";
  if (/\.(md|mdx|rst|txt)$/i.test(path)) return "documentation";
  if (/(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|package\.json)$/i.test(path)) return "dependencies";
  if (/^\.github\/workflows\//.test(path)) return "automation";
  if (/\.(js|jsx|ts|tsx|py|rb|go|rs|java|cs|php|sh)$/i.test(path)) return "source";
  return "assets/configuration";
}

function formatList(items) {
  return items.map((item) => `- ${item}`).join("\n");
}

function summarize(files, pr) {
  const changed = files.length;
  const additions = files.reduce((sum, file) => sum + file.additions, 0);
  const deletions = files.reduce((sum, file) => sum + file.deletions, 0);
  const byType = new Map();

  for (const file of files) {
    const type = classifyPath(file.path);
    byType.set(type, (byType.get(type) || 0) + 1);
  }

  const topTypes = [...byType.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([type, count]) => `${count} ${type} file${count === 1 ? "" : "s"}`);

  const sentenceOne = `This PR updates ${changed} file${changed === 1 ? "" : "s"} in ${pr.owner}/${pr.repo}, with ${additions} addition${additions === 1 ? "" : "s"} and ${deletions} deletion${deletions === 1 ? "" : "s"}.`;
  const sentenceTwo = topTypes.length
    ? `The changes are concentrated in ${topTypes.join(", ")}.`
    : "No changed files were detected in the diff.";
  const sentenceThree =
    changed > 8 || additions + deletions > 500
      ? "Because the diff is broad, review should focus on behavior changes, release impact, and test coverage."
      : "The diff is small enough for focused review of correctness and coverage.";

  return `${sentenceOne} ${sentenceTwo} ${sentenceThree}`;
}

function identifyRisks(files) {
  const risks = [];
  const totalChanged = files.reduce((sum, file) => sum + file.additions + file.deletions, 0);

  if (files.some((file) => classifyPath(file.path) === "dependencies")) {
    risks.push("Dependency or package metadata changed; verify lockfile consistency and runtime compatibility.");
  }

  if (files.some((file) => classifyPath(file.path) === "automation")) {
    risks.push("Workflow automation changed; confirm permissions, event triggers, and secret exposure are appropriate.");
  }

  if (files.some((file) => file.path.match(/\.(sh|bash)$/i))) {
    risks.push("Shell script changes can fail across environments; validate quoting, exit behavior, and executable permissions.");
  }

  if (files.some((file) => file.binary)) {
    risks.push("Binary file changes cannot be meaningfully reviewed from textual diff output.");
  }

  if (totalChanged > 500) {
    risks.push("Large diff size increases the chance of missed regressions during manual review.");
  }

  if (!files.some((file) => classifyPath(file.path) === "tests")) {
    risks.push("No test files changed; behavior changes may not be covered by automated checks.");
  }

  return risks.length ? risks : ["No obvious high-risk areas were detected from the diff shape."];
}

function suggestImprovements(files) {
  const suggestions = [];
  const hasSource = files.some((file) => classifyPath(file.path) === "source");
  const hasTests = files.some((file) => classifyPath(file.path) === "tests");
  const hasDocs = files.some((file) => classifyPath(file.path) === "documentation");

  if (hasSource && !hasTests) {
    suggestions.push("Add or update focused tests for the modified behavior before merging.");
  }

  if (hasSource && !hasDocs) {
    suggestions.push("Consider documenting any user-facing behavior, command, or configuration changes.");
  }

  if (files.some((file) => file.additions + file.deletions > 250)) {
    suggestions.push("Split very large files or broad changes into smaller reviewable units when practical.");
  }

  if (files.some((file) => classifyPath(file.path) === "automation")) {
    suggestions.push("Run the workflow in a safe test PR or with workflow_dispatch to validate permissions and output.");
  }

  if (!suggestions.length) {
    suggestions.push("Run the repository's standard test and lint commands and attach the results to the PR.");
  }

  return suggestions;
}

function confidence(files) {
  const totalChanged = files.reduce((sum, file) => sum + file.additions + file.deletions, 0);

  if (!files.length || files.some((file) => file.binary) || totalChanged > 1200) return "Low";
  if (totalChanged > 400 || files.length > 12) return "Medium";
  return "High";
}

function renderReview(pr, files) {
  return [
    "## Claude PR Review",
    "",
    "### Summary of changes",
    summarize(files, pr),
    "",
    "### Identified risks",
    formatList(identifyRisks(files)),
    "",
    "### Improvement suggestions",
    formatList(suggestImprovements(files)),
    "",
    `### Confidence score: ${confidence(files)}`,
    "",
    "<!-- generated by claude-review -->",
  ].join("\n");
}

async function postComment(pr, body) {
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  if (!token) {
    throw new Error("--post requires GITHUB_TOKEN or GH_TOKEN.");
  }

  const url = `https://api.github.com/repos/${pr.owner}/${pr.repo}/issues/${pr.number}/comments`;
  await request(
    url,
    {
      method: "POST",
      headers: {
        "User-Agent": "claude-review-cli",
        Accept: "application/vnd.github+json",
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
      },
    },
    JSON.stringify({ body })
  );
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    process.stdout.write(HELP);
    return;
  }

  const pr = parsePullRequestUrl(args.pr);
  const diff = args.diffFile
    ? fs.readFileSync(args.diffFile, "utf8")
    : await fetchDiff(pr);

  const files = parseDiff(diff);
  const review = renderReview(pr, files);
  process.stdout.write(`${review}\n`);

  if (args.post) {
    await postComment(pr, review);
    process.stderr.write(`Posted review comment to ${args.pr}\n`);
  }
}

main().catch((error) => {
  process.stderr.write(`claude-review: ${error.message}\n`);
  process.exitCode = 1;
});
