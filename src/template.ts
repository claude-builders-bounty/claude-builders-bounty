import { DiffResult, ReviewResult } from "./types";

function categorizeFile(filePath: string): string {
  const ext = filePath.split(".").pop()?.toLowerCase() ?? "";
  const extMap: Record<string, string> = {
    ts: "TypeScript",
    tsx: "TypeScript (React)",
    js: "JavaScript",
    jsx: "JavaScript (React)",
    py: "Python",
    go: "Go",
    rs: "Rust",
    java: "Java",
    rb: "Ruby",
    md: "Markdown",
    yml: "YAML",
    yaml: "YAML",
    json: "JSON",
    css: "CSS",
    scss: "SCSS",
    html: "HTML",
  };
  return extMap[ext] ?? (ext || "unknown");
}

function countLines(diff: string): { added: number; removed: number } {
  const lines = diff.split("\n");
  let added = 0;
  let removed = 0;
  for (const line of lines) {
    if (line.startsWith("+") && !line.startsWith("+++")) added++;
    if (line.startsWith("-") && !line.startsWith("---")) removed++;
  }
  return { added, removed };
}

function identifyRisks(diff: DiffResult, lines: { added: number; removed: number }): string[] {
  const risks: string[] = [];
  const { added, removed } = lines;
  const total = added + removed;

  // Size-based risks
  if (total > 1000) {
    risks.push("Large diff (>1000 lines) — harder to review thoroughly");
  }
  if (diff.prInfo.changedFiles > 10) {
    risks.push(
      `Many files changed (${diff.prInfo.changedFiles}) — increased regression risk`
    );
  }

  // Pattern-based risks
  const diffLower = diff.diff.toLowerCase();

  if (diffLower.includes("password") || diffLower.includes("secret") || diffLower.includes("api_key")) {
    risks.push("Possible hardcoded credentials or secrets in diff");
  }
  if (diffLower.includes("eval(") || diffLower.includes("exec(")) {
    risks.push("Use of eval/exec detected — potential code injection risk");
  }
  if (diffLower.includes("dangerouslysetinnerhtml")) {
    risks.push("dangerouslySetInnerHTML usage — XSS risk");
  }
  if (diffLower.includes("sql`") || diffLower.includes("query(")) {
    risks.push("Raw SQL queries detected — check for SQL injection");
  }
  if (diffLower.includes("alloworigin") || diffLower.includes("access-control")) {
    risks.push("CORS configuration change — verify allowed origins");
  }

  // Delete-heavy changes
  if (removed > added * 2 && removed > 50) {
    risks.push("Significant code removal — verify no breaking changes");
  }

  if (risks.length === 0) {
    risks.push("No significant risks identified — change appears low-complexity");
  }

  return risks;
}

function generateSuggestions(
  diff: DiffResult,
  lines: { added: number; removed: number }
): string[] {
  const suggestions: string[] = [];

  if (diff.prInfo.changedFiles > 5) {
    suggestions.push(
      "Consider splitting into smaller, focused PRs for easier review"
    );
  }

  const diffLower = diff.diff.toLowerCase();
  if (diffLower.includes("console.log") || diffLower.includes("debugger")) {
    suggestions.push(
      "Remove debug statements (console.log, debugger) before merging"
    );
  }
  if (diffLower.includes("todo") || diffLower.includes("fixme")) {
    suggestions.push("Address TODO/FIXME comments or create tracking issues");
  }
  if (lines.added > 0) {
    suggestions.push("Verify that new code has corresponding tests");
  }
  if (diff.diff.includes(".env") || diff.diff.includes("process.env")) {
    suggestions.push("Ensure environment variables are documented");
  }
  if (diff.prInfo.changedFiles > 0) {
    suggestions.push(
      "Verify that affected files have been tested locally"
    );
  }

  if (suggestions.length === 0) {
    suggestions.push("No specific suggestions — changes look clean");
  }

  return suggestions;
}

export function analyzeWithTemplate(diff: DiffResult): ReviewResult {
  console.log("📝 Using template mode (no ANTHROPIC_API_KEY)...");

  const lines = countLines(diff.diff);
  const langTypes = new Set<string>();

  const fileHeaderRegex = /^diff --git a\/.+ b\/(.+)$/gm;
  let fileMatch: RegExpExecArray | null;
  while ((fileMatch = fileHeaderRegex.exec(diff.diff)) !== null) {
    langTypes.add(categorizeFile(fileMatch[1]));
  }

  const summary = [
    `This PR introduces changes across ${diff.prInfo.changedFiles} file(s)`,
    `with +${diff.prInfo.additions} additions and -${diff.prInfo.deletions} deletions`,
    `in ${[...langTypes].join(", ") || "various"} code.`,
    diff.diff.length === 0 ? "The diff appears empty — verify the PR is populated." : "",
  ]
    .filter(Boolean)
    .join(" ");

  const risks = identifyRisks(diff, lines);
  const suggestions = generateSuggestions(diff, lines);
  const confidence = diff.diff.length === 0 ? "Low" : diff.prInfo.changedFiles > 10 ? "Low" : "Medium";

  return { summary, risks, suggestions, confidence };
}
