export interface ClaudeConfig {
    model?: string;
    maxTokens?: number;
    apiKey?: string;
}
export declare function callClaude(prompt: string, config: ClaudeConfig): Promise<string>;
