import { describe, it, expect, vi } from 'vitest';
import { reviewPR } from '../src/analyzer.js';

// Mock Anthropic SDK
vi.mock('@anthropic-ai/sdk', () => {
  return {
    default: class MockAnthropic {
      messages = {
        create: vi.fn().mockResolvedValue({
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                summary: 'Mock summary',
                risks: [],
                suggestions: [],
                securityNotes: [],
                confidence: 'High'
              })
            }
          ]
        })
      };
    }
  };
});

describe('Analyzer', () => {
  it('should parse Claude response correctly', async () => {
    const prInfo = {
      owner: 'test', repo: 'repo', number: 1, title: 'Test PR',
      description: '', author: 'test', baseBranch: 'main', headBranch: 'feat', labels: []
    };
    const prDiff = { files: 1, additions: 10, deletions: 5, rawDiff: '+test' };
    const config = { depth: 'standard' as const, format: 'console' as const, postComment: false, verbose: false };

    const result = await reviewPR(prInfo, prDiff, config, 'dummy-key');
    expect(result.summary).toBe('Mock summary');
    expect(result.confidence).toBe('High');
  });
});
