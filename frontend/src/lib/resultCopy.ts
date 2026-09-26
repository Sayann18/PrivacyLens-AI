import type { AnalysisFinding, AnalysisReport } from './types';

export const RESULT_COPY = {
  followUpHeading: 'Suggested follow-up',
  noFollowUp: 'No specific follow-up is suggested based on the checks applied.',
  aboutHeading: 'About this analysis',
  aboutText:
    'PrivacyLens AI summarizes and highlights information found in the supplied document. It does not determine whether a term is legal, illegal, enforceable, or appropriate for your individual situation. Always review the original document and linked policies for complete context.'
} as const;


export const RISK_ANALYSIS_COPY = {
  heading: 'Risks for the purchaser',
  notApplicable: 'This document is not a customer-facing purchase, account, permission, tracking, content-rights, or contractual document.',
  noAreas: 'No significant customer-facing risk was identified.'
} as const;

export const THINGS_TO_KNOW = {
  heading: 'Things to Know',
  action: 'View source'
} as const;

const SEVERITY_RANK: Record<string, number> = { high: 3, medium: 2, low: 1, info: 0 };

export function getPriorityFindings(findings: AnalysisFinding[], limit = 5): { finding: AnalysisFinding; index: number }[] {
  return findings
    .map((finding, index) => ({ finding, index }))
    .filter(entry => Boolean(entry.finding))
    .sort((a, b) =>
      (SEVERITY_RANK[b.finding.severity] ?? 0) - (SEVERITY_RANK[a.finding.severity] ?? 0) ||
      (b.finding.confidence || 0) - (a.finding.confidence || 0) ||
      a.index - b.index)
    .slice(0, limit);
}

