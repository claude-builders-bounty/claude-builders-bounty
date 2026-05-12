"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.parsePRUrl = parsePRUrl;
exports.getPRInfo = getPRInfo;
const octokit_1 = require("octokit");
function parsePRUrl(url) {
    // Handle various GitHub URL formats
    const patterns = [
        /github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)/,
        /github\.com\/([^/]+)\/([^/]+)\/pull\/(\d+)\//,
    ];
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) {
            return {
                owner: match[1],
                repo: match[2],
                number: parseInt(match[3], 10),
            };
        }
    }
    throw new Error(`Invalid PR URL: ${url}`);
}
async function getPRInfo(url, config) {
    const { owner, repo, number } = parsePRUrl(url);
    const octokit = new octokit_1.Octokit({
        auth: config.token,
    });
    // Fetch PR details and diff
    const [prResponse, filesResponse] = await Promise.all([
        octokit.rest.pulls.get({ owner, repo, pull_number: number }),
        octokit.rest.pulls.listFiles({ owner, repo, pull_number: number }),
    ]);
    const pr = prResponse.data;
    // Get diff as a string
    const diffResponse = await octokit.rest.pulls.get({
        owner,
        repo,
        pull_number: number,
        headers: { Accept: 'application/vnd.github.v3.diff' },
    });
    const diff = typeof diffResponse.data === 'string' ? diffResponse.data : '';
    const files = filesResponse.data.map((f) => f.filename);
    return {
        owner,
        repo,
        number,
        title: pr.title || '',
        body: pr.body || '',
        diff,
        files,
    };
}
