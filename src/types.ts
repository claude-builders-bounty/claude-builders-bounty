export interface PRInfo {
  number: number;
  title: string;
  author: string;
  htmlUrl: string;
  baseRepo: string;
  baseBranch: string;
  headRepo: string;
  headBranch: string;
  additions: number;
  deletions: number;
  changedFiles: number;
}

export interface DiffResult {
  prInfo: PRInfo;
  diff: string;
  diffSizeKB: number;
}

export interface ReviewSection {
  heading: string;
  content: string;
}

export interface ReviewResult {
  summary: string;
  risks: string[];
  suggestions: string[];
  confidence: "Low" | "Medium" | "High";
  rawResponse?: string;
}

export interface ReviewOptions {
  prUrl: string;
  output?: string;
  post?: boolean;
  model?: string;
}
