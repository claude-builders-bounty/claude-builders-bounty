export interface ReviewConfig {
    githubToken?: string;
    model?: string;
    maxTokens?: number;
}
export declare function reviewPR(prUrl: string, config: ReviewConfig): Promise<string>;
