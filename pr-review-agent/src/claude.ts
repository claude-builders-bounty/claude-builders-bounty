import Anthropic from '@anthropic-ai/sdk';

export interface ClaudeConfig {
  model?: string;
  maxTokens?: number;
  apiKey?: string;
}

export async function callClaude(prompt: string, config: ClaudeConfig): Promise<string> {
  const client = new Anthropic({
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
