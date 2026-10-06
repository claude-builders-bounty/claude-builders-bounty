export interface BountyClaim {
  id: string;
  repoOwner: string;
  repoName: string;
  issueNumber: number;
  claimant: string;
  claimedAt: number;
  transactionHash?: string;
  status: "pending" | "claimed" | "failed";
}

export interface GitHubIssue {
  number: number;
  title: string;
  body: string;
  user: {
    login: string;
  };
  state: "open" | "closed";
  pull_request?: object;
}

export interface GitHubComment {
  id: number;
  body: string;
  user: {
    login: string;
  };
  created_at: string;
}
