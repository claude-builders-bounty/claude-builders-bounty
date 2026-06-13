#!/usr/bin/env node

import { writeFile } from "node:fs/promises";

const VERSION = "0.1.0";
const DEFAULT_MAX_FILES = 80;
const DEFAULT_MAX_DIFF_LINES = 2500;
const USER_AGENT = "claude-code-pr-reviewer/0.1.0";

function usage() {
  return `claude-review ${VERSION}

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123 [options]

Options:
  --pr <url>               GitHub pull request URL to review.
  --format <markdown|json> Output format. Default: markdown.
  --output <path>          Write the review to a file instead of stdout.
  --max-files <number>     Maximum changed files to analyze. Default: ${DEFAULT_MAX_FILES}.
  --max-diff-lines <num>   Maximum patch lines to analyze. Default: ${DEFAULT_MAX_DIFF_LINES}.
  --help                   Show this help message.
  --version                Show the CLI version.

Environment:
  GITHUB_TOKEN             Optional token for higher rate limits and private repos.
`;
}

function parseArgs(argv) {
  const args = {
    format: "markdown",
    maxFiles: DEFAULT_MAX_FILES,
    maxDiffLines: DEFAULT_MAX_DIFF_LINES
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = argv[index + 1];

    if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else if (arg === "--version" || arg === "-v") {
      args.version = true;
    } else if (arg === "--pr") {
      args.pr = requireValue(arg, next);
      index += 1;
    } else if (arg === "--format") {
      args.format = requireValue(arg, next);
      index += 1;
    } else if (arg === "--output" || arg === "-o") {
      args.output = requireValue(arg, next);
      index += 1;
    } else if (arg === "--max-files") {
      args.maxFiles = parsePositiveInteger(arg, requireValue(arg, next));
      index += 1;
    } else if (arg === "--max-diff-lines") {
      args.maxDiffLines = parsePositiveInteger(arg, requireValue(arg, next));
      index += 1;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!["markdown", "json"].includes(args.format)) {
    throw new Error("--format must be either markdown or json");
  }

  return args;
}

function requireValue(flag, value) {
  if (!value || value.startsWith("--")) {
    throw new Error(`${flag} requires a value`);
  }
  return value;
}

function parsePositiveInteger(flag, value) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isInteger(parsed) || parsed < 1) {
    throw new Error(`${flag} must be a positive integer`);
  }
  return parsed;
}

function parsePullRequestUrl(value) {
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new Error(`Invalid PR URL: ${value}`);
  }

  if (url.hostname !== "github.com") {
    throw new Error("Only github.com pull request URLs are supported");
  }

  const parts = url.pathname.split("/").filter(Boolean);
  if (parts.length < 4 || parts[2] !== "pull") {
    throw new Error("Expected PR URL format: https://github.com/owner/repo/pull/123");
  }

  const number = Number.parseInt(parts[3], 10);
  if (!Number.isInteger(number) || number < 1) {
    throw new Error(`Invalid pull request number: ${parts[3]}`);
  }

  return {
    owner: parts[0],
    repo: parts[1],
    number,
    url: `https://github.com/${parts[0]}/${parts[1]}/pull/${number}`
  };
}

async function githubJson(path) {
  const headers = {
    Accept: "application/vnd.github+json",
    "User-Agent": USER_AGENT,
    "X-GitHub-Api-Version": "2022-11-28"
  };
  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }

  const response = await fetch(`https://api.github.com${path}`, { headers });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`GitHub API ${response.status} for ${path}: ${body.slice(0, 300)}`);
  }
  return response.json();
}

async function fetchAllPullRequestFiles(ref, maxFiles) {
  const files = [];
  for (let page = 1; files.length < maxFiles; page += 1) {
    const batch = await githubJson(
      `/repos/${ref.owner}/${ref.repo}/pulls/${ref.number}/files?per_page=100&page=${page}`
    );
    files.push(...batch.slice(0, Math.max(0, maxFiles - files.length)));
    if (batch.length < 100) break;
  }
  return files;
}

function getPatchLines(files, maxDiffLines) {
  const lines = [];
  const addedEntries = [];
  const removedEntries = [];
  let omittedFiles = 0;

  for (const file of files) {
    lines.push(`diff --git a/${file.filename} b/${file.filename}`);
    if (!file.patch) {
      omittedFiles += 1;
      lines.push(`@@ ${file.status} file patch unavailable from GitHub API @@`);
      continue;
    }

    for (const line of file.patch.split("\n")) {
      if (lines.length >= maxDiffLines) {
        return { lines, addedEntries, removedEntries, truncated: true, omittedFiles };
      }
      lines.push(line);
      if (line.startsWith("+") && !line.startsWith("+++")) {
        addedEntries.push({ filename: file.filename, line });
      } else if (line.startsWith("-") && !line.startsWith("---")) {
        removedEntries.push({ filename: file.filename, line });
      }
    }
  }

  return { lines, addedEntries, removedEntries, truncated: false, omittedFiles };
}

function extensionOf(filename) {
  const basename = filename.split("/").pop() || filename;
  const dot = basename.lastIndexOf(".");
  if (dot <= 0) return "no-extension";
  return basename.slice(dot + 1).toLowerCase();
}

function uniqueSorted(values) {
  return [...new Set(values)].sort((a, b) => a.localeCompare(b));
}

function plural(count, singular, pluralValue = `${singular}s`) {
  return count === 1 ? singular : pluralValue;
}

function hasCodeChange(files) {
  const docExtensions = new Set(["md", "mdx", "txt", "rst"]);
  return files.some((file) => !docExtensions.has(extensionOf(file.filename)));
}

function hasTestChange(files) {
  return files.some((file) => {
    const lower = file.filename.toLowerCase();
    return (
      lower.includes("test") ||
      lower.includes("spec") ||
      lower.includes("__tests__") ||
      lower.includes("/tests/") ||
      lower.endsWith(".snap")
    );
  });
}

function hasDocumentationChange(files) {
  return files.some((file) => {
    const lower = file.filename.toLowerCase();
    return lower.endsWith(".md") || lower.includes("docs/") || lower.includes("readme");
  });
}

function changedArea(files) {
  const roots = uniqueSorted(
    files.map((file) => {
      const parts = file.filename.split("/");
      return parts.length > 1 ? parts[0] : "(root)";
    })
  );
  return roots.slice(0, 6).join(", ") + (roots.length > 6 ? ", ..." : "");
}

function addedLines(patchLines) {
  return patchLines.filter((line) => line.startsWith("+") && !line.startsWith("+++"));
}

function removedLines(patchLines) {
  return patchLines.filter((line) => line.startsWith("-") && !line.startsWith("---"));
}

function lineText(item) {
  return typeof item === "string" ? item : item.line;
}

function isTestFile(filename) {
  const lower = filename.toLowerCase();
  return (
    lower.includes("test") ||
    lower.includes("spec") ||
    lower.includes("__tests__") ||
    lower.includes("/tests/") ||
    lower.endsWith(".snap")
  );
}

function isDocumentationFile(filename) {
  const lower = filename.toLowerCase();
  return lower.endsWith(".md") || lower.endsWith(".mdx") || lower.includes("docs/") || lower.includes("readme");
}

function isSampleOutput(filename) {
  return filename.startsWith("sample-outputs/") || filename.startsWith("assets/");
}

function findMatches(lines, patterns) {
  const matches = [];
  for (const { label, regex } of patterns) {
    const hit = lines.find((item) => regex.test(lineText(item)));
    if (hit) {
      matches.push({ label, sample: lineText(hit).slice(0, 160) });
    }
  }
  return matches;
}

function analyze(ref, pr, files, patchInfo) {
  const totalAdditions = files.reduce((sum, file) => sum + (file.additions || 0), 0);
  const totalDeletions = files.reduce((sum, file) => sum + (file.deletions || 0), 0);
  const totalChanges = totalAdditions + totalDeletions;
  const testChanged = hasTestChange(files);
  const docsChanged = hasDocumentationChange(files);
  const codeChanged = hasCodeChange(files);
  const extensions = uniqueSorted(files.map((file) => extensionOf(file.filename))).slice(0, 8);
  const additions = patchInfo.addedEntries ?? addedLines(patchInfo.lines).map((line) => ({ filename: "unknown", line }));
  const removals = patchInfo.removedEntries ?? removedLines(patchInfo.lines).map((line) => ({ filename: "unknown", line }));
  const reviewableAdditions = additions.filter(
    (entry) => !isDocumentationFile(entry.filename) && !isTestFile(entry.filename) && !isSampleOutput(entry.filename)
  );
  const reviewableRemovals = removals.filter(
    (entry) => !isDocumentationFile(entry.filename) && !isTestFile(entry.filename) && !isSampleOutput(entry.filename)
  );

  const riskSignals = [];
  const suggestionSignals = [];

  if (files.length > 35 || totalChanges > 1200) {
    riskSignals.push(
      `Large review surface: ${files.length} ${plural(files.length, "file")} and ${totalChanges} changed lines.`
    );
    suggestionSignals.push("Split unrelated changes or add a reviewer map so high-risk files receive focused review.");
  }

  if (codeChanged && !testChanged) {
    riskSignals.push("Code changed without an obvious test or spec file update.");
    suggestionSignals.push("Add or update focused tests for the changed behavior before merge.");
  }

  if (!docsChanged && files.some((file) => ["package.json", "pyproject.toml", "README.md"].includes(file.filename))) {
    suggestionSignals.push("Document any new setup, commands, or behavior exposed by this change.");
  }

  const secretMatches = findMatches(reviewableAdditions, [
    {
      label: "possible credential or token literal",
      regex: /(api[_-]?key|secret|private[_-]?key|password|token)\s*[:=]\s*["']?[A-Za-z0-9_./+=-]{16,}["']?/i
    },
    { label: "private key marker", regex: /BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY/i }
  ]);
  for (const match of secretMatches) {
    riskSignals.push(`Security-sensitive addition detected: ${match.label}.`);
    suggestionSignals.push("Move secrets to repository or deployment secrets and rotate anything committed by mistake.");
  }

  const executionMatches = findMatches(reviewableAdditions, [
    { label: "dynamic JavaScript execution", regex: /\beval\s*\(|new Function\s*\(/ },
    { label: "shell execution", regex: /(child_process|execSync|spawnSync|subprocess\.|os\.system|shell=True)/ },
    { label: "raw SQL construction", regex: /(query|execute|raw)\s*\([^)]*(SELECT|UPDATE|DELETE|INSERT)[^)]*(\$\{| \+ |\.format\()/i }
  ]);
  for (const match of executionMatches) {
    riskSignals.push(`Runtime risk detected: ${match.label}.`);
    suggestionSignals.push("Prefer parameterized APIs and constrained execution paths around user-controlled input.");
  }

  if (reviewableAdditions.some((entry) => /http:\/\//i.test(entry.line))) {
    riskSignals.push("Plain HTTP URL added in the diff.");
    suggestionSignals.push("Use HTTPS unless the endpoint is explicitly local or intentionally insecure.");
  }

  if (reviewableAdditions.some((entry) => /(console\.log|print\(|debugger;|pdb\.set_trace)/.test(entry.line))) {
    riskSignals.push("Debug logging or breakpoint-like code appears in added lines.");
    suggestionSignals.push("Remove debug-only statements or gate them behind structured logging levels.");
  }

  if (reviewableRemovals.some((entry) => /(assert|expect\(|should\(|pytest|unittest)/i.test(entry.line))) {
    riskSignals.push("Assertions or test expectations appear to be removed.");
    suggestionSignals.push("Explain why removed assertions are obsolete or replace them with equivalent coverage.");
  }

  const workflowTouched = files.some((file) => file.filename.startsWith(".github/workflows/"));
  if (workflowTouched) {
    riskSignals.push("GitHub Actions workflow files changed; permissions and trigger context should be reviewed.");
    suggestionSignals.push("Keep workflow permissions minimal and avoid running untrusted PR code with write tokens.");
  }

  const dependencyFiles = new Set(["package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "pyproject.toml", "requirements.txt"]);
  const dependencyTouched = files.some((file) => dependencyFiles.has(file.filename));
  if (dependencyTouched) {
    suggestionSignals.push("Confirm dependency changes are pinned and lockfiles are consistent.");
  }

  const patchCoverage = files.length === 0 ? 1 : files.filter((file) => Boolean(file.patch)).length / files.length;
  if (patchInfo.truncated || patchCoverage < 0.75) {
    riskSignals.push("Analysis is based on a partial diff because GitHub omitted or truncated some patch content.");
    suggestionSignals.push("Run a full local diff review before merging.");
  }

  const risks = riskSignals.length > 0 ? uniqueSorted(riskSignals) : ["No high-signal risk pattern was detected in the available diff."];
  const suggestions = suggestionSignals.length > 0 ? uniqueSorted(suggestionSignals) : ["Proceed after the normal maintainer review and CI checks pass."];

  let confidence = "High";
  const confidenceReasons = [];
  if (patchCoverage < 0.75 || patchInfo.truncated || files.length > 50 || totalChanges > 1800) {
    confidence = "Low";
    confidenceReasons.push("diff coverage or size limits reduce automated review reliability");
  } else if (patchCoverage < 0.95 || files.length > 20 || totalChanges > 700) {
    confidence = "Medium";
    confidenceReasons.push("moderate review surface");
  } else {
    confidenceReasons.push("small enough diff with usable patch coverage");
  }

  if (riskSignals.length >= 2 && confidence === "High") {
    confidence = "Medium";
    confidenceReasons.push("multiple risk signals require human confirmation");
  }

  return {
    pr: {
      owner: ref.owner,
      repo: ref.repo,
      number: ref.number,
      url: ref.url,
      title: pr.title,
      author: pr.user?.login || "unknown",
      state: pr.state,
      base: pr.base?.ref || "unknown",
      head: pr.head?.ref || "unknown"
    },
    summary: [
      `This PR changes ${files.length} ${plural(files.length, "file")} with ${totalAdditions} additions and ${totalDeletions} deletions.`,
      `The main touched area is ${changedArea(files) || "not available"}, with file types: ${extensions.join(", ") || "not available"}.`,
      testChanged
        ? "The diff includes test/spec coverage changes."
        : codeChanged
          ? "No obvious test/spec file changed alongside code changes."
          : "The change appears to be documentation or configuration focused."
    ],
    risks,
    suggestions,
    confidence,
    confidenceReason: confidenceReasons.join("; "),
    metadata: {
      filesAnalyzed: files.length,
      additions: totalAdditions,
      deletions: totalDeletions,
      patchLinesAnalyzed: patchInfo.lines.length,
      patchCoverage: Number(patchCoverage.toFixed(2)),
      truncated: patchInfo.truncated,
      omittedPatchFiles: patchInfo.omittedFiles,
      costMode: "zero-cost local heuristic analysis; no paid LLM API call"
    }
  };
}

function toMarkdown(review) {
  const riskText = review.risks.map((item) => `- ${item}`).join("\n");
  const suggestionText = review.suggestions.map((item) => `- ${item}`).join("\n");
  const summaryText = review.summary.map((item) => `- ${item}`).join("\n");

  return `## Claude Code PR Review

**PR:** [${review.pr.owner}/${review.pr.repo}#${review.pr.number}](${review.pr.url})  
**Title:** ${review.pr.title}  
**Author:** @${review.pr.author}  
**Branches:** \`${review.pr.head}\` -> \`${review.pr.base}\`

### Summary of Changes
${summaryText}

### Identified Risks
${riskText}

### Improvement Suggestions
${suggestionText}

### Confidence Score
**${review.confidence}** - ${review.confidenceReason}.

### Review Metadata
- Files analyzed: ${review.metadata.filesAnalyzed}
- Additions / deletions: +${review.metadata.additions} / -${review.metadata.deletions}
- Patch lines analyzed: ${review.metadata.patchLinesAnalyzed}
- Patch coverage: ${Math.round(review.metadata.patchCoverage * 100)}%
- Truncated: ${review.metadata.truncated ? "yes" : "no"}
- Cost mode: ${review.metadata.costMode}
`;
}

async function run(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);

  if (args.help) {
    return usage();
  }
  if (args.version) {
    return VERSION;
  }
  if (!args.pr) {
    throw new Error("--pr is required");
  }

  const ref = parsePullRequestUrl(args.pr);
  const pr = await githubJson(`/repos/${ref.owner}/${ref.repo}/pulls/${ref.number}`);
  const files = await fetchAllPullRequestFiles(ref, args.maxFiles);
  const patchInfo = getPatchLines(files, args.maxDiffLines);
  const review = analyze(ref, pr, files, patchInfo);
  const output = args.format === "json" ? `${JSON.stringify(review, null, 2)}\n` : toMarkdown(review);

  if (args.output) {
    await writeFile(args.output, output, "utf8");
    return `Review written to ${args.output}`;
  }
  return output;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  run()
    .then((output) => {
      if (output) {
        process.stdout.write(output.endsWith("\n") ? output : `${output}\n`);
      }
    })
    .catch((error) => {
      process.stderr.write(`claude-review: ${error.message}\n`);
      process.stderr.write("Run `claude-review --help` for usage.\n");
      process.exitCode = 1;
    });
}

export {
  analyze,
  getPatchLines,
  parseArgs,
  parsePullRequestUrl,
  run,
  toMarkdown
};
