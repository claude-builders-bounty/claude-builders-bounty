export interface PRReview {
  summary: string;
  risks: string[];
  suggestions: string[];
  confidence: 'Low' | 'Medium' | 'High';
}

export interface PRInfo {
  owner: string;
  repo: string;
  pullNumber: number;
  title: string;
  description: string;
}

export interface DiffFile {
  filename: string;
  status: 'added' | 'removed' | 'modified' | 'renamed';
  additions: number;
  deletions: number;
  patch: string;
}
