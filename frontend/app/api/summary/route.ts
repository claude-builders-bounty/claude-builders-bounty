import { NextResponse } from "next/server";

const mockData = {
  status: "success",
  summary: {
    title: "Weekly Repository Summary",
    repository: "ApexFlow",
    period: "Last 7 days",
    overview: "This week saw 15 commits, 8 issues closed, and 5 PRs merged.",
    completed_tasks: [
      "Added fingerprint replay defense",
      "Fixed Windows miner path",
      "Updated WHITEPAPER.md"
    ],
    pending_tasks: [
      "Fix entropy profile",
      "Add integration tests",
      "Review PRs"
    ],
    metrics: {
      commits: 15,
      pull_requests: 5,
      issues_closed: 8
    },
    recommendations: [
      "Review pending PRs",
      "Check open issues",
      "Update documentation"
    ]
  }
};

export async function GET() {
  return NextResponse.json(mockData);
}