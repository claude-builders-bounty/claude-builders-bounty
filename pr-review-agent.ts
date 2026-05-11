#!/usr/bin/env -S npx tsx
/**
 * Claude Code Sub-Agent: PR Review Bot
 *
 * Fetches a GitHub PR, analyzes the diff, and posts a structured review comment.
 * Integrates with Claude Code's agent loop as a sub-agent tool.
 *
 * Bounty: $150 — claude-builders-bounty/claude-builders-bounty#4
 *
 * Usage:
 *   npx tsx pr-review-agent.ts --repo owner/repo --pr 123
 */

import { execSync } from "child_process";

interface PRReviewResult {
  pr_number: number;
  repo: string;
  summary: string;
  files_changed: number;
  additions: number;
  deletions: number;
  categories: {
    security?: string[];
    performance?: string[];
    bugs?: string[];
    style?: string[];
    documentation?: string[];
    tests?: string[];
  };
  overall_verdict: "approve" | "request_changes" | "comment";
  confidence: number; // 0-1
}

interface GitHubFile {
  filename: string;
  status: string;
  additions: number;
  deletions: number;
  patch?: string;
}

class PRReviewAgent {
  private token: string;

  constructor(token?: string) {
    this.token = token || process.env.GITHUB_TOKEN || "";
    if (!this.token) {
      throw new Error("GITHUB_TOKEN required. Set it as an env var or pass to constructor.");
    }
  }

  private ghApi(endpoint: string): any {
    const url = endpoint.startsWith("http") ? endpoint : `https://api.github.com${endpoint}`;
    const cmd = `curl -s -H "Authorization: token ${this.token}" -H "Accept: application/vnd.github.v3+json" "${url}"`;
    return JSON.parse(execSync(cmd, { encoding: "utf-8", maxBuffer: 10 * 1024 * 1024 }));
  }

  async reviewPR(repo: string, prNumber: number): Promise<PRReviewResult> {
    // Fetch PR details
    const pr = this.ghApi(`/repos/${repo}/pulls/${prNumber}`);
    
    // Fetch files changed
    const files: GitHubFile[] = this.ghApi(`/repos/${repo}/pulls/${prNumber}/files`);
    
    // Calculate totals
    const totalAdditions = files.reduce((sum, f) => sum + f.additions, 0);
    const totalDeletions = files.reduce((sum, f) => sum + f.deletions, 0);
    
    // Analyze each file
    const categories: PRReviewResult["categories"] = {};
    
    for (const file of files) {
      const analysis = this.analyzeFile(file);
      for (const [cat, items] of Object.entries(analysis)) {
        if (!categories[cat as keyof typeof categories]) {
          categories[cat as keyof typeof categories] = [];
        }
        categories[cat as keyof typeof categories]!.push(...items);
      }
    }

    // Generate summary
    const summary = this.generateSummary(pr, files, categories);
    
    // Determine verdict
    const { verdict, confidence } = this.determineVerdict(categories, files);

    return {
      pr_number: prNumber,
      repo,
      summary,
      files_changed: files.length,
      additions: totalAdditions,
      deletions: totalDeletions,
      categories,
      overall_verdict: verdict,
      confidence,
    };
  }

  private analyzeFile(file: GitHubFile): Record<string, string[]> {
    const issues: Record<string, string[]> = {};
    const patch = file.patch || "";
    const filename = file.filename.toLowerCase();

    // Security checks
    if (patch.includes("eval(") || patch.includes("exec(") || patch.includes("os.system(")) {
      issues.security = issues.security || [];
      issues.security.push(`⚠️ \`${file.filename}\` contains dangerous functions (eval/exec/os.system)`);
    }
    if (patch.includes("pickle.load") || patch.includes("pickle.loads")) {
      issues.security = issues.security || [];
      issues.security.push(`⚠️ \`${file.filename}\` uses pickle deserialization (potential RCE)`);
    }
    if (patch.includes("subprocess") && patch.includes("shell=True")) {
      issues.security = issues.security || [];
      issues.security.push(`⚠️ \`${file.filename}\` uses subprocess with shell=True`);
    }
    if (patch.includes("requests.get") && !patch.includes("verify_url") && !patch.includes("validate")) {
      issues.security = issues.security || [];
      issues.security.push(`⚠️ \`${file.filename}\` makes HTTP requests without URL validation`);
    }

    // Bug checks
    if (patch.includes("console.log") || patch.includes("print(")) {
      issues.bugs = issues.bugs || [];
      issues.bugs.push(`🐛 \`${file.filename}\` contains debug logging that should be removed`);
    }
    if (patch.includes("TODO") || patch.includes("FIXME")) {
      issues.bugs = issues.bugs || [];
      issues.bugs.push(`🐛 \`${file.filename}\` has TODO/FIXME comments`);
    }

    // Style checks
    if (file.additions > 500 && !filename.includes("test")) {
      issues.style = issues.style || [];
      issues.style.push(`📏 \`${file.filename}\` is large (+${file.additions} lines). Consider splitting.`);
    }

    // Documentation checks
    if (filename.endsWith(".ts") || filename.endsWith(".js") || filename.endsWith(".py")) {
      if (!patch.includes("/**") && file.additions > 20) {
        issues.documentation = issues.documentation || [];
        issues.documentation.push(`📝 \`${file.filename}\` missing JSDoc/docstrings for new functions`);
      }
    }

    // Test checks
    if ((filename.includes("test") || filename.includes("spec")) && file.additions > 0) {
      issues.tests = issues.tests || [];
      issues.tests.push(`✅ \`${file.filename}\` adds test coverage`);
    }

    // Performance checks
    if (patch.includes("for.*in.*range") || patch.includes("while True")) {
      issues.performance = issues.performance || [];
      issues.performance.push(`🐌 \`${file.filename}\` may contain inefficient loops`);
    }

    return issues;
  }

  private generateSummary(pr: any, files: GitHubFile[], categories: PRReviewResult["categories"]): string {
    const title = pr.title;
    const author = pr.user.login;
    const totalIssues = Object.values(categories).flat().length;
    
    let summary = `**PR #${pr.number}: ${title}** by @${author}\n\n`;
    summary += `📁 ${files.length} files changed | ➕ ${files.reduce((s, f) => s + f.additions, 0)} additions | ➖ ${files.reduce((s, f) => s + f.deletions, 0)} deletions\n\n`;
    
    if (totalIssues > 0) {
      summary += `**Found ${totalIssues} issue${totalIssues > 1 ? 's' : ''} across ${Object.keys(categories).length} categories.**\n\n`;
    } else {
      summary += `**No issues detected. Clean PR! ✅**\n\n`;
    }

    return summary;
  }

  private determineVerdict(
    categories: PRReviewResult["categories"],
    files: GitHubFile[]
  ): { verdict: PRReviewResult["overall_verdict"]; confidence: number } {
    const securityIssues = categories.security?.length || 0;
    const bugIssues = categories.bugs?.length || 0;
    const totalFiles = files.length;
    
    // High security issues = request changes
    if (securityIssues >= 2) {
      return { verdict: "request_changes", confidence: 0.9 };
    }
    
    // Moderate issues = comment
    if (securityIssues === 1 || bugIssues >= 2) {
      return { verdict: "comment", confidence: 0.75 };
    }
    
    // Clean or minor issues = approve
    if (totalFiles > 0 && securityIssues === 0 && bugIssues <= 1) {
      return { verdict: "approve", confidence: 0.85 };
    }
    
    return { verdict: "comment", confidence: 0.6 };
  }

  postReviewComment(repo: string, prNumber: number, review: PRReviewResult): void {
    const body = this.formatReviewComment(review);
    
    // Post comment via GitHub API
    const cmd = `curl -s -X POST -H "Authorization: token ${this.token}" -H "Accept: application/vnd.github.v3+json" -d '${JSON.stringify({ body })}' "https://api.github.com/repos/${repo}/issues/${prNumber}/comments"`;
    execSync(cmd, { encoding: "utf-8" });
    console.log(`✅ Review posted to ${repo}#${prNumber}`);
  }

  private formatReviewComment(review: PRReviewResult): string {
    let body = `## 🤖 Claude Code PR Review\n\n`;
    body += `${review.summary}\n`;
    body += `**Verdict: ${review.overall_verdict.toUpperCase()}** (confidence: ${Math.round(review.confidence * 100)}%)\n\n`;
    body += `---\n\n`;

    for (const [category, items] of Object.entries(review.categories)) {
      if (items && items.length > 0) {
        const emoji = {
          security: "🔒",
          performance: "🐌",
          bugs: "🐛",
          style: "📏",
          documentation: "📝",
          tests: "✅",
        }[category] || "•";
        
        body += `### ${emoji} ${category.charAt(0).toUpperCase() + category.slice(1)}\n\n`;
        for (const item of items) {
          body += `${item}\n`;
        }
        body += `\n`;
      }
    }

    body += `---\n\n`;
    body += `*This review was generated by the [Claude Code PR Review Agent](https://github.com/claude-builders-bounty/claude-builders-bounty). Human review still recommended.*`;

    return body;
  }
}

// CLI entry point
if (import.meta.main) {
  const args = process.argv.slice(2);
  const repoIndex = args.indexOf("--repo");
  const prIndex = args.indexOf("--pr");
  
  if (repoIndex === -1 || prIndex === -1) {
    console.error("Usage: npx tsx pr-review-agent.ts --repo owner/repo --pr 123");
    process.exit(1);
  }
  
  const repo = args[repoIndex + 1];
  const prNumber = parseInt(args[prIndex + 1], 10);
  
  const agent = new PRReviewAgent();
  const review = agent.reviewPR(repo, prNumber);
  
  console.log("\n=== PR Review Result ===\n");
  console.log(JSON.stringify(review, null, 2));
  
  // Post the review
  agent.postReviewComment(repo, prNumber, review);
}

export { PRReviewAgent };
export type { PRReviewResult, GitHubFile };
