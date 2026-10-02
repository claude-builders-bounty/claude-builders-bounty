import { PRAnalysis } from './pr-analyzer';

export function generateMarkdownReview(analysis: PRAnalysis): string {
  const { summary, risks, suggestions, confidence } = analysis;
  
  return `
## 📋 PR Review Summary

${summary}

### ⚠️ Identified Risks
${risks.length > 0 ? risks.map(risk => `- ${risk}`).join('\n') : '- No significant risks identified'}

### 💡 Improvement Suggestions
${suggestions.length > 0 ? suggestions.map(suggestion => `- ${suggestion}`).join('\n') : '- No suggestions at this time'}

### 🎯 Confidence Score: ${confidence}

---
*Reviewed with Claude Code PR Review Agent*
`;
}