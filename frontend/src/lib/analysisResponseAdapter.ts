import type {
  AnalysisFinding, AnalysisReport, BackendAmbiguity, BackendEvidence, BackendGap,
  BackendImportance, BackendReportData, RawAnalysisReportV2
} from './types';


export function isBackendAnalysisReport(data: unknown): data is RawAnalysisReportV2 {
  if (!data || typeof data !== 'object') return false;
  const record = data as Record<string, unknown>;
  return (
    typeof record.document === 'object' && record.document !== null &&
    typeof record.extraction === 'object' && record.extraction !== null &&
    typeof record.summary === 'object' && record.summary !== null &&
    typeof record.assessment === 'object' && record.assessment !== null &&
    Array.isArray(record.highlights)
  );
}

const IMPORTANCE_TO_SEVERITY: Record<BackendImportance, AnalysisFinding['severity']> = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low'
};

function toSeverity(importance: BackendImportance | undefined): AnalysisFinding['severity'] {
  return (importance && IMPORTANCE_TO_SEVERITY[importance]) || 'low';
}

function titleCaseCategory(category: string): string {
  return category
    .split('_')
    .filter(Boolean)
    .map(word => word[0].toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

function resolveEvidence(evidenceIds: string[] | undefined, byId: Map<string, BackendEvidence>): BackendEvidence | undefined {
  for (const id of evidenceIds || []) {
    const found = byId.get(id);
    if (found) return found;
  }
  return undefined;
}

function highlightToFinding(highlight: RawAnalysisReportV2['highlights'][number], byId: Map<string, BackendEvidence>): AnalysisFinding {
  const evidence = highlight.evidence_id ? byId.get(highlight.evidence_id) : undefined;
  return {
    category: 'highlight',
    severity: toSeverity(highlight.importance),
    title: highlight.title,
    clause: evidence?.exact_quote || '',
    explanation: highlight.summary,
    why_it_matters: highlight.why_it_matters,
    recommendation: '',
    confidence: 0,
    evidence_quality: highlight.confidence ? highlight.confidence.toLowerCase() : '',
    location: { section: evidence?.section ?? null, page: evidence?.page ?? null },
    kind: 'highlight',
    evidence_ids: highlight.evidence_id ? [highlight.evidence_id] : []
  };
}

function ambiguityToFinding(ambiguity: BackendAmbiguity, byId: Map<string, BackendEvidence>): AnalysisFinding {
  const evidence = resolveEvidence(ambiguity.evidence, byId);
  return {
    category: (ambiguity.category || 'ambiguity').toLowerCase(),
    severity: toSeverity(ambiguity.importance),
    title: titleCaseCategory(ambiguity.category || 'Ambiguous wording'),
    clause: evidence?.exact_quote || '',
    explanation: ambiguity.text,
    why_it_matters: ambiguity.explanation,
    recommendation: '',
    confidence: 0,
    evidence_quality: ambiguity.confidence ? ambiguity.confidence.toLowerCase() : '',
    location: { section: evidence?.section ?? null, page: evidence?.page ?? null },
    kind: 'ambiguity',
    evidence_ids: ambiguity.evidence || []
  };
}

function gapToFinding(gap: BackendGap, byId: Map<string, BackendEvidence>): AnalysisFinding {
  const evidence = resolveEvidence(gap.evidence, byId);
  return {
    category: (gap.category || 'gap').toLowerCase(),
    severity: toSeverity(gap.importance),
    title: titleCaseCategory(gap.category || 'Missing information'),
    clause: evidence?.exact_quote || '',
    explanation: gap.description,
    why_it_matters: '',
    recommendation: '',
    confidence: 0,
    evidence_quality: gap.confidence ? gap.confidence.toLowerCase() : '',
    location: { section: evidence?.section ?? null, page: evidence?.page ?? null },
    kind: 'gap',
    evidence_ids: gap.evidence || []
  };
}

const LEVEL_TO_RISK_CLASS: Record<RawAnalysisReportV2['assessment']['level'], string> = {
  NOTHING_SIGNIFICANT_IDENTIFIED: 'info',
  MOSTLY_SAFE: 'low',
  REVIEW_RECOMMENDED: 'medium'
};

const SEVERITY_RANK: Record<AnalysisFinding['severity'], number> = { high: 3, medium: 2, low: 1, info: 0 };


function findingDedupeKey(finding: AnalysisFinding): string {
  return (finding.title || '').trim().toLowerCase().replace(/\s+/g, ' ');
}

function mergeDuplicateFinding(existing: AnalysisFinding, incoming: AnalysisFinding): AnalysisFinding {
  const existingHasCategory = Boolean(existing.category) && existing.category !== 'highlight';
  const incomingHasCategory = Boolean(incoming.category) && incoming.category !== 'highlight';
  const base = incomingHasCategory && !existingHasCategory ? incoming : existing;
  const other = base === existing ? incoming : existing;
  return {
    ...base,
    explanation: base.explanation || other.explanation,
    why_it_matters: base.why_it_matters || other.why_it_matters,
    clause: base.clause || other.clause,
    recommendation: base.recommendation || other.recommendation,
    location: base.location?.section || base.location?.page ? base.location : other.location,
    severity: (SEVERITY_RANK[other.severity] ?? 0) > (SEVERITY_RANK[base.severity] ?? 0) ? other.severity : base.severity
  };
}

function dedupeFindings(findings: AnalysisFinding[]): AnalysisFinding[] {
  const byKey = new Map<string, AnalysisFinding>();
  const order: string[] = [];
  findings.forEach((finding, i) => {
    const key = findingDedupeKey(finding) || `__untitled-${i}`;
    const existing = byKey.get(key);
    if (existing) {
      byKey.set(key, mergeDuplicateFinding(existing, finding));
    } else {
      order.push(key);
      byKey.set(key, finding);
    }
  });
  return order.map(key => byKey.get(key)!);
}

export function adaptAnalysisResponse(raw: RawAnalysisReportV2): AnalysisReport {
  const evidenceById = new Map(raw.evidence.map(e => [e.evidence_id, e]));

  const findings: AnalysisFinding[] = dedupeFindings([
    ...raw.ambiguities.map(a => ambiguityToFinding(a, evidenceById)),
    ...raw.gaps.map(g => gapToFinding(g, evidenceById)),
    ...raw.highlights.map(h => highlightToFinding(h, evidenceById))
  ]);

  const backend: BackendReportData = {
    assessmentLevel: raw.assessment.level,
    summary: raw.summary,
    extractionStatus: raw.extraction.extraction_status,
    extractionInfo: raw.extraction,
    highlights: raw.highlights,
    evidence: raw.evidence,
    recommendations: raw.recommendations,
    riskAnalysis: raw.risk_analysis || null,
  };

  return {
    source: raw.extraction.source_name || raw.document.company || 'Analyzed document',
    document_type: (raw.document.primary_type || 'unknown').toLowerCase(),
    classification_confidence: raw.document.classification_confidence,
    sections: [],
    findings,
    top_things_to_know: raw.summary.key_points || [],
    overall_risk_score: 0,
    overall_risk_level: LEVEL_TO_RISK_CLASS[raw.assessment.level] || 'info',
    summary: raw.summary.text || raw.summary.document_type_description || '',
    analysis_version: 'v2',
    cached: false,
    backend
  };
}
