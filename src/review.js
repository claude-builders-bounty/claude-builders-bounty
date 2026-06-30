const fs = require("node:fs/promises");

function parsePullRequestUrl(value) {
  const match = String(value || "").match(
    /^https:\/\/github\.com\/([^/\s]+)\/([^/\s]+)\/pull\/(\d+)(?:[?#].*)?$/
  );

  if (!match) {
    throw new Error(
      "Expected --pr to be a GitHub pull request URL, for example https://github.com/owner/repo/pull/123"
    );
  }

  const [, owner, repo, number] = match;
  return {
    owner,
    repo,
    number,
    diffUrl: `https://github.com/${owner}/${repo}/pull/${number}.diff`,
    url: `https://github.com/${owner}/${repo}/pull/${number}`
  };
}

function parseArgs(argv) {
  const args = {
    diffFile: "",
    help: false,
    pr: ""
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === "--pr") {
      args.pr = argv[index + 1] || "";
      index += 1;
    } else if (arg === "--diff-file") {
      args.diffFile = argv[index + 1] || "";
      index += 1;
    } else if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return args;
}

async function fetchPullRequestDiff(prUrl, fetchImpl = globalThis.fetch) {
  if (typeof fetchImpl !== "function") {
    throw new Error("This command requires Node.js 18+ with fetch support.");
  }

  const pr = parsePullRequestUrl(prUrl);
  const response = await fetchImpl(pr.diffUrl, {
    headers: {
      "user-agent": "claude-review"
    }
  });

  if (!response.ok) {
    throw new Error(`Unable to fetch PR diff: ${response.status} ${response.statusText}`);
  }

  return {
    diff: await response.text(),
    pr
  };
}

function summarizeFiles(files) {
  const buckets = {
    config: files.filter((file) =>
      /(^|\/)(package|tsconfig|eslint|prettier|vite|next|webpack|rollup|pnpm|yarn|npm|lock)/i.test(file)
    ),
    docs: files.filter((file) => /\.(md|mdx|txt)$/i.test(file)),
    tests: files.filter((file) => isTestFile(file)),
    workflows: files.filter((file) => /^\.github\/workflows\//.test(file))
  };

  const named = Object.entries(buckets)
    .filter(([, matches]) => matches.length > 0)
    .map(([name]) => name);

  return named.length > 0 ? named.join(", ") : "application code";
}

function analyzeDiff(diff, pr = {}) {
  const lines = String(diff || "").split(/\r?\n/);
  const files = [];
  let additions = 0;
  let binaryFiles = 0;
  let deletedFiles = 0;
  let deletions = 0;

  for (const line of lines) {
    const fileMatch = line.match(/^diff --git a\/(.+?) b\/(.+)$/);
    if (fileMatch) {
      files.push(fileMatch[2]);
      continue;
    }

    if (line.startsWith("deleted file mode")) {
      deletedFiles += 1;
    } else if (line.startsWith("Binary files ")) {
      binaryFiles += 1;
    } else if (line.startsWith("+") && !line.startsWith("+++")) {
      additions += 1;
    } else if (line.startsWith("-") && !line.startsWith("---")) {
      deletions += 1;
    }
  }

  const uniqueFiles = [...new Set(files)];
  const touchedTests = uniqueFiles.some((file) => isTestFile(file));
  const touchedWorkflow = uniqueFiles.some((file) => /^\.github\/workflows\//.test(file));
  const touchedDependencies = uniqueFiles.some((file) =>
    /(^|\/)(package(-lock)?\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb)$/.test(file)
  );
  const touchedRuntime = uniqueFiles.some((file) =>
    /\.(js|jsx|ts|tsx|mjs|cjs|py|go|rs|rb|php|java|cs)$/i.test(file)
  );

  const risks = [];
  if (!touchedTests && touchedRuntime) {
    risks.push("No test files were detected in the diff, so behavior may be under-covered.");
  }
  if (touchedDependencies) {
    risks.push("Dependency or lockfile changes can affect installation and CI reproducibility.");
  }
  if (touchedWorkflow) {
    risks.push("Workflow changes can alter CI permissions, triggers, or required checks.");
  }
  if (deletedFiles > 0) {
    risks.push(`${deletedFiles} deleted file(s) may remove behavior that callers still rely on.`);
  }
  if (binaryFiles > 0) {
    risks.push(`${binaryFiles} binary file(s) cannot be reviewed from textual diff context.`);
  }
  if (uniqueFiles.length > 12 || additions + deletions > 500) {
    risks.push("The diff is broad enough that reviewers should inspect affected flows individually.");
  }
  if (risks.length === 0) {
    risks.push("No high-risk patterns were detected from the diff alone.");
  }

  const suggestions = [];
  if (!touchedTests && touchedRuntime) {
    suggestions.push("Add or point to targeted regression tests for the changed runtime behavior.");
  }
  if (touchedDependencies) {
    suggestions.push("Confirm the lockfile was regenerated with the repository's standard package manager.");
  }
  if (touchedWorkflow) {
    suggestions.push("Confirm the workflow uses least-privilege permissions and runs on the intended events.");
  }
  suggestions.push("Run the repository's formatter, lint, and test commands before merge.");
  suggestions.push("Ask a maintainer to verify any product behavior that is not visible in the diff.");

  let confidence = "Medium";
  if (String(diff).trim().length === 0 || binaryFiles > 0) {
    confidence = "Low";
  } else if (touchedTests && uniqueFiles.length <= 8 && additions + deletions <= 300) {
    confidence = "High";
  }

  const fileSummary = summarizeFiles(uniqueFiles);
  const summary = [
    `This PR changes ${uniqueFiles.length} file(s) with ${additions} addition(s) and ${deletions} deletion(s).`,
    `The main touched area appears to be ${fileSummary}.`,
    touchedTests
      ? "The diff includes test coverage, which improves review confidence."
      : "No dedicated test files were detected in the diff."
  ];

  return {
    confidence,
    files: uniqueFiles,
    pr,
    risks,
    stats: {
      additions,
      deletions,
      files: uniqueFiles.length
    },
    suggestions,
    summary
  };
}

function isTestFile(file) {
  return /(^|\/)(__tests__|test|tests|spec)(\/|\.|-)|(^|\/)test_[^/]+\.py$|(^|\/)[^/]+_test\.py$|\.(test|spec)\.[cm]?[jt]sx?$/i.test(
    file
  );
}

function renderMarkdownReview(review) {
  const prLine = review.pr.url ? ` for ${review.pr.url}` : "";
  const changedFiles = review.files.slice(0, 12).map((file) => `- \`${file}\``);

  if (review.files.length > 12) {
    changedFiles.push(`- ...and ${review.files.length - 12} more file(s)`);
  }

  return [
    `## Claude PR Review${prLine}`,
    "",
    "### Summary of changes",
    ...review.summary.map((sentence) => `- ${sentence}`),
    "",
    "### Identified risks",
    ...review.risks.map((risk) => `- ${risk}`),
    "",
    "### Improvement suggestions",
    ...review.suggestions.map((suggestion) => `- ${suggestion}`),
    "",
    "### Changed files",
    ...(changedFiles.length > 0 ? changedFiles : ["- No changed files were detected."]),
    "",
    `### Confidence score: ${review.confidence}`,
    "",
    "<!-- Generated by claude-review -->"
  ].join("\n");
}

function usage() {
  return [
    "Usage:",
    "  claude-review --pr https://github.com/owner/repo/pull/123",
    "  claude-review --pr https://github.com/owner/repo/pull/123 --diff-file ./pr.diff",
    "",
    "Options:",
    "  --pr         GitHub pull request URL used in the report header and diff lookup.",
    "  --diff-file  Optional local diff file for offline or fixture-based review.",
    "  --help       Show this help text."
  ].join("\n");
}

async function runCli(argv = process.argv.slice(2), output = process.stdout) {
  const args = parseArgs(argv);

  if (args.help) {
    output.write(`${usage()}\n`);
    return;
  }

  if (!args.pr) {
    throw new Error(`${usage()}\n\nMissing required --pr argument.`);
  }

  const pr = parsePullRequestUrl(args.pr);
  const diff = args.diffFile
    ? await fs.readFile(args.diffFile, "utf8")
    : (await fetchPullRequestDiff(args.pr)).diff;

  output.write(`${renderMarkdownReview(analyzeDiff(diff, pr))}\n`);
}

module.exports = {
  analyzeDiff,
  fetchPullRequestDiff,
  parseArgs,
  parsePullRequestUrl,
  renderMarkdownReview,
  runCli
};
