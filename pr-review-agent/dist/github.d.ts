export interface PRInfo {
    owner: string;
    repo: string;
    number: number;
    title: string;
    body: string;
    diff: string;
    files: string[];
}
export interface GitHubConfig {
    token?: string;
}
export declare function parsePRUrl(url: string): {
    owner: string;
    repo: string;
    number: number;
};
export declare function getPRInfo(url: string, config: GitHubConfig): Promise<PRInfo>;
