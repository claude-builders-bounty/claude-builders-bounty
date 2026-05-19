import Anthropic from '@anthropic-ai/sdk';
import { PRReview, DiffFile, PRInfo } from './types';

export class CodeAnalyzer {
  private anthropic: Anthropic;

  constructor(apiKey?: string) {
    const key = apiKey || process.env.ANTHROPIC_API_KEY;
    if (!key) {
      throw new Error('Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.');
    }
    this.anthropic = new Anthropic({ apiKey: key });
  }

  async analyzePR(prInfo: PRInfo, diffFiles: DiffFile[]): Promise<PRReview> {
    const diffSummary = diffFiles.map(f => 
      `File: ${f.filename} (${f.status}, +${f.additions}/-${f.deletions})\n${f.patch.substring(0, 3000)}`
    ).join('\n\n---\n\n');

    const prompt = `You are an expert code reviewer. Analyze this Pull Request and provide a structured review.

## PR Information
Title: ${prInfo.title}
Description: ${prInfo.description}

## Files Changed
Total files: ${diffFiles.length}
${diffFiles.map(f => `- ${f.filename}: ${f.status} (+${f.additions}/-${f.deletions})`).join('\n')}

## Diff Content
${diffSummary}

Provide your review in this exact JSON format:
{
  "summary": "2-3 sentence summary of the changes",
  "risks": ["risk 1", "risk 2", ...],
  "suggestions": ["suggestion 1", "suggestion 2", ...],
  "confidence": "Low|Medium|High"
}

Confidence levels:
- High: You fully understand the code and changes
- Medium: Some areas are unclear but overall understanding is good
- Low: Significant uncertainty about the changes or context

Respond ONLY with the JSON object, no markdown formatting.`;

    const response = await this.anthropic.messages.create({
      model: 'claude-3-sonnet-20240229',
      max_tokens: 2000,
      messages: [{ role: 'user', content: prompt }]
    });

    const content = response.content[0].type === 'text' 
      ? response.content[0].text 
      : '';

    try {
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      const jsonStr = jsonMatch ? jsonMatch[0] : content;
      const review = JSON.parse(jsonStr) as PRReview;
      
      // Validate required fields
      if (!review.summary || !Array.isArray(review.risks) || 
          !Array.isArray(review.suggestions) || !review.confidence) {
        throw new Error('Invalid review structure');
      }
      
      return review;
    } catch (e) {
      console.error('Failed to parse LLM response:', content);
      return {
        summary: 'Failed to generate review summary.',
        risks: ['Unable to analyze risks due to parsing error'],
        suggestions: ['Please review manually'],
        confidence: 'Low'
      };
    }
  }
}
