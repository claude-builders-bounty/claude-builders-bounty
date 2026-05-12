"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.callClaude = callClaude;
const sdk_1 = __importDefault(require("@anthropic-ai/sdk"));
async function callClaude(prompt, config) {
    const client = new sdk_1.default({
        apiKey: config.apiKey || process.env.ANTHROPIC_API_KEY,
    });
    if (!client.apiKey) {
        throw new Error('ANTHROPIC_API_KEY environment variable is required');
    }
    const response = await client.messages.create({
        model: config.model || 'claude-sonnet-4-20250514',
        max_tokens: config.maxTokens || 4096,
        messages: [
            {
                role: 'user',
                content: prompt,
            },
        ],
    });
    const text = response.content
        .filter((block) => block.type === 'text')
        .map((block) => ('text' in block ? block.text : ''))
        .join('\n');
    return text;
}
