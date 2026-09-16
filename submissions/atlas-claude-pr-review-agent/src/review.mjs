const RISK_RULES = [
  {
    label: "authentication or secret handling",
    pattern: /auth|login|session|token|secret|password|credential/i,
  },
  {
    label: "payment or billing behavior",
    pattern: /payment|billing|invoice|checkout|stripe|paypal|pix/i,
  },
  {
    label: "database or schema behavior",
    pattern: /migration|schema|database|sql|prisma/i,
  },
  {
    label: "security-sensitive behavior",
    pattern: /security|vulnerab|permission|policy/i,
  },
  {
    label: "deployment or network behavior",
    pattern: /deploy|network|rpc|private[_-]?key|mainnet/i,
  },
];

const TEST_PATTERNS = [
  /test|spec|fixture|snapshot|mock/i,
  /__tests__|\.test\.|\.spec\./i,
];

export function buildReview(pr) {
  const risks = inferRisks(pr);
  const suggestions = inferSuggestions(pr, risks);
  const confidence = inferConfidence(pr, risks);
  const summary = summarize(pr);

  return [
    `# PR Review: ${pr.owner}/${pr.repo}#${pr.number}`,
    "",
    `Source: ${pr.url}`,
    "",
    "## Summary",
    "",
    summary,
    "",
    "## Identified Risks",
    "",
    ...asList(risks),
    "",
    "## Improvement Suggestions",
    "",
    ...asList(suggestions),
    "",
    "## Changed Files",
    "",
    ...asList(summarizeFiles(pr.files)),
    "",
    "## Confidence",
    "",
    confidence,
    "",
    "## Review Metadata",
    "",
    `- Changed files: ${pr.changedFiles}`,
    `- Additions: ${pr.additions}`,
    `- Deletions: ${pr.deletions}`,
    `- Base branch: ${pr.base}`,
    `- Head branch: ${pr.head}`,
  ].join("\n");
}

function summarize(pr) {
  const fileTypes = summarizeFileTypes(pr.files);
  const bodyHint = pr.body ? "The PR description is present." : "The PR description is empty or unavailable.";
  return [
    `This PR is titled "${pr.title}" and changes ${pr.changedFiles} file(s), with ${pr.additions} addition(s) and ${pr.deletions} deletion(s).`,
    `The touched areas appear to include ${fileTypes || "general source files"}.`,
    `${bodyHint} The review below is heuristic and should be verified by a maintainer before merge.`,
  ].join(" ");
}

function inferRisks(pr) {
  const risks = [];
  const reviewableText = [
    pr.body,
    ...pr.files.map((file) => `${file.filename}\n${file.patch}`),
  ].join("\n");

  for (const rule of RISK_RULES) {
    if (rule.pattern.test(reviewableText)) {
      risks.push(`Touches ${rule.label}; verify behavior, failure modes, and rollout before merge.`);
    }
  }

  const hasTests = pr.files.some((file) => TEST_PATTERNS.some((pattern) => pattern.test(file.filename)));
  if (!hasTests) {
    risks.push("No obvious test file was changed, so regression coverage may be missing.");
  }

  if (pr.changedFiles > 20 || pr.additions + pr.deletions > 800) {
    risks.push("The change is large enough that focused manual review is recommended.");
  }

  const deletedHeavy = pr.deletions > pr.additions * 2 && pr.deletions > 100;
  if (deletedHeavy) {
    risks.push("The PR removes substantially more code than it adds; confirm behavior was intentionally removed.");
  }

  return risks.length ? risks : ["No high-risk pattern was detected by the heuristic review."];
}

function inferSuggestions(pr, risks) {
  const suggestions = [];
  const hasTests = pr.files.some((file) => TEST_PATTERNS.some((pattern) => pattern.test(file.filename)));

  if (!hasTests) {
    suggestions.push("Add or reference tests that cover the changed behavior.");
  }

  if (!pr.body || pr.body.trim().length < 80) {
    suggestions.push("Expand the PR description with motivation, implementation notes, and validation steps.");
  }

  if (risks.some((risk) => /security|credential|secret|payment|billing|deployment|production/.test(risk))) {
    suggestions.push("Include explicit rollout, rollback, and secret-handling notes before merge.");
  }

  suggestions.push("Include the exact commands or checks used to validate the change.");
  return [...new Set(suggestions)];
}

function inferConfidence(pr, risks) {
  const riskText = risks.join(" ");
  if (/large enough|security|secret|payment|billing|deployment|network|database|schema|missing/.test(riskText)) {
    return "Medium";
  }
  if (pr.changedFiles <= 5 && pr.additions + pr.deletions <= 200) {
    return "High";
  }
  return "Medium";
}

function summarizeFiles(files) {
  if (!files.length) return ["No changed files were returned by the GitHub API."];
  return files.slice(0, 20).map((file) => {
    return `${file.filename} (${file.status}, +${file.additions}/-${file.deletions})`;
  });
}

function summarizeFileTypes(files) {
  const groups = new Set();
  for (const file of files) {
    if (/readme|docs?\//i.test(file.filename)) groups.add("documentation");
    if (/\.(js|jsx|ts|tsx|mjs|cjs)$/i.test(file.filename)) groups.add("JavaScript/TypeScript");
    if (/\.(py)$/i.test(file.filename)) groups.add("Python");
    if (/\.(yml|yaml|json|toml)$/i.test(file.filename)) groups.add("configuration");
    if (/\.(md|mdx)$/i.test(file.filename)) groups.add("Markdown");
    if (/test|spec|fixture/i.test(file.filename)) groups.add("tests");
  }
  return Array.from(groups).join(", ");
}

function asList(items) {
  return items.map((item) => `- ${item}`);
}
