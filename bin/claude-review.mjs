#!/usr/bin/env node
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { request } from "node:https";
import { dirname } from "node:path";
import { pathToFileURL } from "node:url";

const USER_AGENT = "claude-pr-reviewer-agent/1.0";

function usage() {
  return `Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --fixture test/fixtures/pr.json

Options:
  --pr <url>          GitHub pull request URL to review.
  --fixture <path>    Local JSON fixture with pr and files fields.
  --output <path>     Write review to a file instead of stdout.
  --format <name>     markdown or json. Default: markdown.
  --max-files <n>     Limit analyzed files for very large PRs.
  --help              Show this help text.`;
}

function parseArgs(argv) {
  const args = { format: "markdown" };
  const valueFlags = new Set(["--pr", "--fixture", "--output", "--format", "--max-files"]);

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];

    if (arg === "--help" || arg === "-h") {
      args.help = true;
      continue;
    }

    if (valueFlags.has(arg)) {
      const value = argv[i + 1];
      if (!value || value.startsWith("--")) {
        throw new Error(`${arg} requires a value`);
      }
      const key = arg.slice(2);
      if (key === "max-files" && !/^[0-9]+$/.test(value)) {
        throw new Error("--max-files must be a positive integer");
      }
      args[key] = key === "max-files" ? Number(value) : value;
      i += 1;
      continue;
    }

    throw new Error(`Unknown argument: ${arg}`);
  }

  if (!args.help && !args.pr && !args.fixture) {
    throw new Error("Provide --pr or --fixture");
  }

  if (args.pr && args.fixture) {
    throw new Error("Use either --pr or --fixture, not both");
  }

  if (!["markdown", "json"].includes(args.format)) {
    throw new Error("--format must be markdown or json");
  }

  if (args["max-files"] !== undefined && (!Number.isSafeInteger(args["max-files"]) || args["max-files"] < 1)) {
    throw new Error("--max-files must be a positive integer");
  }

  return args;
}

function parsePullRequestUrl(url) {
  const match = String(url).match(/^https:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)(?:[/?#].*)?$/);
  if (!match) {
    throw new Error(`Not a GitHub pull request URL: ${url}`);
  }
  return {
    owner: match[1],
    repo: match[2],
    number: Number(match[3]),
    url: `https://github.com/${match[1]}/${match[2]}/pull/${match[3]}`,
  };
}

function githubGet(path, token) {
  return new Promise((resolve, reject) => {
    const headers = {
      Accept: "application/vnd.github+json",
      "User-Agent": USER_AGENT,
      "X-GitHub-Api-Version": "2022-11-28",
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const req = request(
      {
        hostname: "api.github.com",
        path,
        method: "GET",
        headers,
      },
      (res) => {
        let body = "";
        res.setEncoding("utf8");
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          if (res.statusCode < 200 || res.statusCode >= 300) {
            reject(new Error(`GitHub API ${res.statusCode}: ${body.slice(0, 300)}`));
            return;
          }
          try {
            resolve(JSON.parse(body));
          } catch (error) {
            reject(new Error(`Invalid GitHub JSON response: ${error.message}`));
          }
        });
      }
    );

    req.on("error", reject);
    req.end();
  });
}

async function fetchPullRequest(prUrl, token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN) {
  const ref = parsePullRequestUrl(prUrl);
  const pr = await githubGet(`/repos/${ref.owner}/${ref.repo}/pulls/${ref.number}`, token);
  const files = [];

  for (let page = 1; page <= 10; page += 1) {
    const pageFiles = await githubGet(
      `/repos/${ref.owner}/${ref.repo}/pulls/${ref.number}/files?per_page=100&page=${page}`,
      token
    );
    files.push(...pageFiles);
    if (pageFiles.length < 100) break;
  }

  const reportedChangedFiles = Number(pr.changed_files || 0);
  if (reportedChangedFiles > files.length) {
    pr.truncatedFiles = reportedChangedFiles - files.length;
  }

  return { ref, pr, files };
}

export function applyFileLimit(input, maxFiles) {
  if (!maxFiles || input.files.length <= maxFiles) {
    return input;
  }

  const alreadyTruncated = Number(input.pr.truncatedFiles || 0);
  return {
    ...input,
    pr: {
      ...input.pr,
      truncatedFiles: alreadyTruncated + input.files.length - maxFiles,
    },
    files: input.files.slice(0, maxFiles),
  };
}

async function loadFixture(path) {
  const raw = await readFile(path, "utf8");
  const parsed = JSON.parse(raw);
  if (!parsed.pr || !Array.isArray(parsed.files)) {
    throw new Error("Fixture must contain { pr, files }");
  }
  return {
    ref: parsed.ref || {
      owner: "fixture",
      repo: "fixture",
      number: parsed.pr.number || 0,
      url: parsed.pr.html_url || "fixture://pull-request",
    },
    pr: parsed.pr,
    files: parsed.files,
  };
}

function isTestFile(fileName) {
  return /(^|\/)(__tests__|tests?|specs?)\//.test(fileName)
    || /\.(test|spec)\.[cm]?[jt]sx?$/.test(fileName)
    || /(^|\/)test_.*\.py$/.test(fileName)
    || /(^|\/)test[-_].*\.(sh|bash|zsh|ps1)$/.test(fileName);
}

function isCodeFile(fileName, patch = "") {
  return /\.(js|jsx|ts|tsx|mjs|cjs|py|go|rs|java|rb|php|cs|sql|sh|bash|zsh|ps1)$/.test(fileName)
    || /^\+#!\s*\/usr\/bin\/(?:env\s+)?(?:node|python\d*|ruby|php|bash|sh|zsh)\b/m.test(patch);
}

function isDocsFile(fileName) {
  return /\.(md|mdx|txt|rst)$/.test(fileName) || /(^|\/)docs?\//.test(fileName);
}

function isWorkflowFile(fileName) {
  return /^\.github\/workflows\/.+\.ya?ml$/.test(fileName) || /(^|\/)action\.ya?ml$/.test(fileName);
}

function isMigrationFile(fileName) {
  return /(^|\/)(migrations?|db|database)\//.test(fileName) || /migration/i.test(fileName);
}

function isDependencyFile(fileName) {
  return /(^|\/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|requirements\.txt|poetry\.lock|Cargo\.lock|go\.sum)$/.test(fileName)
    || /(^|\/)(package\.json|pyproject\.toml|Cargo\.toml|go\.mod)$/.test(fileName);
}

function patchContains(files, pattern) {
  return files.some((file) => pattern.test(`${file.patch || ""}\n${file.filename || ""}`));
}

function unique(values) {
  return [...new Set(values)];
}

function describeFileMix(files) {
  const labels = [];
  if (files.some((file) => isCodeFile(file.filename, file.patch))) labels.push("application code");
  if (files.some((file) => isTestFile(file.filename))) labels.push("tests");
  if (files.some((file) => isDocsFile(file.filename))) labels.push("documentation");
  if (files.some((file) => isWorkflowFile(file.filename))) labels.push("automation");
  if (files.some((file) => isMigrationFile(file.filename))) labels.push("database migrations");
  return labels.length ? labels.join(", ") : "repository files";
}

export function analyzePullRequest({ ref, pr, files }) {
  const truncatedFiles = Number(pr.truncatedFiles || 0);
  const additions = files.reduce((sum, file) => sum + (file.additions || 0), 0);
  const deletions = files.reduce((sum, file) => sum + (file.deletions || 0), 0);
  const changedFiles = files.length;
  const missingPatches = files.filter((file) =>
    (Number(file.additions || 0) + Number(file.deletions || 0) > 0)
    && (typeof file.patch !== "string" || file.patch.trim().length === 0)
  ).length;
  const codeFiles = files.filter((file) => isCodeFile(file.filename, file.patch));
  const testFiles = files.filter((file) => isTestFile(file.filename));
  const workflowFiles = files.filter((file) => isWorkflowFile(file.filename));
  const migrationFiles = files.filter((file) => isMigrationFile(file.filename));
  const dependencyFiles = files.filter((file) => isDependencyFile(file.filename));
  const risks = [];
  const suggestions = [];

  if (codeFiles.length > 0 && testFiles.length === 0) {
    risks.push("Code changed without matching test files in the diff.");
    suggestions.push("Add focused tests or explain why existing coverage already exercises the changed behavior.");
  }

  if (changedFiles > 20 || additions + deletions > 800) {
    risks.push(`Large review surface: ${changedFiles} analyzed files and ${additions + deletions} changed lines.`);
    suggestions.push("Split the change or add a reviewer guide that maps files to behavior changes.");
  }

  if (truncatedFiles > 0) {
    risks.push(`${truncatedFiles} changed file${truncatedFiles === 1 ? " was" : "s were"} omitted from this review; API coverage or a local file limit may be responsible.`);
    suggestions.push("Check API file coverage and any --max-files limit; review the omitted files manually before merge.");
  }

  if (missingPatches > 0) {
    risks.push(`Patch text is unavailable for ${missingPatches} file${missingPatches === 1 ? "" : "s"} with reported changed lines; metadata alone cannot establish their behavior.`);
    suggestions.push("Inspect the full diff for files without patch text before relying on this review.");
  }

  if (migrationFiles.length > 0) {
    risks.push("Database or migration files changed, so rollout and rollback behavior need explicit review.");
    suggestions.push("Document migration order, data backfill expectations, and rollback safety before merge.");
  }

  if (workflowFiles.length > 0) {
    risks.push("Automation or workflow files changed, which can affect CI permissions or secret exposure.");
    suggestions.push("Verify workflow permissions are least-privilege and secrets are not echoed in logs.");
  }

  if (dependencyFiles.length > 0) {
    risks.push("Dependency or lock files changed, which may introduce supply-chain or runtime drift.");
    suggestions.push("Call out why each dependency change is required and confirm lockfile consistency.");
  }

  if (patchContains(files, /\b(eval|exec|child_process|subprocess|shell_exec)\b/)) {
    risks.push("The diff references dynamic execution or shell execution primitives.");
    suggestions.push("Constrain inputs, document trust boundaries, and add tests for command injection paths.");
  }

  if (patchContains(files, /\b(TODO|FIXME|XXX)\b/)) {
    risks.push("The diff contains TODO/FIXME markers that may represent unfinished work.");
    suggestions.push("Resolve the marker or convert it into a tracked follow-up with clear non-blocking rationale.");
  }

  if (patchContains(files, /\b(secret|token|password|private[_-]?key|api[_-]?key)\b/i)) {
    risks.push("The diff mentions credential-like terms and should be checked for accidental secret handling.");
    suggestions.push("Confirm examples use placeholders only and that no secret value is committed.");
  }

  if (risks.length === 0) {
    risks.push("No high-risk pattern was detected from the diff metadata and patch text.");
  }

  const defaultSuggestion = "Keep the PR description aligned with the final diff and include manual verification evidence.";
  if (suggestions.length === 0) {
    suggestions.push(defaultSuggestion);
  } else if (!suggestions.includes(defaultSuggestion)) {
    suggestions.push(defaultSuggestion);
  }

  const uniqueRisks = unique(risks);
  const uniqueSuggestions = unique(suggestions);
  const riskScore = uniqueRisks.filter((risk) => !risk.startsWith("No high-risk")).length;
  const confidence = truncatedFiles > 0 || missingPatches > 0 || riskScore >= 4 || changedFiles > 30
    ? "Low"
    : riskScore >= 2 || testFiles.length === 0
      ? "Medium"
      : "High";

  const title = pr.title || `PR #${ref.number}`;
  const summary = [
    `${title} changes ${changedFiles} file${changedFiles === 1 ? "" : "s"} with ${additions} additions and ${deletions} deletions across ${describeFileMix(files)}.`,
    testFiles.length > 0
      ? `The diff includes ${testFiles.length} test-related file${testFiles.length === 1 ? "" : "s"}, which improves review confidence.`
      : "No test file was detected in the changed file list, so behavior coverage should be verified explicitly.",
  ];
  if (truncatedFiles > 0) {
    summary.push(`${truncatedFiles} additional changed file${truncatedFiles === 1 ? " was" : "s were"} not analyzed; file coverage is incomplete.`);
  }

  return {
    pullRequest: {
      url: ref.url || pr.html_url,
      owner: ref.owner,
      repo: ref.repo,
      number: ref.number || pr.number,
      title,
      author: pr.user?.login || pr.author || "unknown",
    },
    stats: {
      changedFiles,
      missingPatches,
      additions,
      deletions,
      codeFiles: codeFiles.length,
      testFiles: testFiles.length,
      workflowFiles: workflowFiles.length,
      migrationFiles: migrationFiles.length,
      dependencyFiles: dependencyFiles.length,
    },
    summary,
    risks: uniqueRisks,
    suggestions: uniqueSuggestions,
    confidence,
  };
}

export function formatMarkdown(review) {
  const lines = [];
  lines.push("# Claude PR Review");
  lines.push("");
  lines.push(`**PR:** ${review.pullRequest.url}`);
  lines.push(`**Author:** @${review.pullRequest.author}`);
  lines.push(`**Files:** ${review.stats.changedFiles} changed, +${review.stats.additions} / -${review.stats.deletions}`);
  lines.push("");
  lines.push("## Summary");
  lines.push("");
  for (const sentence of review.summary) {
    lines.push(sentence);
  }
  lines.push("");
  lines.push("## Identified Risks");
  lines.push("");
  for (const risk of review.risks) {
    lines.push(`- ${risk}`);
  }
  lines.push("");
  lines.push("## Improvement Suggestions");
  lines.push("");
  for (const suggestion of review.suggestions) {
    lines.push(`- ${suggestion}`);
  }
  lines.push("");
  lines.push(`## Confidence: ${review.confidence}`);
  lines.push("");
  lines.push("Confidence is based on diff size, affected file types, test coverage signals, and security-sensitive patterns.");
  return `${lines.join("\n")}\n`;
}

async function main() {
  try {
    const args = parseArgs(process.argv.slice(2));
    if (args.help) {
      process.stdout.write(`${usage()}\n`);
      return;
    }

    const input = args.fixture
      ? await loadFixture(args.fixture)
      : await fetchPullRequest(args.pr);

    const limitedInput = applyFileLimit(input, args["max-files"]);

    const review = analyzePullRequest(limitedInput);
    const output = args.format === "json"
      ? `${JSON.stringify(review, null, 2)}\n`
      : formatMarkdown(review);

    if (args.output) {
      await mkdir(dirname(args.output), { recursive: true });
      await writeFile(args.output, output, "utf8");
    } else {
      process.stdout.write(output);
    }
  } catch (error) {
    process.stderr.write(`claude-review: ${error.message}\n\n${usage()}\n`);
    process.exitCode = 1;
  }
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}

export { parseArgs, parsePullRequestUrl };
