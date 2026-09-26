export type Result = {
  url: string;
  privacy_score: number;
  security_score: number;
  risk_level: string;
  summary: string;
  trackers: { name: string; purpose: string; risk: string }[];
  cookies: Record<string, number>;
  security: { https: boolean; headers: Record<string, string>; recommendations: string[] };
  compliance: Record<string, { status: string; explanation: string }>;
  recommendations: string[];
};

export type AnalysisFinding = {
  category: string;
  severity: 'high' | 'medium' | 'low' | 'info';
  title: string;
  clause: string;
  explanation: string;
  why_it_matters: string;
  recommendation: string;
  evidence_ids?: string[];
  confidence: number;
  evidence_quality: string;
  status?: string;
  disclosure_status?: string;
  location: { section?: string | null; page?: number | null };
  kind?: 'highlight' | 'ambiguity' | 'gap';
};

export type AnalysisReport = {
  source: string;
  document_type: string;
  classification_confidence: number;
  sections: { title: string; text: string; page?: number | null }[];
  findings: AnalysisFinding[];
  top_things_to_know: string[];
  overall_risk_score: number;
  overall_risk_level: string;
  summary: string;
  analysis_version: string;
  cached: boolean;
  backend?: BackendReportData;
};


export type BackendImportance = 'LOW' | 'MEDIUM' | 'HIGH';
export type BackendConfidence = 'LOW' | 'MEDIUM' | 'HIGH';
export type BackendAssessmentLevel = 'MOSTLY_SAFE' | 'NOTHING_SIGNIFICANT_IDENTIFIED' | 'REVIEW_RECOMMENDED';
export type BackendExtractionStatus = 'COMPLETE' | 'PARTIAL' | 'FAILED' | 'NO_READABLE_CONTENT';
export type BackendDisclosureStatus = 'DISCLOSED' | 'PARTIALLY_DISCLOSED' | 'AMBIGUOUS' | 'NOT_FOUND' | 'CONFLICTING';
export type BackendFinancialClarity = 'EXPLICIT' | 'AMBIGUOUS' | 'NOT_CLEARLY_STATED' | 'CONFLICTING';
export type BackendEvidenceStrength = 'DIRECT' | 'STRONG' | 'MODERATE' | 'INFERRED';

export type BackendEvidence = {
  evidence_id: string;
  source_document: string;
  source_url?: string | null;
  page?: number | null;
  section?: string | null;
  exact_quote: string;
  normalized_quote: string;
  evidence_type: BackendEvidenceStrength;
  confidence: number;
};

export type BackendHighlight = {
  title: string;
  importance: BackendImportance;
  summary: string;
  why_it_matters: string;
  evidence_id?: string | null;
  confidence: BackendConfidence;
};

export type BackendGap = {
  gap_id?: string | null;
  category: string;
  description: string;
  importance: BackendImportance;
  evidence: string[];
  confidence: BackendConfidence;
};

export type BackendAmbiguity = {
  ambiguity_id?: string | null;
  text: string;
  category: string;
  explanation: string;
  importance: BackendImportance;
  evidence: string[];
  confidence: BackendConfidence;
};

export type BackendRecommendation = {
  recommendation_id?: string | null;
  title: string;
  description: string;
  importance: BackendImportance;
  category: string;
  evidence_ids: string[];
};

export type BackendAreaReport = {
  area_name: string;
  status?: BackendDisclosureStatus;
  clarity?: BackendFinancialClarity;
  user_impact?: string;
  what_document_says?: string;
  why_it_matters?: string;
  what_to_check?: string;
  plain_language_explanation?: string;
  potential_user_impact?: string;
  conditions_or_exceptions?: string[];
  evidence_ids: string[];
  confidence: BackendConfidence;
};

export type BackendExtractionInfo = {
  source_type: string;
  source_name: string;
  source_url?: string | null;
  mime_type?: string | null;
  detected_file_type: string;
  extraction_method: string;
  extraction_status: BackendExtractionStatus;
  partial: boolean;
  warnings: string[];
  pages_total?: number | null;
  pages_extracted?: number | null;
  pages_failed?: number | null;
};

export type BackendDocumentProfile = {
  primary_type: string;
  secondary_types: string[];
  classification_confidence: number;
  company?: string | null;
  product?: string | null;
  effective_date?: string | null;
  last_updated?: string | null;
  version?: string | null;
  jurisdiction?: string | null;
};

export type BackendSummary = {
  document_type_description: string;
  text?: string;
  key_points: string[];
  word_count: number;
};

export type BackendAssessment = {
  level: BackendAssessmentLevel;
  explanation: string;
  confidence: BackendConfidence;
};


export type BackendRiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'NOT_APPLICABLE';

export type BackendRiskArea = {
  area: string;
  level: BackendRiskLevel;
  title: string;
  summary: string;
  why_it_matters: string;
  evidence_ids: string[];
};

export type BackendRiskAnalysis = {
  overall_level: BackendRiskLevel;
  title: string;
  explanation: string;
  areas: BackendRiskArea[];
  scope: string;
  disclaimer: string;
};

export type RawAnalysisReportV2 = {
  id: string;
  status: string;
  created_at: string;
  document: BackendDocumentProfile;
  extraction: BackendExtractionInfo;
  summary: BackendSummary;
  assessment: BackendAssessment;
  highlights: BackendHighlight[];
  privacy?: Record<string, BackendAreaReport> | null;
  payments?: Record<string, BackendAreaReport> | null;
  contract?: Record<string, BackendAreaReport> | null;
  gaps: BackendGap[];
  ambiguities: BackendAmbiguity[];
  evidence: BackendEvidence[];
  recommendations: BackendRecommendation[];
  risk_analysis?: BackendRiskAnalysis | null;
};

export type BackendReportData = {
  summary: BackendSummary;
  assessmentLevel: BackendAssessmentLevel;
  extractionStatus: BackendExtractionStatus;
  extractionInfo: BackendExtractionInfo;
  highlights: BackendHighlight[];
  evidence: BackendEvidence[];
  recommendations: BackendRecommendation[];
  riskAnalysis?: BackendRiskAnalysis | null;
};

export type AnalysisNotice = {
  kind: 'info' | 'warning';
  code?: string;
  message: string;
};


export type AnalysisItem = {
  label: string;
  report?: AnalysisReport;
  error?: string;
  errorCode?: string;
  supportedFormats?: string[];
  warning?: string;
  notice?: AnalysisNotice;
};


export type AppSettings = { theme: 'dark' | 'light'; displayName: string };

export type TurnAttachment = { name: string; size: number; type: string };

export type ConversationTurn = {
  id: string;
  date: string;
  status?: 'pending' | 'complete';
  userText?: string;
  userUrl?: string;
  userFiles?: TurnAttachment[];
  items: AnalysisItem[];
};

export type Conversation = {
  id: string;
  title: string;
  titleSource?: 'automatic' | 'manual';
  createdAt: string;
  updatedAt: string;
  pinned?: boolean;
  turns: ConversationTurn[];
};

export type AppNotification = { id: string; title: string; time: string };

export type AnalysisInputType = 'text' | 'image' | 'pdf' | 'document' | 'spreadsheet' | 'presentation' | 'url' | 'files';

type AnalysisInputLike = {
  text?: string;
  url?: string;
  useUrl?: boolean;
  files?: { name: string; type?: string }[];
};

const SPREADSHEET_EXT = new Set(['xlsx', 'xls', 'csv', 'tsv']);
const PRESENTATION_EXT = new Set(['pptx', 'ppt']);
const IMAGE_EXT = new Set(['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tif', 'tiff', 'gif']);

function getFileInputType(file: { name: string; type?: string }): AnalysisInputType {
  const ext = file.name.split('.').pop()?.toLowerCase() || '';
  const mime = (file.type || '').toLowerCase();
  if (mime.startsWith('image/') || IMAGE_EXT.has(ext)) return 'image';
  if (mime === 'application/pdf' || ext === 'pdf') return 'pdf';
  if (SPREADSHEET_EXT.has(ext) || mime.includes('spreadsheet') || mime === 'text/csv') return 'spreadsheet';
  if (PRESENTATION_EXT.has(ext) || mime.includes('presentation')) return 'presentation';
  return 'document';
}

export function getAnalysisInputType(input: AnalysisInputLike): AnalysisInputType {
  const files = input.files || [];
  const hasText = Boolean(input.text && input.text.trim());
  const hasUrl = Boolean(input.useUrl && input.url && input.url.trim());
  if ((hasText ? 1 : 0) + (hasUrl ? 1 : 0) + files.length > 1) return 'files';
  if (hasUrl) return 'url';
  if (files.length === 1) return getFileInputType(files[0]);
  return 'text';
}
