#!/usr/bin/env node

import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const MAX_DIFF_CHARS = 180_000;

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    printHelp();
    return;
  }

  if (!args.pr) {
    throw new Error("missing required --pr https://github.com/owner/repo/pull/123");
  }

  const target = parsePrUrl(args.pr);
  const pr = await fetchPullRequest(target);
  const diff = await fetchDiff(pr.diff_url || buildDiffUrl(target));
  const diffForAnalysis = diff.slice(0, args.maxDiffChars);
  const analysis = analyzePullRequest({ pr, target, diff, diffForAnalysis });
  const markdown = renderMarkdown(analysis);

  if (args.out) {
    const outPath = path.resolve(args.out);
    await mkdir(path.dirname(outPath), { recursive: true });
    await writeFile(outPath, markdown, "utf8");
    console.error(`review written to ${outPath}`);
  } else {
    process.stdout.write(`${markdown}\n`);
  }
}

function parseArgs(argv) {
  const args = {
    help: false,
    pr: "",
    out: "",
    maxDiffChars: MAX_DIFF_CHARS,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else if (arg === "--pr") {
      args.pr = readValue(argv, (index += 1), "--pr");
    } else if (arg.startsWith("--pr=")) {
      args.pr = arg.slice("--pr=".length);
    } else if (arg === "--out") {
      args.out = readValue(argv, (index += 1), "--out");
    } else if (arg.startsWith("--out=")) {
      args.out = arg.slice("--out=".length);
    } else if (arg === "--max-diff-chars") {
      args.maxDiffChars = Number(readValue(argv, (index += 1), "--max-diff-chars"));
    } else if (arg.startsWith("--max-diff-chars=")) {
      args.maxDiffChars = Number(arg.slice("--max-diff-chars=".length));
    }
  }

  if (!Number.isInteger(args.maxDiffChars) || args.maxDiffChars < 1000) {
    throw new Error("--max-diff-chars must be an integer >= 1000");
  }

  return args;
}

function readValue(argv, index, flag) {
  const value = argv[index];
  if (!value || value.startsWith("--")) {
    throw new Error(`${flag} requires a value`);
  }
  return value;
}

function printHelp() {
  console.log(`claude-review

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --out review.md

Options:
  --pr <url>                 GitHub pull request URL
  --out <file>               Write Markdown review to a file instead of stdout
  --max-diff-chars <number>  Limit diff text used for analysis, default ${MAX_DIFF_CHARS}
  --help                     Show this message
`);
}

function parsePrUrl(input) {
  let url;
  try {
    url = new URL(input);
  } catch {
    throw new Error(`invalid PR URL: ${input}`);
  }

  if (url.hostname !== "github.com") {
    throw new Error("only github.com pull request URLs are supported");
  }

  const parts = url.pathname.split("/").filter(Boolean);
  if (parts.length < 4 || parts[2] !== "pull") {
    throw new Error("PR URL must look like https://github.com/owner/repo/pull/123");
  }

  const number = Number(parts[3]);
  if (!Number.isInteger(number) || number < 1) {
    throw new Error("PR number must be a positive integer");
  }

  return {
    owner: parts[0],
    repo: parts[1],
    number,
    url: `https://github.com/${parts[0]}/${parts[1]}/pull/${number}`,
  };
}

async function fetchPullRequest(target) {
  return fetchJson(`https://api.github.com/repos/${target.owner}/${target.repo}/pulls/${target.number}`);
}

function buildDiffUrl(target) {
  return `https://github.com/${target.owner}/${target.repo}/pull/${target.number}.diff`;
}

async function fetchJson(url) {
  const response = await fetchWithHeaders(url);
  if (!response.ok) {
    throw new Error(`GitHub API request failed (${response.status}): ${url}`);
  }
  return response.json();
}

async function fetchDiff(url) {
  const response = await fetchWithHeaders(url, {
    Accept: "application/vnd.github.v3.diff",
  });
  if (!response.ok) {
    throw new Error(`GitHub diff request failed (${response.status}): ${url}`);
  }
  return response.text();
}

function fetchWithHeaders(url, extraHeaders = {}) {
  const headers = {
    "User-Agent": "claude-review-agent",
    ...extraHeaders,
  };
  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }
  return fetch(url, { headers });
}

function analyzePullRequest({ pr, target, diff, diffForAnalysis }) {
  const files = parseFiles(diffForAnalysis);
  const stats = summarizeFiles(files);
  const signals = collectSignals({ pr, diff, diffForAnalysis, files, stats });
  const risks = buildRisks(signals);
  const suggestions = buildSuggestions(signals);
  const confidence = scoreConfidence({ pr, diff, diffForAnalysis, files, signals });

  return {
    title: pr.title || `PR #${target.number}`,
    prUrl: target.url,
    author: pr.user?.login || "unknown",
    base: pr.base?.ref || "unknown",
    head: pr.head?.ref || "unknown",
    changedFiles: Number(pr.changed_files ?? files.length),
    additions: Number(pr.additions ?? stats.additions),
    deletions: Number(pr.deletions ?? stats.deletions),
    files,
    stats,
    risks,
    suggestions,
    confidence,
    truncated: diff.length > diffForAnalysis.length,
  };
}

function parseFiles(diff) {
  const files = [];
  let current = null;

  for (const line of diff.split("\n")) {
    const fileMatch = line.match(/^diff --git a\/(.+) b\/(.+)$/);
    if (fileMatch) {
      current = {
        oldPath: fileMatch[1],
        path: fileMatch[2],
        additions: 0,
        deletions: 0,
        addedLines: [],
        deletedLines: [],
      };
      files.push(current);
      continue;
    }

    if (!current) continue;
    if (line.startsWith("+++") || line.startsWith("---")) continue;
    if (line.startsWith("+")) {
      current.additions += 1;
      current.addedLines.push(line.slice(1));
    } else if (line.startsWith("-")) {
      current.deletions += 1;
      current.deletedLines.push(line.slice(1));
    }
  }

  return files;
}

function summarizeFiles(files) {
  const additions = files.reduce((sum, file) => sum + file.additions, 0);
  const deletions = files.reduce((sum, file) => sum + file.deletions, 0);
  const extensions = new Map();

  for (const file of files) {
    const ext = extensionOf(file.path);
    extensions.set(ext, (extensions.get(ext) || 0) + 1);
  }

  return {
    additions,
    deletions,
    extensions,
    testFiles: files.filter((file) => isTestFile(file.path)),
    docsFiles: files.filter((file) => isDocsFile(file.path)),
    configFiles: files.filter((file) => isConfigFile(file.path)),
    dependencyFiles: files.filter((file) => isDependencyFile(file.path)),
    securityFiles: files.filter((file) => isSecurityRelevantPath(file.path)),
    deletedFiles: files.filter((file) => file.additions === 0 && file.deletions > 0),
  };
}

function collectSignals({ pr, diff, diffForAnalysis, files, stats }) {
  const allAddedText = files.flatMap((file) => file.addedLines).join("\n");
  const productionFiles = files.filter((file) => !isTestFile(file.path) && !isDocsFile(file.path));
  const riskyPatterns = findRiskyPatterns(allAddedText);
  const areas = describeAreas(files);

  return {
    areas,
    touchesTests: stats.testFiles.length > 0,
    touchesDocs: stats.docsFiles.length > 0,
    touchesDependencies: stats.dependencyFiles.length > 0,
    touchesSecurity: stats.securityFiles.length > 0 || riskyPatterns.security.length > 0,
    riskyPatterns,
    productionFiles,
    largeChange: files.length >= 15 || Number(pr.additions ?? stats.additions) + Number(pr.deletions ?? stats.deletions) >= 700,
    noTestsForProduction: productionFiles.length > 0 && stats.testFiles.length === 0,
    hasDeletes: stats.deletedFiles.length > 0,
    truncated: diff.length > diffForAnalysis.length,
  };
}

function buildRisks(signals) {
  const risks = [];

  if (signals.noTestsForProduction) {
    risks.push("Production files changed without obvious test files in the diff.");
  }
  if (signals.touchesDependencies) {
    risks.push("Dependency or lockfile changes can affect install reproducibility and transitive package behavior.");
  }
  if (signals.touchesSecurity) {
    risks.push("Security-sensitive code or patterns were touched; authentication, secrets, or command execution paths need extra review.");
  }
  if (signals.riskyPatterns.runtime.length > 0) {
    risks.push(`Runtime-sensitive patterns detected: ${signals.riskyPatterns.runtime.slice(0, 4).join(", ")}.`);
  }
  if (signals.largeChange) {
    risks.push("The diff is large enough that subtle regressions may be hidden across files or modules.");
  }
  if (signals.hasDeletes) {
    risks.push("The diff removes code or files, so callers depending on the removed behavior may break.");
  }
  if (signals.truncated) {
    risks.push("The diff was truncated for analysis, so confidence is limited for later hunks.");
  }

  if (risks.length === 0) {
    risks.push("No high-risk patterns were detected from the available diff.");
  }

  return risks;
}

function buildSuggestions(signals) {
  const suggestions = [];

  if (signals.noTestsForProduction) {
    suggestions.push("Add focused tests for the changed production path, or document why existing coverage is sufficient.");
  }
  if (signals.touchesDependencies) {
    suggestions.push("Confirm lockfile changes are intentional and run the package manager's audit or integrity check.");
  }
  if (signals.touchesSecurity) {
    suggestions.push("Review the changed security-sensitive paths manually and avoid logging tokens, credentials, or raw user input.");
  }
  if (signals.largeChange) {
    suggestions.push("Consider splitting the PR or adding a concise migration note so reviewers can verify behavior by area.");
  }
  if (signals.touchesDocs && !signals.touchesTests && signals.productionFiles.length === 0) {
    suggestions.push("For docs-only changes, verify links, examples, and command snippets against current project behavior.");
  }

  suggestions.push("Run the repository's normal CI or test command before merging.");

  return unique(suggestions);
}

function scoreConfidence({ pr, diff, diffForAnalysis, files, signals }) {
  if (!files.length || signals.truncated) return "Low";
  const totalLines = Number(pr.additions ?? 0) + Number(pr.deletions ?? 0);
  if (totalLines > 700 || files.length > 15 || diff.length > diffForAnalysis.length) return "Medium";
  if (signals.riskyPatterns.security.length > 0 || signals.riskyPatterns.runtime.length > 2) return "Medium";
  return "High";
}

function renderMarkdown(analysis) {
  return [
    "# Claude Review",
    "",
    `PR: ${analysis.prUrl}`,
    `Author: ${analysis.author}`,
    `Base: ${analysis.base} | Head: ${analysis.head}`,
    "",
    "## Summary of changes",
    "",
    buildSummary(analysis),
    "",
    "## Identified risks",
    "",
    ...analysis.risks.map((risk) => `- ${risk}`),
    "",
    "## Improvement suggestions",
    "",
    ...analysis.suggestions.map((suggestion) => `- ${suggestion}`),
    "",
    `## Confidence score: ${analysis.confidence}`,
    "",
    buildEvidenceLine(analysis),
  ].join("\n");
}

function buildSummary(analysis) {
  const areas = analysis.stats.extensions.size
    ? Array.from(analysis.stats.extensions.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([ext, count]) => `${count} ${ext} file${count === 1 ? "" : "s"}`)
        .join(", ")
    : "no parsed file extensions";
  const coverage = analysis.stats.testFiles.length
    ? `${analysis.stats.testFiles.length} test file${analysis.stats.testFiles.length === 1 ? "" : "s"} included`
    : "no obvious test files included";

  return [
    `This PR changes ${analysis.changedFiles} file${analysis.changedFiles === 1 ? "" : "s"} (${areas}) with +${analysis.additions}/-${analysis.deletions} lines.`,
    `The main review surface is ${analysis.stats.summary || describeAreaText(analysis.files)}, with ${coverage}.`,
    `The strongest signal in this review is ${analysis.risks[0].replace(/\.$/, "").toLowerCase()}.`,
  ].join(" ");
}

function buildEvidenceLine(analysis) {
  const suffix = analysis.truncated ? " Diff analysis was truncated by --max-diff-chars." : "";
  return `Evidence inspected: GitHub PR metadata and parsed diff for ${analysis.files.length} file${analysis.files.length === 1 ? "" : "s"}.${suffix}`;
}

function describeAreas(files) {
  const dirs = new Map();
  for (const file of files) {
    const dir = file.path.includes("/") ? file.path.split("/")[0] : "(root)";
    dirs.set(dir, (dirs.get(dir) || 0) + 1);
  }
  return dirs;
}

function describeAreaText(files) {
  const dirs = Array.from(describeAreas(files).entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([dir, count]) => `${dir} (${count})`);
  return dirs.length ? dirs.join(", ") : "the parsed diff";
}

function findRiskyPatterns(text) {
  const securityChecks = [
    ["secret", /\b(secret|password|token|private[_-]?key|api[_-]?key)\b/i],
    ["auth", /\b(auth|oauth|jwt|session|cookie)\b/i],
    ["sql", /\b(select|insert|update|delete)\b.+\b(from|where|into)\b/i],
  ];
  const runtimeChecks = [
    ["eval", /\beval\s*\(/i],
    ["child_process", /\b(child_process|exec\s*\(|spawn\s*\()/i],
    ["innerHTML", /\b(innerHTML|dangerouslySetInnerHTML)\b/i],
    ["filesystem delete", /\b(rm\s+-rf|unlinkSync|rmdirSync)\b/i],
    ["network listener", /\b(app\.listen|server\.listen|createServer)\b/i],
  ];

  return {
    security: securityChecks.filter(([, pattern]) => pattern.test(text)).map(([label]) => label),
    runtime: runtimeChecks.filter(([, pattern]) => pattern.test(text)).map(([label]) => label),
  };
}

function extensionOf(filePath) {
  const base = path.basename(filePath);
  if (base === "package.json" || base.endsWith(".lock")) return "dependency";
  if (!base.includes(".")) return "no-ext";
  return path.extname(base).slice(1) || "no-ext";
}

function isTestFile(filePath) {
  return /(^|\/)(__tests__|tests?|spec)\//i.test(filePath) || /\.(test|spec)\.[cm]?[jt]sx?$/i.test(filePath);
}

function isDocsFile(filePath) {
  return /(^|\/)(docs?|documentation)\//i.test(filePath) || /\.(md|mdx|rst|txt)$/i.test(filePath);
}

function isConfigFile(filePath) {
  return /(^|\/)(\.github|config)\//i.test(filePath) || /\.(ya?ml|toml|ini|json|config\.[cm]?[jt]s)$/i.test(filePath);
}

function isDependencyFile(filePath) {
  return /(^|\/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb?|package\.json|requirements\.txt|poetry\.lock|pyproject\.toml|go\.mod|go\.sum|Cargo\.toml|Cargo\.lock)$/i.test(filePath);
}

function isSecurityRelevantPath(filePath) {
  return /(auth|security|session|jwt|oauth|permission|acl|policy|secret|credential)/i.test(filePath);
}

function unique(items) {
  return Array.from(new Set(items));
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
