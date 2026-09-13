const RISK_PATTERNS = [
  {
    name: "authentication or authorization",
    test: /\b(auth|oauth|jwt|session|permission|role|admin|token)\b/i,
    risk: "Authentication or authorization paths changed; verify access control and negative cases."
  },
  {
    name: "database migration or schema",
    test: /\b(db|database|migration|alter table|create table|drop table|sql|sqlite|postgres|mysql)\b/i,
    risk: "Database shape changed; confirm migrations are reversible and compatible with existing data."
  },
  {
    name: "payments or billing",
    test: /\b(payment|billing|stripe|invoice|checkout|wallet|crypto|usdc)\b/i,
    risk: "Payment-related behavior changed; check idempotency, rounding, and failure handling."
  },
  {
    name: "network or API integration",
    test: /\b(fetch|axios|http|api|webhook|request|response|retry)\b/i,
    risk: "External API behavior changed; validate timeout, retry, and non-2xx handling."
  },
  {
    name: "secrets",
    test: /\b(secret|api[_-]?key|private[_-]?key|password|credential)\b/i,
    risk: "Secret-handling code changed; ensure secrets are not logged, committed, or exposed in errors."
  },
  {
    name: "deletion or destructive operations",
    test: /\b(delete|destroy|remove|truncate|drop)\b/i,
    risk: "Destructive behavior appears in the diff; confirm safeguards and authorization."
  },
  {
    name: "tests removed",
    test: /^-\s*(it|test|describe)\(/m,
    risk: "Tests appear to be removed; make sure coverage still protects the changed behavior."
  }
];

function parseFiles(diff) {
  const files = [];
  let current = null;

  for (const line of diff.split(/\r?\n/)) {
    if (line.startsWith("diff --git ")) {
      const match = line.match(/^diff --git a\/(.+?) b\/(.+)$/);
      current = {
        before: match?.[1] ?? "unknown",
        path: match?.[2] ?? "unknown",
        additions: 0,
        deletions: 0,
        hunks: 0,
        addedLines: [],
        removedLines: []
      };
      files.push(current);
      continue;
    }

    if (!current) continue;
    if (line.startsWith("@@")) current.hunks += 1;
    if (line.startsWith("+") && !line.startsWith("+++")) {
      current.additions += 1;
      current.addedLines.push(line.slice(1));
    }
    if (line.startsWith("-") && !line.startsWith("---")) {
      current.deletions += 1;
      current.removedLines.push(line.slice(1));
    }
  }

  return files;
}

function languageFromPath(path) {
  const extension = path.split(".").pop()?.toLowerCase();
  return {
    js: "JavaScript",
    jsx: "React",
    ts: "TypeScript",
    tsx: "React TypeScript",
    py: "Python",
    go: "Go",
    rs: "Rust",
    rb: "Ruby",
    php: "PHP",
    java: "Java",
    cs: "C#",
    yml: "YAML",
    yaml: "YAML",
    json: "JSON",
    md: "Markdown"
  }[extension] ?? extension?.toUpperCase() ?? "unknown";
}

function collectRisks(files) {
  const text = files
    .flatMap((file) => [...file.addedLines, ...file.removedLines])
    .join("\n");

  const risks = RISK_PATTERNS
    .filter((pattern) => pattern.test.test(text))
    .map((pattern) => pattern.risk);

  const largeFiles = files.filter((file) => file.additions + file.deletions > 300);
  if (largeFiles.length) {
    risks.push(`Large diff surface in ${largeFiles.map((file) => file.path).join(", ")}; review in smaller logical chunks if possible.`);
  }

  return [...new Set(risks)];
}

function collectSuggestions(files, risks) {
  const suggestions = [];
  const hasTests = files.some((file) => /(^|\/)(test|tests|spec|__tests__)\/|(\.test|\.spec)\./i.test(file.path));
  const hasDocs = files.some((file) => /\.(md|mdx|rst)$/i.test(file.path));
  const hasConfig = files.some((file) => /\.(ya?ml|json|toml|ini)$/i.test(file.path));

  if (!hasTests) {
    suggestions.push("Add or update focused tests that exercise the main changed behavior and at least one failure path.");
  }
  if (risks.length > 0) {
    suggestions.push("Document the manual verification performed for the highest-risk path before merging.");
  }
  if (hasConfig) {
    suggestions.push("Confirm configuration changes are covered in setup or deployment notes.");
  }
  if (!hasDocs && files.length > 3) {
    suggestions.push("Consider adding a short README or changelog note if this affects user-visible behavior.");
  }

  suggestions.push("Run the repository's standard formatter, linter, and test command before requesting final review.");
  return [...new Set(suggestions)];
}

function confidence(files, risks) {
  const changedLines = files.reduce((sum, file) => sum + file.additions + file.deletions, 0);
  if (changedLines > 500 || risks.length >= 4) return "Low";
  if (changedLines > 150 || risks.length >= 2) return "Medium";
  return "High";
}

export function reviewPullRequestDiff(diff, options = {}) {
  const files = parseFiles(diff);
  if (files.length === 0) {
    throw new Error("No files were found in the unified diff.");
  }

  const additions = files.reduce((sum, file) => sum + file.additions, 0);
  const deletions = files.reduce((sum, file) => sum + file.deletions, 0);
  const languages = [...new Set(files.map((file) => languageFromPath(file.path)))].slice(0, 6);
  const risks = collectRisks(files);
  const suggestions = collectSuggestions(files, risks);
  const topFiles = [...files]
    .sort((a, b) => b.additions + b.deletions - (a.additions + a.deletions))
    .slice(0, 5);

  const riskLines = risks.length
    ? risks.map((risk) => `- ${risk}`)
    : ["- No obvious high-risk patterns were detected from the diff alone."];

  return [
    "# Claude PR Review",
    "",
    `Source: ${options.source ?? "diff input"}`,
    "",
    "## Summary",
    "",
    `This pull request changes ${files.length} file${files.length === 1 ? "" : "s"} with ${additions} additions and ${deletions} deletions. The main touched areas are ${topFiles.map((file) => `\`${file.path}\``).join(", ")}, and the detected file types are ${languages.join(", ")}.`,
    "",
    "The diff-level review below is based on changed lines and file metadata, so it should be paired with project-specific tests and a maintainer pass for business logic.",
    "",
    "## Identified Risks",
    "",
    ...riskLines,
    "",
    "## Improvement Suggestions",
    "",
    ...suggestions.map((suggestion) => `- ${suggestion}`),
    "",
    "## Changed File Snapshot",
    "",
    "| File | + | - | Hunks |",
    "|---|---:|---:|---:|",
    ...topFiles.map((file) => `| \`${file.path}\` | ${file.additions} | ${file.deletions} | ${file.hunks} |`),
    "",
    `## Confidence Score: ${confidence(files, risks)}`
  ].join("\n");
}
