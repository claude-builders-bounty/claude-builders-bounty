export interface PRInfo {
  owner: string;
  repo: string;
  number: number;
  title: string;
  description: string;
  author: string;
  baseBranch: string;
  headBranch: string;
  labels: string[];
}

export interface PRDiff {
  files: number;
  additions: number;
  deletions: number;
  rawDiff: string;
}

export interface Risk {
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  file?: string;
  line?: number;
}

export interface Suggestion {
  description: string;
  priority: 'low' | 'medium' | 'high';
  file?: string;
  codeSnippet?: string;
}

export interface ReviewResult {
  summary: string;
  risks: Risk[];
  suggestions: Suggestion[];
  securityNotes: string[];
  confidence: 'Low' | 'Medium' | 'High';
}

export interface ReviewConfig {
  depth: 'quick' | 'standard' | 'deep';
  format: 'console' | 'markdown' | 'json';
  postComment: boolean;
  verbose: boolean;
  outputFile?: string;
}
